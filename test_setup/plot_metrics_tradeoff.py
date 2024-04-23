import matplotlib.pyplot as plt
import os
import utils.util as utils
import utils.types as types

from argparse import ArgumentParser
from argparse import BooleanOptionalAction


def init_argparse():
    parser = ArgumentParser(
        usage="python %(prog)s [options]",
        description="Create a trade-off plot for retransmissions and throughput for various classification thresholds",
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
        "--output_dir",
        metavar="OUTPUT_DIR",
        type=str,
        required=False,
        help="Path to the directory where the plots should be saved",
    )
    parser.add_argument(
        "--larger_fonts",
        metavar="LARGER_FONTS",
        action=BooleanOptionalAction,
        default=False,
        help="If the fonts should be larger or not",
    )

    return parser


def extract_summary(results: dict) -> dict:
    """Extracts a summary (five-number summary) of the throughput and retransmissions for each threshold.

    Args:
        results: Dictionary containing the metrics organized by threshold.

    Returns:
        A dictionary containing the thresholds as keys and a dictionary containing the five-number summary
        for both throughput and retransmissions as values.
    """
    throughput_summaries = utils.get_five_number_summary(
        results, types.Metric.THROUGHPUT
    )
    retransmissions_summaries = utils.get_five_number_summary(
        results, types.Metric.RETRANSMISSIONS
    )

    summary = {}
    for threshold in results.keys():
        summary[threshold] = {
            "throughput": throughput_summaries[threshold],
            "retransmissions": retransmissions_summaries[threshold],
        }

    return summary


def plot_tradeoff(directory_path: str, output_dir: str, larger_fonts: bool = False):
    """Plot the trade-off between retransmissions and throughput for various classification thresholds.

    Args:
        directory_path: Path to the directory that contains the directories for the various thresholds.
        output_dir: Where the plots should be saved.
        larger_fonts: If the fonts should be larger or not.
    """
    results = utils.get_results(directory_path)
    summary = extract_summary(results)

    baseline_throughput = summary[1.0]["throughput"]
    baseline_retransmissions = summary[1.0]["retransmissions"]

    x_values, y_values, sizes, colors = [], [], [], []
    labels = ["0.1th", "0.25th", "0.5th"]
    color_map = {"0.1th": "purple", "0.25th": "red", "0.5th": "blue"}

    for threshold in [0.1, 0.25, 0.5]:
        throughput_change = utils.calculate_percentage_change_simple(
            summary[threshold]["throughput"], baseline_throughput
        )
        retransmission_reduction = utils.calculate_percentage_reduction_simple(
            summary[threshold]["retransmissions"], baseline_retransmissions
        )

        x_values.append(throughput_change["median"])
        y_values.append(retransmission_reduction["median"])

        diameter = retransmission_reduction["q3"] - retransmission_reduction["q1"]
        if diameter < 0:
            diameter = diameter * -1
        sizes.append(diameter)

        colors.append(color_map[str(threshold) + "th"])

    if larger_fonts:
        plt.rcParams.update({"font.size": 14})
    else:
        plt.rcParams.update({"font.size": 10})

    plt.scatter(x_values, y_values, s=[d**2 for d in sizes], c=colors, alpha=0.5)

    for i, label in enumerate(labels):
        # Move label to the right by adding diameter to the x-value of the circle
        adjusted_x = x_values[i] + (sizes[i] ** 0.5) / 2.2

        plt.annotate(
            label,
            (adjusted_x, y_values[i]),
            fontsize=14 if larger_fonts else 10,
            ha="left",
            va="center",
            fontweight="bold",
        )

    plt.xlabel("Throughput change (%)")
    plt.ylabel("Retransmission reduction (%)")
    plt.xlim(min(x_values) - 10, max(x_values) + 15)
    plt.ylim(min(y_values) - 10, max(y_values) + 10)

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    plt.grid(True)

    # Adjusting the bottom layout to prevent text from being cut off
    plt.tight_layout()
    plt.subplots_adjust(bottom=0.15)

    plt.savefig(
        os.path.join(output_dir, "retransmissions_vs_throughput.png"),
        format="png",
        dpi=300,
    )
    plt.savefig(
        os.path.join(output_dir, "retransmissions_vs_throughput.pdf"),
        format="pdf",
    )

    plt.show()


def main():
    parser = init_argparse()
    args = parser.parse_args()
    output_dir = (
        args.output_dir
        if args.output_dir
        else os.path.join(args.directory_path, "output")
    )
    plot_tradeoff(args.directory_path, output_dir, args.larger_fonts)


if __name__ == "__main__":
    main()
