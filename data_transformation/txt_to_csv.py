import csv
import re

from argparse import ArgumentParser
from pathlib import Path
from typing import List, Dict


def read_ss(paths: list) -> dict:
    """Read information from different ss output files and return a dictionary of ss data lists.

    Args:
        paths: A list of paths to the ss output files.

    Returns:
        A dictionary with the ss output file paths representing the keys and lists containing the information from the ss output files representing the values.
    """
    ss_data_lists = {}

    for path in paths:
        ss_data = []
        try:
            with open(path) as data:
                # Remove all lines containing "Netid".
                lines = [line for line in data.readlines() if "Netid" not in line]

                # Append every first and second line to the packet string, then add packet to the ss_data list.
                i = 0
                packet = ""
                for line in lines:
                    if i == 0:
                        if "tcp" not in line:
                            continue
                        packet = line.strip()
                        i += 1
                    elif i == 1:
                        packet += line.strip()
                        ss_data.append(packet)
                        packet = ""
                        i = 0
            ss_data_lists[path.name] = ss_data
        except FileNotFoundError as e:
            print(f"File not found: {e}")
            raise SystemExit()

    return ss_data_lists


def add_timer_info(ss_dict: dict, measurement: str) -> tuple:
    """Add the timer information from the given measurement to the given dictionary.

    Args:
        ss_dict: The dictionary to add the timer information to.
        measurement: The measurement from ss.

    Returns:
        A tuple with a list containing the timer name, expire time, and retrans and True
        if the measurement contained timer info or an empty list and False otherwise.
    """
    timer_regex = re.compile(r"timer:\((.+?)\)")
    expire_time_regex = re.compile(r"(\d+)")

    timer_info_match = re.search(timer_regex, measurement)
    if timer_info_match:
        timer_info = timer_info_match.group(1)
        timer_name, expire_time, retrans = timer_info.split(",")

        expire_time_match = re.search(expire_time_regex, expire_time)
        if expire_time_match:
            expire_time = expire_time_match.group(1)
            expire_time, retrans = int(expire_time), int(retrans)

            ss_dict["timer_name"] = timer_name
            ss_dict["expire_time"] = expire_time
            ss_dict["retrans"] = retrans
            return [timer_name, expire_time, retrans], True

    return [], False


def add_rto(ss_dict: dict, measurement: str) -> tuple:
    """Add the rto from the given measurement to the given dictionary.

    Args:
        ss_dict: The dictionary to add the rto to.
        measurement: The measurement from ss.

    Returns:
        A tuple containing the rto and True if the measurement contained rto information,
        0 and False otherwise.
    """
    rto_regex = re.compile(r"rto:(\d+)")
    rto_match = re.search(rto_regex, measurement)
    if rto_match:
        rto = rto_match.group(1)
        rto = int(rto)
        ss_dict["rto"] = rto
        return rto, True

    return 0, False


def add_rtt_and_rtt_variance(ss_dict: dict, measurement: str) -> tuple:
    """Add the rtt and rtt variance from the given measurement to the given dictionary.

    Args:
        ss_dict: The dictionary to add the rtt and rtt variance to.
        measurement: The measurement from ss.

    Returns:
        A tuple containnig a list with the rtt and rtt variance and True if the measurement contained rtt and rtt variance,
        an empty list and False otherwise.
    """
    rtt_and_rtt_var_regex = re.compile(r"rtt:(\d+\.?\d*)/(\d+\.?\d*)")
    rtt_and_rtt_var_match = re.search(rtt_and_rtt_var_regex, measurement)
    if rtt_and_rtt_var_match:
        rtt, rtt_var = rtt_and_rtt_var_match.group(1), rtt_and_rtt_var_match.group(2)
        rtt, rtt_var = float(rtt), float(rtt_var)
        ss_dict["rtt"] = rtt
        ss_dict["rtt_variance"] = rtt_var
        return [rtt, rtt_var], True

    return [], False


