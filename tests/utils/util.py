import re
import os
import csv
import time
import timeit
import matplotlib.pyplot as plt

from utils import types


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

            ss_dict["timer_name"] = 1 if timer_name == "on" else 0
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
    pacing_rate_regex = re.compile(r"pacing_rate (\d+(\.\d+)?)([Mk])bps")
    pacing_rate_match = re.search(pacing_rate_regex, measurement)
    if pacing_rate_match:
        rate, _, unit = pacing_rate_match.groups()
        rate = float(rate)
        if unit == "k":  # Convert kbps to Mbps if necessary
            rate /= 1000.0
        ss_dict["pacing_rate"] = rate
        return rate, True

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


def add_cwnd_diff_simple(ss_dict: dict, prev_cwnd: int) -> tuple:
    """Add the difference between the current congestion window and the previous congestion window value.

    Args:
        ss_dict: The dictionary to add the cwnd diff to.
        prev_cwnd: The previous congestion window value.

    Returns:
        A tuple containing the cwnd diff and True if the previous cwnd was not zero,
        0 and False otherwise.
    """
    if prev_cwnd == 0:
        return 0, False

    cwnd_diff = ss_dict["cwnd"] - prev_cwnd
    ss_dict["cwnd_diff"] = cwnd_diff

    return cwnd_diff, True


def get_relative_path(absolute_path: str) -> str:
    """Get the relative path given an absolute path.

    Args:
        absolute_path: The absolute path.

    Returns:
        The relative path.
    """
    base_path = os.getcwd()
    return os.path.relpath(absolute_path, base_path)


def read_ss_single_output(file_path: str) -> str:
    """Read the single ss output in the text file located at the given file_path.

    Args:
        file_path: The path to the ss output file that should be loaded and parsed.

    Returns:
        A string containing the output from the ss output file
        or an empty string if the output file was not valid.
    """
    try:
        with open(file_path) as data:
            lines = [line for line in data.readlines() if "Netid" not in line]

            if len(lines) < 2:
                return ""

            first_line = lines[0]
            if "tcp" not in first_line:
                return ""

            second_line = lines[1]
            if "tcp" in second_line:
                return ""

        return first_line.strip() + second_line.strip()
    except Exception as e:
        print(f"Error loading input data: {e}")
        return ""


def read_ss(file_path: str) -> list:
    """Read the ss outputs in the text file located at the given file_path.

    Args:
        file_path: The path to the ss output file that should be loaded and parsed.

    Returns:
        A list containing the ss outputs from the file.
    """

    ss_data = []
    try:
        with open(file_path) as data:
            lines = [line for line in data.readlines() if "Netid" not in line]

            # Append every first and second line to the packet string,
            # then append packet to the ss_data list.
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
    except FileNotFoundError as e:
        print(f"File not found: {e}")
        raise SystemExit()

    return ss_data


def calculate_ss_interval(total_time: int, ss_polls: int) -> float:
    """Calculate the interval between each measurement.

    Args:
        total_time: The total time the iperf test ran.
        ss_polls: The number of times ss was polled.

    Returns:
        The interval between each measurement in seconds.
    """
    return total_time / ss_polls


def get_cc_algo(ss_outputs: list) -> str:
    """Get the congestion control algorithm that was used.

    Args:
        ss_outputs: The ss outputs.

    Returns:
        The congestion control algorithm that was used.
    """
    cc_algo_regex = re.compile(r"ts sack ecn (reno|cubic|bbr)")

    for ss_output in ss_outputs:
        cc_algo_match = re.search(cc_algo_regex, ss_output)
        if cc_algo_match:
            return cc_algo_match.group(1)

    return ""


def get_cwnd_values(ss_outputs: list) -> list:
    """Get the cwnd values from the ss outputs.

    Args:
        ss_outputs: The ss outputs.

    Returns:
        A list containing the cwnd values.
    """
    return [
        int(re.search(r"cwnd:(\d+)", ss_output).group(1)) for ss_output in ss_outputs
    ]


