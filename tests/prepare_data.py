import utils.util as utils
import time
import sys

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from argparse import ArgumentParser
from argparse import BooleanOptionalAction

timestamps = False


class EventHandler(FileSystemEventHandler):
    """Custom event handler for the watchdog observer.

    Monitors specific filesystem changes such as file modification, creation,
    deletion, and movement. The event handler is called when a change occurs
    and the corresponding method is called.

    Attributes:
        dir_path: The directory path that should be watched.
        file_path: Path to the file that should contain the input data.
    """

    def __init__(
        self, dir_path: str, file_path: str, output_path: str, *args, **kwargs
    ):
        """Initializes the EventHandler with a specific file path.

        Args:
            dir_path: The directory path that should be watched.
            file_path: Path to the file that should be loaded and parsed.
            output_path: Path to where the output should be saved.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.
        """
        super().__init__(*args, **kwargs)
        self.dir_path = dir_path
        self.file_path = file_path
        self.output_path = output_path
        self.timeout = time.time() + 5
        self.timestamp = 0
        self.time_started = 0
        self.min_rtt = 0
        self.max_rtt = 0
        self.min_cwnd = 0
        self.max_cwnd = 0
        self.min_ssthresh = 0
        self.max_ssthresh = 0
        self.prev_data_segs_out = 0
        self.prev_cwnd = 0

    def on_modified(self, event):
        """Handles the file or directory modification event.

        Args:
            event (FileSystemEvent): Event representing filesystem change.
        """
        self.timeout = time.time() + 5

        if event.is_directory:
            return

        print("\n\nModified event")

        relative_path = utils.get_relative_path(event.src_path)
        if relative_path != self.file_path:
            print("Not the relevant output file.")
            return

        self.debug_prints()
        input_data_created = self.prepare_input_data()
        print("input data created:", input_data_created)
        self.debug_prints()

    def on_created(self, event):
        """Handles the file or directory creation event.

        Args:
            event (FileSystemEvent): Event representing filesystem change.
        """
        self.timeout = time.time() + 5

        if event.is_directory:
            return

        print("\n\nCreated event")

        relative_path = utils.get_relative_path(event.src_path)
        print(f"Relative path: {relative_path}")
        if relative_path != self.file_path:
            print("Not the relevant output file.")
            return

        input_data_created = self.prepare_input_data()
        print("input data created:", input_data_created)

    def on_moved(self, event):
        """Handles the file or directory movement event.

        Args:
            event (FileSystemEvent): Event representing filesystem change.
        """
        # Not relevant.

    def on_deleted(self, event):
        """Handles the file or directory deletion event.

        Args:
            event (FileSystemEvent): Event representing filesystem change.
        """
        # Not relevant.

    def parse_packet(self, packet: str) -> dict | None:
        """Parse the given packet.

        Args:
            packet: The packet that should be parsed.

        Returns:
            A dictionary containing the parsed packet with the relevant
            ss fields as keys and their formatted values as values.
        """
        if self.time_started == 0:
            self.time_started = time.time()

        # Only parse rtt and rtt var from the initial slow start phase.
        if time.time() - self.time_started < 1:  # TODO: Keep this in mind
            rtt_and_rtt_var, rtt_and_rtt_var_added = utils.add_rtt_and_rtt_variance(
                {}, packet
            )
            if rtt_and_rtt_var_added:
                rtt = rtt_and_rtt_var[0]
                self.min_rtt, self.max_rtt = utils.add_min_and_max_rtt(
                    {}, rtt, self.min_rtt, self.max_rtt
                )
            return None

        parsed_packet = {}

        _, timer_info_added = utils.add_timer_info(parsed_packet, packet)

        _, rto_added = utils.add_rto(parsed_packet, packet)

        rtt_and_rtt_var, rtt_and_rtt_var_added = utils.add_rtt_and_rtt_variance(
            parsed_packet, packet
        )

        cwnd, cwnd_added = utils.add_cwnd(parsed_packet, packet)

        ssthresh, ssthresh_added = utils.add_ssthresh(parsed_packet, packet)

        data_segs_out, data_segs_out_added = utils.add_data_segs_out(
            parsed_packet, packet
        )

        _, last_send_added = utils.add_lastsnd(parsed_packet, packet)

        _, pacing_rate_added = utils.add_pacing_rate(parsed_packet, packet)

        if timestamps:
            parsed_packet["timestamp"] = self.timestamp
        self.timestamp += 20

        if rtt_and_rtt_var_added:
            self.min_rtt, self.max_rtt = utils.add_min_and_max_rtt(
                parsed_packet, rtt_and_rtt_var[0], self.min_rtt, self.max_rtt
            )

        cwnd_diff_added = False
        if cwnd_added:
            _, cwnd_diff_added = utils.add_cwnd_diff_simple(
                parsed_packet, self.prev_cwnd
            )

        if cwnd_added:
            self.prev_cwnd = parsed_packet["cwnd"]
            self.min_cwnd, self.max_cwnd = utils.add_min_and_max_cwnd(
                parsed_packet, cwnd, self.min_cwnd, self.max_cwnd
            )

        if ssthresh_added:
            self.min_ssthresh, self.max_ssthresh = utils.add_min_and_max_ssthresh(
                parsed_packet, ssthresh, self.min_ssthresh, self.max_ssthresh
            )

        if data_segs_out_added:
            data_segs_out_diff = data_segs_out - self.prev_data_segs_out
            self.prev_data_segs_out = data_segs_out
            parsed_packet["data_segments_sent"] = data_segs_out_diff

        if utils.field_missing(
            timer_info_added,
            rto_added,
            rtt_and_rtt_var_added,
            cwnd_added,
            ssthresh_added,
            data_segs_out_added,
            last_send_added,
            pacing_rate_added,
            cwnd_diff_added,
        ):
            return None

        return parsed_packet

    def prepare_input_data(self) -> bool:
        """Load and parse ss output, and create csv for the classifier.

        Returns:
            True if the input data was successfully prepared, False otherwise.
        """
        packet = utils.read_ss_single_output(self.file_path)
        if packet == "":
            print("ss output file not valid.")
            return False

        packet_dict = self.parse_packet(packet)
        if packet_dict is None:
            print(
                "Error parsing packet. This could be due to missing ss fields"
                + " or because the threshold has not been reached yet."
            )
            return False

        utils.create_csv(packet_dict, self.output_path)

        return True

    def debug_prints(self) -> None:
        """Prints the current values of the instance variables."""
        print("\n\n---DEBUG PRINTS---")
        print(f"dir_path: {self.dir_path}")
        print(f"file_path: {self.file_path}")
        print(f"timestamp: {self.timestamp}")
        print(f"time_started: {self.time_started}")
        print(f"min_rtt: {self.min_rtt}")
        print(f"max_rtt: {self.max_rtt}")
        print(f"min_cwnd: {self.min_cwnd}")
        print(f"max_cwnd: {self.max_cwnd}")
        print(f"min_ssthresh: {self.min_ssthresh}")
        print(f"max_ssthresh: {self.max_ssthresh}")
        print(f"prev_data_segs_out: {self.prev_data_segs_out}")
        print(f"prev_cwnd: {self.prev_cwnd}")
        print("\n\n---END DEBUG PRINTS---")