def add_cwnd(ss_dict: dict, measurement: str) -> tuple:
    """Add the cwnd from the given measurement to the given dictionary.

    Args:
        ss_dict: The dictionary to add the cwnd to.
        measurement: The measurement from ss.

    Returns:
        A tuple containing the cwnd and True if the measurement contained cwnd information,
        0 and False otherwise.
    """
    cwnd_regex = re.compile(r"cwnd:(\d+)")
    cwnd_match = re.search(cwnd_regex, measurement)
    if cwnd_match:
        cwnd = cwnd_match.group(1)
        cwnd = int(cwnd)
        ss_dict["cwnd"] = cwnd
        return cwnd, True

    return 0, False


def add_ssthresh(ss_dict: dict, measurement: str) -> tuple:
    """Add the ssthresh from the given measurement to the given dictionary.

    Args:
        ss_dict: The dictionary to add the ssthresh to.
        measurement: The measurement from ss.

    Returns:
        A tuple containing the ssthresh and True if the measurement contained ssthresh information,
        0 and False otherwise.
    """
    ssthresh_regex = re.compile(r"\bssthresh:(\d+)")
    ssthresh_match = re.search(ssthresh_regex, measurement)
    if ssthresh_match:
        ssthresh = ssthresh_match.group(1)
        ssthresh = int(ssthresh)
        ss_dict["ssthresh"] = ssthresh
        return ssthresh, True

    return 0, False


def add_data_segs_out(ss_dict: dict, measurement: str) -> tuple:
    """Add the data segments out from the given measurement to the given dictionary.

    Args:
        ss_dict: The dictionary to add the data segments out to.
        measurement: The measurement from ss.

    Returns:
        A tuple containing the data segments out and True if the measurement contained data segments out information,
        0 and False otherwise.
    """
    data_segs_out_regex = re.compile(r"data_segs_out:(\d+)")
    data_segs_out_match = re.search(data_segs_out_regex, measurement)
    if data_segs_out_match:
        data_segs_out = data_segs_out_match.group(1)
        data_segs_out = int(data_segs_out)
        ss_dict["data_segments_sent"] = data_segs_out
        return data_segs_out, True

    return 0, False


def add_lastsnd(ss_dict: dict, measurement: str) -> tuple:
    """Add the last send from the given measurement to the given dictionary.

    Args:
        ss_dict: The dictionary to add the last send to.
        measurement: The measurement from ss.

    Returns:
        A tuple containing the last send and True if the measurement contained last send information,
        0 and False otherwise.
    """
    lastsnd_regex = re.compile(r"lastsnd:(\d+)")
    last_send_match = re.search(lastsnd_regex, measurement)
    if last_send_match:
        last_send = last_send_match.group(1)
        last_send = int(last_send)
        ss_dict["last_send"] = last_send
        return last_send, True

    return 0, False


def add_pacing_rate(ss_dict: dict, measurement: str) -> tuple:
    """Add the pacing rate from the given measurement to the given dictionary.

    Args:
        ss_dict: The dictionary to add the pacing rate to.
        measurement: The measurement from ss.

    Returns:
        A tuple containing the pacing rate and True if the measurement contained pacing rate information,
        empty string and False otherwise.
    """
    pacing_rate_regex = re.compile(r"pacing_rate (\d+\.?\d*)Mbps")
    pacing_rate_match = re.search(pacing_rate_regex, measurement)
    if pacing_rate_match:
        pacing_rate = pacing_rate_match.group(1)
        pacing_rate = float(pacing_rate)
        ss_dict["pacing_rate"] = pacing_rate
        return pacing_rate, True

    return "", False


def add_min_and_max_cwnd(
    ss_dict: dict, cwnd: int, min_cwnd: int, max_cwnd: int
) -> tuple:
    """Add the minimum and maximum congestion window from the given measurements to the given dictionary.

    Args:
        ss_dict: The dictionary to add the minimum and maximum congestion window to.
        cwnd: The congestion window.
        min_cwnd: The minimum congestion window.
        max_cwnd: The maximum congestion window.

    Returns:
        The minimum and maximum congestion window.
    """
    min_cwnd = cwnd if min_cwnd == 0 or cwnd < min_cwnd else min_cwnd
    max_cwnd = cwnd if max_cwnd == 0 or cwnd > max_cwnd else max_cwnd

    ss_dict["min_cwnd"] = min_cwnd
    ss_dict["max_cwnd"] = max_cwnd

    return min_cwnd, max_cwnd