def get_ssthresh_values(ss_outputs: list) -> list:
    """Get the ssthresh values from the ss outputs.

    Args:
        ss_outputs: The ss outputs.

    Returns:
        A list containing the ssthresh values.
    """
    return [
        int(re.search(r"ssthresh:(\d+)", ss_output).group(1))
        for ss_output in ss_outputs
    ]


def get_expire_time_values(ss_outputs: list) -> list:
    """Get the expire time values from the ss outputs.

    Args:
        ss_outputs: The ss outputs.

    Returns:
        A list containing the expire time values.
    """
    return [
        int(re.search(r",\s*(\d+)ms,", ss_output).group(1))
        for ss_output in ss_outputs
        if re.search(r",\s*(\d+)ms,", ss_output)
    ]


def get_retrans_values(ss_outputs: list) -> list:
    """Get the retrans values from the ss outputs.

    Args:
        ss_outputs: The ss outputs.

    Returns:
        A list containing the retrans values.
    """
    return [
        int(re.search(r",(\d+)\)", ss_output).group(1))
        for ss_output in ss_outputs
        if re.search(r",(\d+)\)", ss_output)
    ]


def get_rto_values(ss_outputs: list) -> list:
    """Get the rto values from the ss outputs.

    Args:
        ss_outputs: The ss outputs.

    Returns:
        A list containing the rto values.
    """
    return [
        int(re.search(r"rto:(\d+)", ss_output).group(1))
        for ss_output in ss_outputs
        if re.search(r"rto:(\d+)", ss_output)
    ]


def get_rtt_values(ss_outputs: list) -> list:
    """Get the rtt values from the ss outputs.

    Args:
        ss_outputs: The ss outputs.

    Returns:
        A list containing the rtt values.
    """
    return [
        float(re.search(r"rtt:(\d+\.\d+)/", ss_output).group(1))
        for ss_output in ss_outputs
        if re.search(r"rtt:(\d+\.\d+)/", ss_output)
    ]


def get_rtt_var_values(ss_outputs: list) -> list:
    """Get the rtt_var values from the ss outputs.

    Args:
        ss_outputs: The ss outputs.

    Returns:
        A list containing the rtt_var values.
    """
    return [
        float(re.search(r"rtt:\d+\.\d+/(\d+\.\d+)", ss_output).group(1))
        for ss_output in ss_outputs
        if re.search(r"rtt:\d+\.\d+/(\d+\.\d+)", ss_output)
    ]


def get_last_send_values(ss_outputs: list) -> list:
    """Get the lastsnd values from the ss outputs.

    Args:
        ss_outputs: The ss outputs.

    Returns:
        A list containing the lastsnd values.
    """
    return [
        int(re.search(r"lastsnd:(\d+)", ss_output).group(1))
        for ss_output in ss_outputs
        if re.search(r"lastsnd:(\d+)", ss_output)
    ]


def get_pacing_rate_values(ss_outputs: list) -> list:
    """Get the pacing_rate values from the ss outputs, converting kbps to Mbps.

    Args:
        ss_outputs: The ss outputs.

    Returns:
        A list containing the pacing_rate values in Mbps.
    """
    pacing_rates = []
    for ss_output in ss_outputs:
        search_result = re.search(r"pacing_rate (\d+(\.\d+)?)([Mk])bps", ss_output)
        if search_result:
            rate, _, unit = search_result.groups()
            rate = float(rate)
            if unit == "k":  # Convert kbps to Mbps if necessary
                rate /= 1000.0
            pacing_rates.append(rate)
    return pacing_rates


