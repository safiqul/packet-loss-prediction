import utils.util as utils
import sys

from argparse import ArgumentParser
from argparse import BooleanOptionalAction


def init_argparse() -> ArgumentParser:
    """Initialize the argument parser.

    Returns:
            The argument parser.
    """
    parser = ArgumentParser(
        usage="%(prog)s [options]",
        description="Create a plot of the congestion window over time",
    )

    parser.add_argument(
        "-i",
        "--input_file",
        metavar="INPUT_FILE",
        type=str,
        required=True,
        help="Path to the input file that contains the ss outputs",
    )
    parser.add_argument(
        "-b",
        "--bandwidth",
        metavar="BANDWIDTH",
        type=int,
        required="--no_title_and_caption" not in sys.argv,
        help="The bandwidth the connection was configured with ",
    )
    parser.add_argument(
        "-d",
        "--delay",
        metavar="DELAY",
        type=int,
        required="--no_title_and_caption" not in sys.argv,
        help="The delay the connection was configured with",
    )
    parser.add_argument(
        "-q",
        "--queue_size",
        metavar="QUEUE_SIZE",
        type=int,
        required="--no_title_and_caption" not in sys.argv,
        help="The queue size the connection was configured with (in bytes)",
    )
    parser.add_argument(
        "--model_inference",
        metavar="MODEL_INFERENCE",
        action=BooleanOptionalAction,
        default=False,
        help="If model inference was enabled or not",
    )
    parser.add_argument(
        "-c",
        "--classification_threshold",
        metavar="CLASSIFICATION_THRESHOLD",
        type=float,
        required="--model_inference" in sys.argv
        and "--no_title_and_caption" not in sys.argv,
        help="The classification threshold that was used when predicting",
    )
    parser.add_argument(
        "-t",
        "--time",
        metavar="TIME",
        type=int,
        required=True,
        help="The time the connection was running for (in seconds)",
    )
    parser.add_argument(
        "-o",
        "--output",
        metavar="OUTPUT",
        type=str,
        help="Path to where the output should be saved",
    )
    parser.add_argument(
        "--show",
        metavar="SHOW",
        action=BooleanOptionalAction,
        default=False,
        help="Show the plot after it has been created",
    )
    parser.add_argument(
        "--include_timestamps",
        metavar="INCLUDE_TIMESTAMPS",
        action=BooleanOptionalAction,
        default=False,
        help="Include prediction timestamps.",
    )
    parser.add_argument(
        "-p",
        "--prediction_file",
        metavar="PREDICTION_FILE",
        type=str,
        required="--include_timestamps" in sys.argv,
        help="Path to the file that contains the predictions and their timestamps.",
    )
    parser.add_argument(
        "--no_title_and_caption",
        metavar="NO_TITLE_AND_CAPTION",
        action=BooleanOptionalAction,
        default=False,
        help="If the title and caption should be included in the plot or not.",
    )
    parser.add_argument(
        "--larger_fonts",
        metavar="LARGER_FONTS",
        action=BooleanOptionalAction,
        default=False,
        help="If the fonts should be larger or not.",
    )

    return parser


def create_and_save_cwnd_plot(args: object) -> None:
    """Create and save a plot of the congestion window over time.

    Args:
        args: The arguments passed to the script.
    """
    try:
        bandwidth = int(args.bandwidth)
    except ValueError as e:
        print("Invalid bandwidth value: {}".format(args.bandwidth))
        raise SystemExit(e)

    try:
        delay = int(args.delay)
    except ValueError as e:
        print("Invalid delay value: {}".format(args.delay))
        raise SystemExit(e)

    try:
        queue_size = int(args.queue_size)
    except ValueError as e:
        print("Invalid queue size value: {}".format(args.queue_size))
        raise SystemExit(e)

    threshold = None
    if args.model_inference:
        try:
            threshold = float(args.classification_threshold)
        except ValueError as e:
            print(
                "Invalid classification threshold value: {}".format(
                    args.classification_threshold
                )
            )
            raise SystemExit(e)
    predictions_and_timestamps = None
    if args.include_timestamps:
        try:
            predictions_and_timestamps = utils.get_predictions_and_timestamps(
                args.prediction_file
            )
        except FileNotFoundError as e:
            print("Prediction file not found: {}".format(args.prediction_file))
            raise SystemExit(e)

    ss_outputs = utils.read_ss(args.input_file)
    ss_interval = utils.calculate_ss_interval(args.time, len(ss_outputs))
    cc_algo = utils.get_cc_algo(ss_outputs)
    cwnd_values = utils.get_cwnd_values(ss_outputs)

    utils.create_and_save_cwnd_plot(
        cwnd_values,
        ss_interval,
        cc_algo,
        bandwidth,
        delay,
        queue_size,
        args.output if args.output else "output/plots",
        args.model_inference,
        threshold,
        predictions_and_timestamps,
        args.show,
        args.larger_fonts,
    )


def create_and_save_cwnd_plot_without_title_and_caption(args: object) -> None:
    """Create and save a plot of the congestion window over time with no title and caption.

    Args:
        args: The arguments passed to the script.
    """
    predictions_and_timestamps = None
    if args.include_timestamps:
        try:
            predictions_and_timestamps = utils.get_predictions_and_timestamps(
                args.prediction_file
            )
        except FileNotFoundError as e:
            print("Prediction file not found: {}".format(args.prediction_file))
            raise SystemExit(e)

    ss_outputs = utils.read_ss(args.input_file)
    ss_interval = utils.calculate_ss_interval(args.time, len(ss_outputs))
    cwnd_values = utils.get_cwnd_values(ss_outputs)

    utils.create_and_save_cwnd_plot_without_title_and_caption(
        cwnd_values,
        ss_interval,
        args.output if args.output else "output/plots",
        predictions_and_timestamps,
        args.show,
        args.larger_fonts,
    )


def main():
    parser = init_argparse()
    args = parser.parse_args()

    if args.no_title_and_caption:
        create_and_save_cwnd_plot_without_title_and_caption(args)
    else:
        create_and_save_cwnd_plot(args)


if __name__ == "__main__":
    main()