def add_min_and_max_ssthresh(
    ss_dict: dict, ssthresh: int, min_ssthresh: int, max_ssthresh: int
) -> tuple:
    """Add the minimum and maximum slow start threshold from the given measurements to the given dictionary.

    Args:
        ss_dict: The dictionary to add the minimum and maximum slow start threshold to.
        ssthresh: The slow start threshold.
        min_ssthresh: The minimum slow start threshold.
        max_ssthresh: The maximum slow start threshold.

    Returns:
        The minimum and maximum slow start threshold.
    """
    min_ssthresh = (
        ssthresh if min_ssthresh == 0 or ssthresh < min_ssthresh else min_ssthresh
    )
    max_ssthresh = (
        ssthresh if max_ssthresh == 0 or ssthresh > max_ssthresh else max_ssthresh
    )

    ss_dict["min_ssthresh"] = min_ssthresh
    ss_dict["max_ssthresh"] = max_ssthresh

    return min_ssthresh, max_ssthresh


def add_min_and_max_rtt(ss_dict: dict, rtt: int, min_rtt: int, max_rtt: int) -> tuple:
    """Add the minimum and maximum round trip time (rtt) from the given measurements to the given dictionary.

    Args:
        ss_dict: The dictionary to add the minimum and maximum round trip time (rtt) to.
        rtt: The round trip time (rtt).
        min_rtt: The minimum rtt.
        max_rtt: The maximum rtt.

    Returns:
        The minimum and maximum round trip time (rtt).
    """
    min_rtt = rtt if min_rtt == 0 or rtt < min_rtt else min_rtt
    max_rtt = rtt if max_rtt == 0 or rtt > max_rtt else max_rtt

    ss_dict["min_rtt"] = min_rtt
    ss_dict["max_rtt"] = max_rtt

    return min_rtt, max_rtt


def add_cwnd_diff(
    ss_dicts: list, ss_dict: dict, cwnd: int, prev_cwnd: int, current_index: int
) -> None:
    """Add the difference between the current congestion window and the previous congestion window value that was not the same.
       The previous value in this case refers to an earlier value in the same measurement that was not the same as the current.
       Meaning, that if the current congestion window is 10 and the one directly before it was also 10, the previous congestion
       window will the one before that, and so on.

    Args:
        ss_dicts: The list of dictionaries that contain the measurements from ss.
        ss_dict. The dictionary to add the cwnd diff to.
        cwnd: The current congestion window value.
        prev_cwnd: The previous congestion window value that was not the same.
        current_index: The index of the current measurement in in ss_dicts.
    """
    if current_index == 0:
        ss_dict["cwnd_diff"] = 0
        return

    if cwnd == prev_cwnd:
        prev_cwnd = ss_dicts[current_index - 1]["cwnd"]
        if prev_cwnd == cwnd:
            return add_cwnd_diff(ss_dicts, ss_dict, cwnd, prev_cwnd, current_index - 1)
        else:
            ss_dict["cwnd_diff"] = cwnd - prev_cwnd
            return


def label_packet(ss_dict: dict, cwnd: int, prev_cwnd: int, next_cwnd: int) -> bool:
    """Label the packet as either lost or not.

    The packet is labeled as lost or not by comparing its cwnd value with the values of the previous and next measurements.

    If the cwnd of the previous measurement is smaller or the same as the current one,
    and the cwnd of the next measurement is smaller than the one of the current measurement, the packet is labeled as lost.
    Otherwise, it is labeled as not lost.

    Args:
        ss_dict: The dictionary to add the label to.
        cwnd: The congestion window value of the current measurement.
        prev_cwnd: The congestion window value of the previous measurement.
        next_cwnd: The congestion window value of the next measurement.

    Returns:
        True if the packet was lost and False otherwise.
    """
    if prev_cwnd <= cwnd and next_cwnd < cwnd:
        ss_dict["lost"] = True
        return True

    ss_dict["lost"] = False
    return False