def create_and_save_cwnd_plot(
    cwnd_values: list,
    timestamp_interval: float,
    cc_algorithm: str,
    bandwidth: int,
    delay: int,
    queue_size: int,
    output_path: str,
    model_inference: bool = False,
    classification_threshold: float = None,
    predictions_and_timestamps: dict = None,
    show_plot: bool = False,
    larger_fonts: bool = False,
) -> None:
    """Create and save a plot of the congestion window over time."""

    if larger_fonts:
        plt.rcParams.update({"font.size": 14})
    else:
        plt.rcParams.update({"font.size": 10})

    timestamps = [i * timestamp_interval for i in range(len(cwnd_values))]

    _, ax = plt.subplots()
    ax.plot(timestamps, cwnd_values, label="cwnd")

    if predictions_and_timestamps:
        true_predictions = {
            ts: pred for ts, pred in predictions_and_timestamps.items() if pred == 1
        }
        x_values = [float(ts) for ts in true_predictions.keys()]
        y_values = [cwnd_values[int(float(ts) / timestamp_interval)] for ts in x_values]

        ax.scatter(
            x_values, y_values, label="Predictions", color="red", marker="x", s=75
        )
        ax.legend()

    ax.set_title(f"Congestion window ({cc_algorithm.capitalize()})")
    ax.set_xlabel("Timestamp (s)")
    ax.set_ylabel("Congestion window (MSS)")

    params = (
        f"{bandwidth}Mbps bandwidth, {delay}ms delay, {queue_size} bytes queue size"
    )
    if model_inference and classification_threshold is not None:
        params += f"\nModel inference enabled (Threshold: {classification_threshold})"

    ax.text(
        0.5,
        -0.2,
        params,
        transform=ax.transAxes,
        fontsize=12 if larger_fonts else 8,
        ha="center",
        va="top",
    )

    plt.tight_layout()
    plt.grid(True)

    try:
        plt.savefig(f"{output_path}/cwnd_plot.png", format="png", dpi=300)
        plt.savefig(f"{output_path}/cwnd_plot.pdf", format="pdf")
    except FileNotFoundError as e:
        print(f"Error saving plot: {e}")
        raise SystemExit()

    if show_plot:
        plt.show()


def create_and_save_cwnd_plot_without_title_and_caption(
    cwnd_values: list,
    timestamp_interval: float,
    output_path: str,
    predictions_and_timestamps: dict = None,
    show_plot: bool = False,
    larger_fonts: bool = False,
) -> None:
    """Create and save a plot of the congestion window over time.

    Args:
        cwnd_values: The cwnd values that should be plotted.
        timestamp_interval: The interval between each timestamp.
        output_path: The path to where the output should be saved.
        predictions_and_timestamps: The predictions and timestamps that should be plotted.
        show_plot: Whether or not to show the plot after it has been created.
        larger_fonts: Whether or not to use larger fonts in the plot.
    """
    if larger_fonts:
        plt.rcParams.update({"font.size": 14})
    else:
        plt.rcParams.update({"font.size": 10})

    timestamps = [i * timestamp_interval for i in range(len(cwnd_values))]

    _, ax = plt.subplots()
    ax.plot(timestamps, cwnd_values, label="cwnd")

    if predictions_and_timestamps:
        true_predictions = {
            ts: pred for ts, pred in predictions_and_timestamps.items() if pred == 1
        }
        x_values = [float(ts) for ts in true_predictions.keys()]
        y_values = [cwnd_values[int(float(ts) / timestamp_interval)] for ts in x_values]

        ax.scatter(
            x_values, y_values, label="Predictions", color="red", marker="x", s=75
        )
        ax.legend()

    ax.set_xlabel("Timestamp (s)")
    ax.set_ylabel("Congestion window (MSS)")

    plt.grid(True)

    try:
        plt.savefig(f"{output_path}/cwnd_plot.png", format="png", dpi=300)
        plt.savefig(f"{output_path}/cwnd_plot.pdf", format="pdf")
    except FileNotFoundError as e:
        print(f"Error saving plot: {e}")
        raise SystemExit()

    if show_plot:
        plt.show()


def calculate_queue_size(bandwidth: int, delay: int, bdp: float) -> int:
    """Calculate the queue size given the bandwidth, delay, and BDP multiplier.

    Args:
        bandwidth: The bandwidth.
        delay: The delay.
        bdp: The BDP multiplier.

    Returns:
        The calculated queue size in bytes.
    """
    bandwidth_in_bits = bandwidth * 1000000
    delay_in_seconds = delay / 1000
    bdp_in_bits = bandwidth_in_bits * delay_in_seconds * bdp
    bdp_in_bytes = bdp_in_bits / 8

    return bdp_in_bytes


