import enum
import os
import re
import sys
import utils.util as utils
import utils.types as types

from argparse import ArgumentParser
from argparse import BooleanOptionalAction


class CongestionControlAlgorithm(enum.Enum):
    """Enum for the different congestion control algorithms."""

    TCP_RENO = "reno"
    TCP_CUBIC = "cubic"


def init_argparse() -> ArgumentParser:
    """Initialize the argument parser.

    Returns:
        The initialized argument parser.
    """
    parser = ArgumentParser(
        usage="python %(prog)s [options]",
        description="Create two box plots showing the average retransmissions and throughput vs. the threshold values",
    )
    parser.add_argument(
        "-d",
        "--directory_path",
        metavar="DIRECTORY_PATH",
        type=str,
        required=True,
        help="Path to the main directory that contains the directories for the specific thresholds",
    )
    parser.add_argument(
        "-o",
        "--output_path",
        metavar="OUTPUT_PATH",
        type=str,
        required=True,
        help="Path to where the plots should be saved",
    )
    parser.add_argument(
        "-c",
        "--cong_alg",
        metavar="CONG_ALG",
        type=CongestionControlAlgorithm,
        required="--no_title_and_caption" not in sys.argv,
        help="The congestion control algorithm that was used",
    )
    parser.add_argument(
        "--no_title_and_caption",
        metavar="NO_TITLE_AND_CAPTION",
        action=BooleanOptionalAction,
        default=False,
        help="If the title and caption should be included in the plot or not",
    )
    parser.add_argument(
        "--larger_fonts",
        metavar="LARGER_FONTS",
        action=BooleanOptionalAction,
        default=False,
        help="If the fonts should be larger or not",
    )

    return parser


def map_cong_alg_to_title(
    cong_alg: CongestionControlAlgorithm, directory_path: str
) -> str:
    """Map the given congestion control algorithm to a title.

    Args:
        cong_alg: The congestion control algorithm that should be mapped.
        directory_path: Path to the main directory that contains the directories for the specific thresholds.

    Returns:
        The title for the given congestion control algorithm.
    """
    if cong_alg == CongestionControlAlgorithm.TCP_RENO:
        if "single_flow" in directory_path:
            return "TCP Reno (single flow)"
        elif "bg_traffic" in directory_path:
            return "TCP Reno (background traffic)"
    elif cong_alg == CongestionControlAlgorithm.TCP_CUBIC:
        if "single_flow" in directory_path:
            return "TCP Cubic (single flow)"
        elif "bg_traffic" in directory_path:
            return "TCP Cubic (background traffic)"
    else:
        print("Invalid congestion control algorithm given, exiting...")
        raise SystemExit


def create_caption(bandwidths: list, delays: list, queue_sizes: list) -> str:
    """Create a caption for the plot.

    Args:
        bandwidths: The bandwidths that were used.
        delays: The delays that were used.
        queue_sizes: The queue sizes that were used in bytes.

    Returns:
        The caption for the plot.
    """

    return f"Bandwidths (Mbps): {bandwidths}\nDelays (ms): {delays}\nQueue sizes (bytes): {queue_sizes}"


def extract_parameters(directory_path: str) -> tuple[list[int], list[int], list[float]]:
    """Extract values for delay, bandwidth, and queue size from the given directory path.

    Args:
        directory_path: The directory path to extract values from.

    Returns:
        A tuple containing the extracted delay and bandwidth values.
    """

    delays = set()
    bandwidths = set()
    queue_sizes = set()

    for threshold_dir in os.listdir(directory_path):
        threshold_path = os.path.join(directory_path, threshold_dir)
        if os.path.isdir(threshold_path) and not threshold_dir.startswith("."):
            for delay_dir in os.listdir(threshold_path):
                if "ms" in delay_dir:
                    delay_value = int(delay_dir.rstrip("ms"))
                    delays.add(delay_value)

                    delay_path = os.path.join(threshold_path, delay_dir)
                    for bandwidth_dir in os.listdir(delay_path):
                        if "mbit" in bandwidth_dir:
                            bandwidth_value = int(bandwidth_dir.rstrip("mbit"))
                            bandwidths.add(bandwidth_value)

                            bandwidth_path = os.path.join(delay_path, bandwidth_dir)
                            for queue_size_dir in os.listdir(bandwidth_path):
                                if "bdp" in queue_size_dir:
                                    queue_size_value = float(
                                        queue_size_dir.rstrip("bdp")
                                    )
                                    queue_size_in_bytes = utils.calculate_queue_size(
                                        bandwidth_value, delay_value, queue_size_value
                                    )
                                    queue_sizes.add(int(queue_size_in_bytes))

    return (sorted(list(delays)), sorted(list(bandwidths)), sorted(list(queue_sizes)))