def label_packets(cwnd_dicts: list) -> None:
    """Label all of the packets in the given list of dictionaries.

    Args:
        cwnd_dicts: The list of dictionaries that contain the measurements
        from ss where the cwnd field was present but potentially not some other fields.
    """
    for i in range(1, len(cwnd_dicts) - 1):
        cwnd = cwnd_dicts[i]["cwnd"]
        prev_cwnd = cwnd_dicts[i - 1]["cwnd"]
        next_cwnd = cwnd_dicts[i + 1]["cwnd"]

        label_packet(cwnd_dicts[i], cwnd, prev_cwnd, next_cwnd)


def create_dictionary_list(ss_data: list) -> list:
    """Create a dictionary for each of the ss measurements in the given list.

    Args:
        ss_data: A list containing the measurements from ss.

    Returns:
        A list of dictionaries, where each dictionary consists of the different statistics for each of the measurements.
    """
    prev_data_segs_sent = 0
    min_rtt = (
        max_rtt
    ) = min_cwnd = max_cwnd = min_ssthresh = max_ssthresh = cumulative_rtt = 0
    timestamp = index = 0
    threshold = 30 * 1000  # 30 seconds in milliseconds.
    dicts = []
    cwnd_dicts = []
    for measurement in ss_data:
        if cumulative_rtt > threshold:
            ss_dict = {}
            field_missing = False

            # Add the timer info.
            timer_info_added = add_timer_info(ss_dict, measurement)[1]
            if not timer_info_added:
                field_missing = True

            # Add the rto.
            rto_added = add_rto(ss_dict, measurement)[1]
            if not rto_added:
                field_missing = True

            # Add the rtt and rtt variance.
            rtt_and_rtt_var, rtt_and_rtt_var_added = add_rtt_and_rtt_variance(
                ss_dict, measurement
            )
            if not rtt_and_rtt_var_added:
                field_missing = True
            else:
                rtt = rtt_and_rtt_var[0]
                cumulative_rtt += rtt

            # Add the cwnd.
            cwnd, cwnd_added = add_cwnd(ss_dict, measurement)
            if not cwnd_added:
                field_missing = True

            # Add the ssthresh.
            ssthresh, ssthresh_added = add_ssthresh(ss_dict, measurement)
            if not ssthresh_added:
                field_missing = True

            # Add the data segments out.
            data_segs_out, data_segs_out_added = add_data_segs_out(ss_dict, measurement)
            if not data_segs_out_added:
                field_missing = True

            # Add the lastsnd.
            last_send_added = add_lastsnd(ss_dict, measurement)[1]
            if not last_send_added:
                field_missing = True

            # Add the pacing rate.
            pacing_rate_added = add_pacing_rate(ss_dict, measurement)[1]
            if not pacing_rate_added:
                field_missing = True

            # Add the timestamp (ms when ss was ran).
            ss_dict["timestamp"] = timestamp
            timestamp += 20

            # Add the min and max rtt.
            if rtt_and_rtt_var_added:
                min_rtt, max_rtt = add_min_and_max_rtt(
                    ss_dict, rtt_and_rtt_var[0], min_rtt, max_rtt
                )

            # Add the cwnd diff and min and max cwnd.
            if cwnd_added:
                try:
                    add_cwnd_diff(cwnd_dicts, ss_dict, cwnd, cwnd, index)
                except RecursionError:
                    field_missing = True
                min_cwnd, max_cwnd = add_min_and_max_cwnd(
                    ss_dict, cwnd, min_cwnd, max_cwnd
                )

            # Add the min and max ssthresh.
            if ssthresh_added:
                min_ssthresh, max_ssthresh = add_min_and_max_ssthresh(
                    ss_dict, ssthresh, min_ssthresh, max_ssthresh
                )

            # Calculate the difference between the current and previous data segments sent.
            if data_segs_out_added:
                data_segments_sent_diff = data_segs_out - prev_data_segs_sent
                prev_data_segs_sent = data_segs_out
                ss_dict["data_segments_sent"] = data_segments_sent_diff

            if not field_missing:
                dicts.append(ss_dict)

            if cwnd_added:
                cwnd_dicts.append(ss_dict)
                index += 1
        else:
            rtt_and_rtt_var, rtt_and_rtt_var_added = add_rtt_and_rtt_variance(
                {}, measurement
            )

            if rtt_and_rtt_var_added:
                rtt = rtt_and_rtt_var[0]
                cumulative_rtt += rtt
                min_rtt, max_rtt = add_min_and_max_rtt({}, rtt, min_rtt, max_rtt)

    # Label all the packets as either lost or not.
    label_packets(dicts)

    # Remove the first and last packets since they cannot be reliably labeled.
    dicts = dicts[1:-1]

    return dicts