def parse_packet_test(packet: str, vars: dict) -> dict | None:
    """Parse the given packet (test version).

    Args:
        packet: The packet that should be parsed.
        vars: Some vars that are needed for the parsing.

    Returns:
        A dictionary containing the parsed packet with the relevant
        ss fields as keys and their formatted values as values.
    """

    (
        time_started,
        min_rtt,
        max_rtt,
        min_cwnd,
        max_cwnd,
        min_ssthresh,
        max_ssthresh,
        prev_data_segs_out,
        prev_cwnd,
    ) = [
        vars[k]
        for k in [
            "time_started",
            "min_rtt",
            "max_rtt",
            "min_cwnd",
            "max_cwnd",
            "min_ssthresh",
            "max_ssthresh",
            "prev_data_segs_out",
            "prev_cwnd",
        ]
    ]
    # Only parse rtt and rtt var from the initial slow start phase.
    if time.time() - time_started < 10:
        rtt_and_rtt_var, rtt_and_rtt_var_added = add_rtt_and_rtt_variance({}, packet)
        if rtt_and_rtt_var_added:
            rtt = rtt_and_rtt_var[0]
            min_rtt, max_rtt = add_min_and_max_rtt({}, rtt, min_rtt, max_rtt)
        return None

    parsed_packet = {}

    add_timer_info(parsed_packet, packet)

    add_rto(parsed_packet, packet)

    rtt_and_rtt_var, rtt_and_rtt_var_added = add_rtt_and_rtt_variance(
        parsed_packet, packet
    )

    cwnd, cwnd_added = add_cwnd(parsed_packet, packet)

    ssthresh, ssthresh_added = add_ssthresh(parsed_packet, packet)

    data_segs_out, data_segs_out_added = add_data_segs_out(parsed_packet, packet)

    add_lastsnd(parsed_packet, packet)

    add_pacing_rate(parsed_packet, packet)

    if rtt_and_rtt_var_added:
        min_rtt, max_rtt = add_min_and_max_rtt(
            parsed_packet, rtt_and_rtt_var[0], min_rtt, max_rtt
        )

    if cwnd_added:
        add_cwnd_diff_simple(parsed_packet, prev_cwnd)

    if cwnd_added:
        prev_cwnd = parsed_packet["cwnd"]
        min_cwnd, max_cwnd = add_min_and_max_cwnd(
            parsed_packet, cwnd, min_cwnd, max_cwnd
        )

    if ssthresh_added:
        min_ssthresh, max_ssthresh = add_min_and_max_ssthresh(
            parsed_packet, ssthresh, min_ssthresh, max_ssthresh
        )

    if data_segs_out_added:
        data_segs_out_diff = data_segs_out - prev_data_segs_out
        prev_data_segs_out = data_segs_out
        parsed_packet["data_segments_sent"] = data_segs_out_diff

    return parsed_packet


def create_csv(packet: dict, output_path: str, print: bool = False) -> None:
    """Create a csv file from the given packet.

    Args:
        packet: The packet that has been parsed.
        output_path: The path to the output file.
        print: Whether or not to print the output path.
    """

    with open(output_path, "w") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=packet.keys())

        writer.writeheader()
        writer.writerow(packet)

    if print:
        print(f"Input data successfully prepared at {output_path}")


def time_execution(func: object, func_name: str, num_executions: int = 100000) -> None:
    """Time the execution of the given function and print the result in ms.

    Args:
        func: The function that should be timed.
        func_name: The name of the function that should be timed.
        num_executions: The number of times the function should be executed.
    """
    print(f"Timing execution of {func_name} with {num_executions} iterations...")
    execution_time = timeit.timeit(func, number=num_executions)
    avg_execution_time = execution_time / num_executions

    # Print the average execution time in ms.
    print(f"Average execution time: {avg_execution_time * 1000}ms")