def init_argparse() -> ArgumentParser:
    """Initialize the argument parser.

    Returns:
        The initialized argument parser.
    """
    parser = ArgumentParser(
        usage="python %(prog)s -d <directory_path> -i <input_file>",
        description="Watch for changes to a given directory and prepare input data for classifier",
    )

    parser.add_argument(
        "-d",
        "--directory_path",
        metavar="DIRECTORY_PATH",
        type=str,
        required="--time" not in sys.argv,
        help="Path to the directory that should be watched for changes",
    )
    parser.add_argument(
        "-i",
        "--input_file",
        metavar="INPUT_FILE",
        type=str,
        required="--time" not in sys.argv,
        help="Path to the text file that should be loaded and parsed",
    )
    parser.add_argument(
        "-o",
        "--output_path",
        metavar="OUTPUT_PATH",
        type=str,
        required="--time" not in sys.argv,
        help="Path to where the output should be saved",
    )
    parser.add_argument(
        "--timestamps",
        metavar="TIMESTAMPS",
        type=bool,
        action=BooleanOptionalAction,
        default=False,
        help="Add timestamps",
    )
    parser.add_argument(
        "--time",
        metavar="TIME",
        type=bool,
        action=BooleanOptionalAction,
        default=False,
        help="Time the execution of the module without running the observer",
    )

    return parser


def observe(dir_path: str, file_path: str, output_path: str) -> None:
    """Observe the directory with the given path for changes and prepare input data.

    Observes the directory with the given path for changes. If there is a change,
    an event handler is called that loads the file located at the given path
    and prepares the input data for the classifier.

    Args:
        dir_path: The directory path that should be watched.
        file_path: The path to the text file that should be loaded and parsed.
        output_path: Path to where the output should be saved.
    """
    observer = Observer()
    event_handler = EventHandler(dir_path, file_path, output_path)
    observer.schedule(event_handler, path=dir_path)
    observer.start()

    print("Data persistence module started. Waiting for changes...\n\n")

    try:
        while observer.is_alive() and time.time() < event_handler.timeout:
            observer.join(1)
    finally:
        observer.stop()
        observer.join()


def prepare_input_data_test(input_path: str) -> None:
    """Load and parse example ss output, and create example csv for the classifier.

    Args:
        input_path: The path to the text file containing the ss data.
    """
    packet = utils.read_ss_single_output(input_path)
    if packet == "":
        print("ss output file not valid.")
        return False

    vars = {
        "time_started": time.time() - 10,
        "min_rtt": 0,
        "max_rtt": 0,
        "min_cwnd": 0,
        "max_cwnd": 0,
        "min_ssthresh": 0,
        "max_ssthresh": 0,
        "prev_data_segs_out": 0,
        "prev_cwnd": 0,
    }

    packet_dict = utils.parse_packet_test(packet, vars)

    utils.create_csv(packet_dict, "output/test/input_data.csv")


def main():
    parser = init_argparse()
    args = parser.parse_args()

    global timestamps
    if args.timestamps:
        timestamps = True

    if args.time:
        utils.time_execution(
            lambda: prepare_input_data_test("output/test/ss_output.txt"),
            "prepare_input_data_test",
        )
    else:
        observe(args.directory_path, args.input_file, args.output_path)


if __name__ == "__main__":
    main()