def create_dictionary_lists(ss_data: dict) -> list:
    """Create a dictionary for each of the ss measurements for each of the lists in the given list of ss data and add the various dictionary lists to a list.

    Args:
        ss_data: A dictionary containing lists with measurements from ss.

    Returns:

        A list of dictionary lists where each dictionary consists of the different statistics for each of the measurements.
    """
    return [create_dictionary_list(value) for value in ss_data.values()]


def create_csv(ss_dicts: List[List[Dict]], path: str) -> None:
    """Create a csv file from the ss measurements in the given list of lists of dictionaries.

    Args:
        ss_dicts: A list of lists, each containing dictionaries representing the measurements from ss.
        path: Where to create the csv file.
    """
    flattened_ss_dicts = [ss_dict for sublist in ss_dicts for ss_dict in sublist]

    with open(path, "w", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=flattened_ss_dicts[0].keys())

        writer.writeheader()
        for ss_dict in flattened_ss_dicts:
            writer.writerow(ss_dict)

    print("Created csv file under path:", path)


def init_argparse() -> ArgumentParser:
    """Initialize the argument parser.

    Returns:
        The initialized argument parser.
    """
    parser = ArgumentParser(
        description="Read data from different ss output files and create a final merged csv file",
        usage="python %(prog)s -a <congestion algorithm used> -o <output path> -s <paths to the folders that contain the ss output files>",
    )

    parser.add_argument(
        "-a",
        "--algorithm",
        metavar="ALGORITHM",
        type=str,
        default="reno",
        help="Congestion algorithm used: reno, cubic, bbr (default: reno)",
    )
    parser.add_argument(
        "-o",
        "--output",
        metavar="OUTPUT",
        type=str,
        default="",
        help="Output path (default: output/ss_data_[algorithm].csv)",
    )
    parser.add_argument(
        "-s",
        "--ss",
        metavar="FOLDER_PATHS",
        type=Path,
        required=True,
        help="Paths to folders that contain the ss output files separated by spaces, for example: folderpath1 folderpath2 ... folderpath3",
        nargs="+",
    )

    return parser


def paths_valid(paths: list) -> bool:
    """Check if the given paths are valid.

    Args:
        paths: A list containing the paths to check.

    Returns:
        True if all the paths are valid, False otherwise.
    """
    folders_valid = all(path.is_dir() for path in paths)
    if folders_valid:
        return all(child.is_file() for path in paths for child in path.iterdir())

    return False


def read_paths(paths: list) -> list:
    """Read the dictionary paths given as arguments and return a list containing the paths to the ss output files.

    Args:
        paths: A list containing the paths to the folders that contain the ss output files.

    Returns:
        A list containing the paths to the ss output files.
    """
    if paths_valid(paths):
        return [child.resolve() for path in paths for child in path.iterdir()]
    else:
        print("Invalid paths given, exiting...")
        raise SystemExit


def main():
    parser = init_argparse()
    args = parser.parse_args()

    print("Collecting paths containing ss output files...")
    ss_outputs = read_paths(args.ss)

    print("Reading ss output files...")
    ss_data_lists_dict = read_ss(ss_outputs)

    print("Creating dictionaries for each of the ss measurements...")
    ss_data_dicts = create_dictionary_lists(ss_data_lists_dict)

    print("Creating csv file...")
    if args.output != "":
        create_csv(ss_data_dicts, args.output)
    else:
        create_csv(ss_data_dicts, "output/ss_data_" + args.algorithm + ".csv")


if __name__ == "__main__":
    main()