def field_missing(
    timer_info_added: bool,
    rto_added: bool,
    rtt_and_rtt_var_added: bool,
    cwnd_added: bool,
    ssthresh_added: bool,
    data_segs_out_added: bool,
    last_send_added: bool,
    pacing_rate_added: bool,
    cwnd_diff_added: bool,
) -> bool:
    """Check if any of the fields are missing.

    Args:
        timer_info_added: Whether or not the timer info field was added.
        rto_added: Whether or not the rto field was added.
        rtt_and_rtt_var_added: Whether or not the rtt and rtt variance field was added.
        cwnd_added: Whether or not the cwnd field was added.
        ssthresh_added: Whether or not the ssthresh field was added.
        data_segs_out_added: Whether or not the data segments out field was added.
        last_send_added: Whether or not the last send field was added.
        pacing_rate_added: Whether or not the pacing rate field was added.
        cwnd_diff_added: Whether or not the cwnd diff field was added.
    Returns:
        True if any of the fields are missing, False otherwise.
    """
    return (
        not timer_info_added
        or not rto_added
        or not rtt_and_rtt_var_added
        or not cwnd_added
        or not ssthresh_added
        or not data_segs_out_added
        or not last_send_added
        or not pacing_rate_added
        or not cwnd_diff_added
    )


def write_to_file(file_path: str, data: str) -> None:
    """Write the given data to the file located at the given file path.

    Args:
        file_path: The path to the file.
        data: The data that should be written to the file.
    """
    with open(file_path, "w") as file:
        file.write(data)


def append_to_file(file_path: str, data: str) -> None:
    """Append the given data to the file located at the given file path.

    Args:
        file_path: The path to the file.
        data: The data that should be appended to the file.
    """
    with open(file_path, "a") as file:
        file.write(data)


def get_predictions_and_timestamps(file_path: str) -> dict:
    """Get the predictions and timestamps from the given file.

    Args:
        file_path: The path to the file.

    Returns:
        A dictionary containing the predictions and timestamps where the
        timestamps are the keys and the predictions are the values.
    """
    predictions_and_timestamps = {}
    with open(file_path) as file:
        for line in file.readlines():
            timestamp, prediction = line.split(": ")
            predictions_and_timestamps[timestamp] = int(prediction.strip())

    return predictions_and_timestamps


def path_valid(path: str) -> bool:
    """Check if the given path is valid.

    Args:
        path: The path to a directory.

    Returns:
        True if the path is valid, False otherwise.
    """
    return os.path.exists(path) and os.path.isdir(path)


def create_line_chart(
    x_values: list,
    y_values: list,
    x_label: str,
    y_label: str,
    title: str,
    fig_text: str,
    output_path: str,
) -> None:
    """Create a line chart from the given x and y values.

    Args:
        x_values: The x values.
        y_values: The y values.
        x_label: The label for the x axis.
        y_label: The label for the y axis.
        title: The title of the chart.
        fig_text: The text that should be added to the figure.
        output_path: The path to where the output should be saved.
    """

    plt.plot(x_values, y_values)
    plt.xlabel(x_label)
    plt.ylabel(y_label)
    plt.title(title)
    plt.figtext(
        0.5, 0.05, fig_text, wrap=True, horizontalalignment="center", fontsize=10
    )

    plt.subplots_adjust(bottom=0.2)
    plt.savefig(output_path, format="png", dpi=300)

    plt.show()


def read_metric_files(path: str) -> list:
    """Read the paths under the given path and return a list containing the contents of the various metric files.
    Args:
        path: The path to the directory that contains the directories with the metrics.
    Returns:
        A list containing the contents of the various metric files.
    """
    if not path_valid(path):
        print("Invalid path given, exiting...")
        raise SystemExit

    metric_files = []
    for dirpath, _, filenames in os.walk(path):
        if "metrics.txt" in filenames:
            metric_files.append(os.path.join(dirpath, "metrics.txt"))

    return [open(metric_file).read() for metric_file in metric_files]


def get_classification_threshold(file_content: str) -> float:
    """Get the classification threshold from the given file.

    Args:
        file_content: The content of the file.

    Returns:
        The classification threshold.
    """
    pattern = r"Classification Threshold: (\d+\.\d+)"

    match = re.search(pattern, file_content)

    if match:
        return float(match.group(1))
    else:
        raise ValueError("Classification Threshold not found in the file content.")


