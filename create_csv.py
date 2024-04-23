import itertools
import csv

from argparse import ArgumentParser
from argparse import BooleanOptionalAction


def create_permutations(
    bandwidths: list,
    delays: list,
    bdps: list,
    congestion_control_algorithms: list,
    scenarios: list = ["reno"],
) -> list:
    """Create all possible permutations of the connection parameters.

    Args:
        bandwidths: All possible bandwidths.
        delays: All possible delays.
        bdps: All possible bdps.
        congestion_control_algorithms: All possible congestion control algorithms.
        scenarios: All possible scenarios.


    Returns:
        A list of all possible permutations of the connection parameters.
    """
    permutations = list(
        itertools.product(
            bandwidths, delays, bdps, congestion_control_algorithms, scenarios
        )
    )
    permutations = [list(permutation) for permutation in permutations]

    # Calculate the BDP for each permutation.
    for permutation in permutations:
        bandwidth, delay, bdp = permutation[0], permutation[1], permutation[2]
        calculated_bdp = bandwidth * 125000 * delay / 1000 * bdp
        permutation[2] = int(calculated_bdp)

    return permutations


def create_csv(file_path: str, permutations: list):
    """Create a csv file with all possible permutations of the connection parameters.

    Args:
        permutations: A list of all possible permutations of the connection parameters.
    """
    with open(file_path, mode="w", newline="") as csv_file:
        fieldnames = ["bw", "delay", "bdp", "cc_algo", "scenario"]
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)

        writer.writeheader()
        for permutation in permutations:
            writer.writerow(
                {
                    "bw": permutation[0],
                    "delay": permutation[1],
                    "bdp": permutation[2],
                    "cc_algo": permutation[3],
                    "scenario": permutation[4],
                }
            )

    print(f"CSV file created at {file_path}")


def init_argparse() -> ArgumentParser:
    """Initialize the argument parser.

    Returns:
        The argument parser.
    """
    parser = ArgumentParser(
        description="Create a csv file with all possible permutations of the connection parameters",
        usage="python create_csv.py [-h] [--scenarios/--no-scenarios SCENARIOS]",
    )
    parser.add_argument(
        "--scenarios",
        metavar="SCENARIOS",
        type=bool,
        action=BooleanOptionalAction,
        default=False,
        help="Whether to include scenarios or not",
    )

    return parser


def main():
    bandwidths = [10, 20, 30, 40, 50]
    delays = [30, 40, 50, 60, 70]
    bdps = [0.25, 0.5, 1]
    congestion_control_algorithms = ["reno", "cubic"]
    scenarios = ["reno", "cubic", "half"]

    parser = init_argparse()
    args = parser.parse_args()

    print("Scenarios enabled: {}".format(args.scenarios))

    if args.scenarios:
        permutations = create_permutations(
            bandwidths, delays, bdps, congestion_control_algorithms, scenarios
        )
    else:
        permutations = create_permutations(
            bandwidths, delays, bdps, congestion_control_algorithms
        )

    create_csv("connection_parameter_combinations.csv", permutations)


if __name__ == "__main__":
    main()
