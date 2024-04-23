import glob
import os
import gzip

from argparse import ArgumentParser


def init_argparse() -> ArgumentParser:
    """Initialize the argument parser.

    Returns:
        ArgumentParser: The argument parser.

    """

    DEFAULT_THRESHOLD = 10

    parser = ArgumentParser(
        description="Merge measurements and filter by RTT threshold."
    )
    parser.add_argument(
        "-t",
        "--threshold",
        type=float,
        default=DEFAULT_THRESHOLD,
        help="RTT threshold in seconds",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default="",
        help="Output file path. If not specified, the file will be saved in the current directory with the default name.",
    )

    return parser


def main():
    parser = init_argparse()
    args = parser.parse_args()

    # Merge all text files in the current directory into a single file.
    dir_name = os.path.basename(os.getcwd())

    output_file = ""
    if args.output == "":
        output_file = f"{dir_name}_merged_data.txt"
    else:
        output_file = args.output

    outfile = open(output_file, "w")

    rtt_index = 5
    rtt_value = cumulative_rtt = 0

    threshold = args.threshold * 1000

    for filename in glob.glob("*.txt"):
        with open(filename) as infile:
            lines = infile.readlines()

            for i, line in enumerate(lines):
                if cumulative_rtt > threshold:
                    outfile.writelines(lines[i:])
                    break

                if "rtt:" in line:
                    words = line.split()

                    rtt_value = float(words[rtt_index].split(":")[1].split("/")[0])

                cumulative_rtt += rtt_value / 5

    outfile.close()

    # Gzip the merged file.
    with open(output_file, "rb") as infile:
        with gzip.open(f"{output_file}.gz", "wb") as outfile:
            outfile.writelines(infile)

    # Remove the uncompressed file.
    os.remove(output_file)

    print(f"Merged data saved to {os.path.abspath(output_file)}.gz")


if __name__ == "__main__":
    main()