def get_bandwidth(file_content: str) -> float:
    """Get the bandwidth from the given file.

    Args:
        file_content: The content of the file.

    Returns:
        The bandwidth value as a float.
    """
    pattern = r"Bandwidth: (\d+) Mbit"
    match = re.search(pattern, file_content)
    if match:
        return float(match.group(1))
    else:
        raise ValueError("Bandwidth not found in the file content.")


def get_delay(file_content: str) -> float:
    """Get the delay from the given file.

    Args:
        file_content: The content of the file.

    Returns:
        The delay value as a float.
    """
    pattern = r"Delay: (\d+) ms"
    match = re.search(pattern, file_content)
    if match:
        return float(match.group(1))
    else:
        raise ValueError("Delay not found in the file content.")


def get_retransmissions(file_content: str) -> int:
    """Get the retransmissions from the given file.

    Args:
        file_content: The content of the file.

    Returns:
        The retransmissions value as an integer.
    """
    pattern = r"Retransmissions: (\d+)"
    match = re.search(pattern, file_content)
    if match:
        return int(match.group(1))
    else:
        raise ValueError("Retransmissions not found in the file content.")


def get_throughput(file_content: str) -> float:
    """Get the throughput from the given file.

    Args:
        file_content: The content of the file.

    Returns:
        The throughput value as a float.
    """
    pattern = r"Throughput: (\d+\.\d+)Mbps"
    match = re.search(pattern, file_content)
    if match:
        return float(match.group(1))
    else:
        raise ValueError("Throughput not found in the file content.")


def get_model_inference(file_content: str) -> int:
    """Get the model inference value from the given file.

    Args:
        file_content: The content of the file.

    Returns:
        The model inference value as an integer.
    """
    pattern = r"Model inference: (\d+)"
    match = re.search(pattern, file_content)
    if match:
        return int(match.group(1))
    else:
        raise ValueError("Model inference value not found in the file content.")


def create_box_plot(
    five_number_summaries: dict,
    x_label: str,
    y_label: str,
    title: str,
    fig_text: str,
    output_path: str,
    larger_fonts: bool = False,
) -> None:
    """Create a box plot based on the five-number summary.

    Args:
        five_number_summaries: A dictionary containing some given keys and the five-number summaries as values.
        x_label: The label for the x axis.
        y_label: The label for the y axis.
        title: The title of the chart.
        fig_text: The text that should be added to the figure.
        output_path: The path to where the output should be saved.
        larger_fonts: Whether or not to use larger fonts in the plot.
    """
    if larger_fonts:
        plt.rcParams.update({"font.size": 14})
    else:
        plt.rcParams.update({"font.size": 10})

    labels = list(five_number_summaries.keys())
    data = [
        [
            five_number_summary["smallest"],
            five_number_summary["q1"],
            five_number_summary["median"],
            five_number_summary["q3"],
            five_number_summary["largest"],
        ]
        for five_number_summary in five_number_summaries.values()
    ]

    plt.boxplot(data, labels=labels, vert=True, patch_artist=True, showfliers=False)
    plt.xlabel(x_label)
    plt.ylabel(y_label)

    if title is not None:
        plt.title(title)

    if fig_text is not None:
        plt.figtext(
            0.5,
            0.05,
            fig_text,
            wrap=True,
            horizontalalignment="center",
            fontsize=12 if larger_fonts else 8,
        )
        plt.subplots_adjust(bottom=0.3)

    plt.grid(True)

    plt.savefig(output_path, format="png", dpi=300)

    plt.show()


def calculate_percentage_reduction(data, baseline_data) -> dict:
    """Calculate percentage reduction for given five-number summary data compared to baseline data.

    Args:
        data: Data to compare to baseline data.
        baseline_data: Baseline data.

    Returns:
        A dictionary containing the percentage reduction for each metric.
    """
    reduction = {}
    for key in data:
        reduction[key] = {
            "smallest": (1 - data[key]["smallest"] / baseline_data["smallest"]) * 100,
            "median": (1 - data[key]["median"] / baseline_data["median"]) * 100,
            "q1": (1 - data[key]["q1"] / baseline_data["q1"]) * 100,
            "q3": (1 - data[key]["q3"] / baseline_data["q3"]) * 100,
            "largest": (1 - data[key]["largest"] / baseline_data["largest"]) * 100,
        }

    return reduction


