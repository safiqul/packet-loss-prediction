import os
import re
import utils.util as utils

from argparse import ArgumentParser
from pathlib import Path


def init_argparse() -> ArgumentParser:
    """Initialize the argument parser.

    Returns:
        The initialized argument parser.
    """
    parser = ArgumentParser(
        usage="python %(prog)s -d <directory_path>",
        description="Calculate the average throughput and retransmissions for the given metrics",
    )
    parser.add_argument(
        "-d",
        "--directory_path",
        metavar="DIRECTORY_PATH",
        type=Path,
        required=True,
        help="Path to the directory that contains the directories with the metrics",
    )

    return parser


def get_average_throughput(metric_files: list) -> float:
    """Calculate the average throughput for the given metric files.

    Args:
        metric_files: The contents of the various metric files.

    Returns:
        The average throughput.
    """
    throughput_regex = re.compile(r"Throughput: (\d+\.\d+)Mbps")
    throughputs = [
        float(re.findall(throughput_regex, metric_file)[0])
        for metric_file in metric_files
    ]

    return sum(throughputs) / len(throughputs)


def get_avg_retransmissions(metric_files: list) -> float:
    """Calculate the average number of retransmissions for the given metric files.

    Args:
        metric_files: The contents of the various metric files.

    Returns:
        The average number of retransmissions.
    """
    retransmissions_regex = re.compile(r"Retransmissions: (\d+)")
    retransmissions = [
        int(re.findall(retransmissions_regex, metric_file)[0])
        for metric_file in metric_files
    ]

    return round(sum(retransmissions) / len(retransmissions))


def write_results(
    dir_path: str, avg_throughput: float, avg_retransmissions: int
) -> None:
    """Write the results to a file.

    Args:
        dir_path: Path to the directory that contains the directories with the results.
        avg_throughput: The average throughput.
        avg_retransmissions: The average number of retransmissions.
    """
    with open(os.path.join(dir_path, "results.txt"), "w") as results_file:
        results_file.write(f"Average throughput: {round(avg_throughput, 2)}Mbps\n")
        results_file.write(f"Average retransmissions: {avg_retransmissions}\n")


def calculate_and_write_results(dir_path: str) -> None:
    """Calculate the average throughput and retransmissions for the given results.

    Args:
        dir_path: Path to the directory that contains the directories with the results.
    """
    metric_files = utils.read_metric_files(dir_path)
    avg_throughput = get_average_throughput(metric_files)
    avg_retransmissions = get_avg_retransmissions(metric_files)

    write_results(dir_path, avg_throughput, avg_retransmissions)


def main():
    parser = init_argparse()
    args = parser.parse_args()

    calculate_and_write_results(args.directory_path)


if __name__ == "__main__":
    main()