def extract_metrics(thresholds_and_metric_files: dict) -> dict:
    """Extract the metrics from the given metric files.

    Args:
        thresholds_and_metric_files: Dictionary containing the metric files organized by threshold.

    Returns:
        A dictionary containing the metrics organized by threshold.
    """
    thresholds_and_metrics = {}
    for threshold in thresholds_and_metric_files.keys():
        if threshold not in thresholds_and_metrics:
            thresholds_and_metrics[threshold] = []

        metric_files = thresholds_and_metric_files[threshold]
        for metric_file in metric_files:
            metrics = {}
            retransmissions = utils.get_retransmissions(metric_file)
            throughput = utils.get_throughput(metric_file)
            metrics["throughput"] = throughput
            metrics["retransmissions"] = retransmissions
            thresholds_and_metrics[threshold].append(metrics)

    return thresholds_and_metrics


def calculate_median(sorted_metrics: list, metric: types.Metric) -> float:
    """Calculate the median for the given metric.

    Args:
        sorted_metrics: Sorted list of metrics.
        metric: The metric that should be used.

    Returns:
        The median for the given metric.
    """
    if len(sorted_metrics) % 2 == 0:
        median = (
            sorted_metrics[len(sorted_metrics) // 2 - 1][metric.value]
            + sorted_metrics[len(sorted_metrics) // 2][metric.value]
        ) / 2
    else:
        median = sorted_metrics[len(sorted_metrics) // 2][metric.value]

    return median


def create_box_plots(
    directory_path: str,
    output_path: str,
    cong_alg: CongestionControlAlgorithm,
    no_title_and_caption: bool = False,
    larger_fonts: bool = False,
):
    """Create the box plots for the given directory.

    Args:
        directory_path: Path to the main directory that contains the directories for the specific thresholds.
        output_path: Path to where the plots should be saved.
        cong_alg: The congestion control algorithm that was used.
        no_title_and_caption: If the title and caption should be included in the plot or not.
        larger_fonts: If the fonts should be larger or not.
    """
    print("Creating box plots...")

    thresholds_and_results = utils.get_results(directory_path)

    delay, bandwidth, queue_size = extract_parameters(directory_path)

    figure_title = (
        map_cong_alg_to_title(cong_alg, directory_path)
        if not no_title_and_caption
        else None
    )
    figure_caption = (
        create_caption(bandwidth, delay, queue_size)
        if not no_title_and_caption
        else None
    )

    throughput_plot_path = os.path.join(output_path, "throughput.png")
    retransmissions_plot_path = os.path.join(output_path, "retransmissions.png")

    thresholds_and_five_number_summary_throughput = utils.get_five_number_summary(
        thresholds_and_results, types.Metric.THROUGHPUT
    )
    sorted_thresholds_and_five_number_summary_throughput = {
        k: thresholds_and_five_number_summary_throughput[k]
        for k in sorted(thresholds_and_five_number_summary_throughput, reverse=False)
    }

    thresholds_and_five_number_summary_retransmissions = utils.get_five_number_summary(
        thresholds_and_results, types.Metric.RETRANSMISSIONS
    )
    sorted_thresholds_and_five_number_summary_retransmissions = {
        k: thresholds_and_five_number_summary_retransmissions[k]
        for k in sorted(
            thresholds_and_five_number_summary_retransmissions, reverse=False
        )
    }

    baseline_throughput_data = sorted_thresholds_and_five_number_summary_throughput[1.0]
    percentage_change_throughput = utils.calculate_percentage_change(
        {
            k: v
            for k, v in sorted_thresholds_and_five_number_summary_throughput.items()
            if k != 1.0
        },
        baseline_throughput_data,
    )

    baseline_retransmissions_data = (
        sorted_thresholds_and_five_number_summary_retransmissions[1.0]
    )
    percentage_reduction_retransmissions = utils.calculate_percentage_reduction(
        {
            k: v
            for k, v in sorted_thresholds_and_five_number_summary_retransmissions.items()
            if k != 1.0
        },
        baseline_retransmissions_data,
    )

    # Create the throughput plot.
    utils.create_box_plot(
        percentage_change_throughput,
        "Classification threshold",
        "Throughput change (%)",
        figure_title,
        figure_caption,
        throughput_plot_path,
        larger_fonts,
    )

    # Create the retransmissions plot.
    utils.create_box_plot(
        percentage_reduction_retransmissions,
        "Classification threshold",
        "Retransmissions reduction (%)",
        figure_title,
        figure_caption,
        retransmissions_plot_path,
        larger_fonts,
    )


def main():
    argparse = init_argparse()
    args = argparse.parse_args()

    create_box_plots(
        args.directory_path,
        args.output_path,
        args.cong_alg,
        args.no_title_and_caption,
        args.larger_fonts,
    )


if __name__ == "__main__":
    main()