def calculate_percentage_change(data, baseline_data):
    """Calculate percentage change for given five-number summary data compared to baseline data.

    Args:
        data: Data to compare to baseline data.
        baseline_data: Baseline data.

    Returns:
        A dictionary containing the percentage change for each metric.
    """
    change = {}
    for key in data:
        change[key] = {
            "smallest": (data[key]["smallest"] / baseline_data["smallest"] - 1) * 100,
            "median": (data[key]["median"] / baseline_data["median"] - 1) * 100,
            "q1": (data[key]["q1"] / baseline_data["q1"] - 1) * 100,
            "q3": (data[key]["q3"] / baseline_data["q3"] - 1) * 100,
            "largest": (data[key]["largest"] / baseline_data["largest"] - 1) * 100,
        }

    return change


def calculate_percentage_reduction_simple(data: dict, baseline_data: dict) -> dict:
    """Calculate percentage reduction for given five-number summary data compared to baseline data.

    Args:
        data: Data to compare to baseline data. Expected to be a five-number summary.
        baseline_data: Baseline data. Expected to be a five-number summary.

    Returns:
        A dictionary containing the percentage reduction for each metric.
    """
    return {
        "smallest": (1 - data["smallest"] / baseline_data["smallest"]) * 100,
        "median": (1 - data["median"] / baseline_data["median"]) * 100,
        "q1": (1 - data["q1"] / baseline_data["q1"]) * 100,
        "q3": (1 - data["q3"] / baseline_data["q3"]) * 100,
        "largest": (1 - data["largest"] / baseline_data["largest"]) * 100,
    }


def calculate_percentage_change_simple(data: dict, baseline_data: dict) -> dict:
    """Calculate percentage change for given five-number summary data compared to baseline data.

    Args:
        data: Data to compare to baseline data. Expected to be a five-number summary.
        baseline_data: Baseline data. Expected to be a five-number summary.

    Returns:
        A dictionary containing the percentage change for each metric.
    """
    return {
        "smallest": (data["smallest"] / baseline_data["smallest"] - 1) * 100,
        "median": (data["median"] / baseline_data["median"] - 1) * 100,
        "q1": (data["q1"] / baseline_data["q1"] - 1) * 100,
        "q3": (data["q3"] / baseline_data["q3"] - 1) * 100,
        "largest": (data["largest"] / baseline_data["largest"] - 1) * 100,
    }


def get_feature_values(ss_outputs: list, feature: types.Feature) -> list:
    """Get the feature values from the given ss outputs for the specified feature.

    Args:
        ss_outputs: The ss outputs.
        feature: The feature that should be extracted.

    Returns:
        A list containing the feature values.
    """

    match feature:
        case feature.CWND:
            return get_cwnd_values(ss_outputs)
        case feature.SSTHRESH:
            return get_ssthresh_values(ss_outputs)
        case feature.EXPIRE_TIME:
            return get_expire_time_values(ss_outputs)
        case feature.RETRANS:
            return get_retrans_values(ss_outputs)
        case feature.RTO:
            return get_rto_values(ss_outputs)
        case feature.RTT:
            return get_rtt_values(ss_outputs)
        case feature.RTT_VAR:
            return get_rtt_var_values(ss_outputs)
        case feature.LAST_SEND:
            return get_last_send_values(ss_outputs)
        case feature.PACING_RATE:
            return get_pacing_rate_values(ss_outputs)
        case _:
            raise ValueError("Invalid feature given.")


def create_and_save_line_chart(
    x_values: list,
    y_values: list,
    x_label: str,
    y_label: str,
    output_path: str,
    show: bool = False,
) -> None:
    """Create and save a line chart from the given x and y values.

    Args:
        x_values: The x values.
        y_values: The y values.
        x_label: The label for the x axis.
        y_label: The label for the y axis.
        output_path: The path to where the output should be saved.
    """
    plt.plot(x_values, y_values)
    plt.xlabel(x_label)
    plt.ylabel(y_label)

    plt.savefig(output_path, format="png", dpi=300)

    if show:
        plt.show()


