import utils.util as utils
import utils.types as types

from argparse import ArgumentParser
from pathlib import Path


def init_argparse() -> ArgumentParser:
    """Initialize the argument parser.

    Returns:
        The initialized argument parser.
    """
    parser = ArgumentParser(
        usage="python %(prog)s -i <input_file> -f <feature> -d <duration>",
        description="Plot a given feature vs. the timestamps.",
    )
    parser.add_argument(
        "-i",
        "--input_file",
        metavar="INPUT_FILE",
        type=Path,
        required=True,
        help="Path to the input file that contains the ss data",
    )
    parser.add_argument(
        "-f",
        "--feature",
        metavar="FEATURE",
        type=types.Feature,
        required=True,
        help="The feature that should be plotted",
    )
    parser.add_argument(
        "-d",
        "--duration",
        metavar="DURATION",
        type=int,
        required=True,
        help="Duration that the measurement was running for in seconds",
    )

    return parser


def plot_feature(input_file: Path, feature: types.Feature, duration: int) -> None:
    """Plot the given feature vs. the timestamps.

    Args:
        input_file: Path to the input file that contains the ss data.
        feature: The feature that should be plotted.
        duration: Duration that the measurement was running for in seconds.
    """
    ss_outputs = utils.read_ss(input_file)
    ss_interval = utils.calculate_ss_interval(duration, len(ss_outputs))

    feature_values = utils.get_feature_values(ss_outputs, feature)

    timestamps = [i * ss_interval for i in range(len(feature_values))]

    output_path = input_file.parent

    utils.create_and_save_line_chart(
        timestamps,
        feature_values,
        "Time (s)",
        feature.name.lower(),
        f"{output_path}/output/{feature.name.lower()}.png",
    )


def main():
    parser = init_argparse()
    args = parser.parse_args()

    plot_feature(args.input_file, args.feature, args.duration)


if __name__ == "__main__":
    main()