def get_results(directory_path: str) -> dict:
    """Read the results for the various thresholds from the given directory.

    Args:
        directory_path: Path to the main directory that contains the directories for the specific thresholds.

    Returns:
        A dictionary with the thresholds as keys and lists containing dictionaries of results as values.
    """
    if not path_valid(directory_path):
        print("Invalid directory path given, exiting...")
        raise SystemExit

    number_regex = re.compile(r"(\d+\.\d+)")
    throughput_regex = re.compile(r"Average throughput: (\d+\.\d+)Mbps")
    retransmissions_regex = re.compile(r"Average retransmissions: (\d+)")

    thresholds_and_results = {}
    for threshold_dir in os.listdir(directory_path):
        threshold_path = os.path.join(directory_path, threshold_dir)
        if os.path.isdir(threshold_path):
            for dirpath, _, filenames in os.walk(threshold_path):
                if "results.txt" in filenames:
                    with open(os.path.join(dirpath, "results.txt")) as file:
                        content = file.read()

                        throughput_match = throughput_regex.search(content)
                        retransmissions_match = retransmissions_regex.search(content)

                        if throughput_match and retransmissions_match:
                            throughput = float(throughput_match.group(1))
                            retransmissions = int(retransmissions_match.group(1))

                            results_dict = {
                                "throughput": throughput,
                                "retransmissions": retransmissions,
                            }

                            if threshold_dir == "no_model_inference":
                                threshold_value = 1.0
                            else:
                                threshold_match = number_regex.search(threshold_dir)
                                if threshold_match:
                                    threshold_value = float(threshold_match.group(1))

                            if threshold_value not in thresholds_and_results:
                                thresholds_and_results[threshold_value] = []

                            thresholds_and_results[threshold_value].append(results_dict)

    return thresholds_and_results


def get_five_number_summary(thresholds_and_metrics: dict, metric: types.Metric) -> dict:
    """Get the smallest, median, largest, first quartile, and third quartile values for the given metric and threshold.

    Args:
        thresholds_and_metrics: Dictionary containing the metrics organized by threshold.
        metric: The metric that should be used.

    Returns:
        A dictionary containing the thresholds as keys and a dictionary containing the
        smallest, median, largest, first quartile, and third quartile values for the given metric as values.
    """
    thresholds_and_five_number_summary = {}
    for threshold, metrics in thresholds_and_metrics.items():
        (
            smallest,
            median,
            largest,
            first_quartile,
            third_quartile,
        ) = find_five_number_summary(metrics, metric)

        thresholds_and_five_number_summary[threshold] = {
            "smallest": smallest,
            "median": median,
            "largest": largest,
            "q1": first_quartile,
            "q3": third_quartile,
        }

    return thresholds_and_five_number_summary


def find_five_number_summary(metrics: list, metric: types.Metric) -> tuple:
    """Find the smallest, median, largest, first quartile, and third quartile values for the given metric.

    Args:
        metrics: List of metrics.
        metric: The metric that should be used.

    Returns:
        A tuple containing the smallest, median, largest, first quartile,
        and third quartile values for the given metric.
    """
    sorted_metrics = sorted(metrics, key=lambda k: k[metric.value])
    metrics_ct = len(sorted_metrics)

    def get_percentile_value(percentile: float) -> float:
        index = (metrics_ct - 1) * percentile
        floor_index = int(index)
        ceil_index = int(index) + 1

        # If the index is an integer, return the corresponding value
        if floor_index == index:
            return sorted_metrics[floor_index][metric.value]

        # Otherwise, return the average of two values surrounding the index
        d0 = sorted_metrics[floor_index][metric.value] * (ceil_index - index)
        d1 = sorted_metrics[ceil_index][metric.value] * (index - floor_index)
        return d0 + d1

    smallest = sorted_metrics[0][metric.value]
    median = get_percentile_value(0.5)
    largest = sorted_metrics[-1][metric.value]
    first_quartile = get_percentile_value(0.25)
    third_quartile = get_percentile_value(0.75)

    return (smallest, median, largest, first_quartile, third_quartile)
