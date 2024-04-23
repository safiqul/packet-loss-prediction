import itertools
import csv


def create_permutations(bandwidths: list, queue_sizes: list, thresholds: list) -> list:
    """Create all possible permutations of the connection parameters.

    Args:
        bandwidths: All possible bandwidths.
        queue_sizes: All possible queue sizes.
        thresholds: All possible thresholds.

    Returns:
        A list of all possible permutations of the connection parameters.
    """
    permutations = list(itertools.product(bandwidths, queue_sizes, thresholds))
    return [list(permutation) for permutation in permutations]


def create_csv(file_path: str, permutations: list):
    """Create a csv file with all possible permutations of the connection parameters.

    Args:
        permutations: A list of all possible permutations of the connection parameters.
    """
    with open(file_path, mode="w", newline="") as csv_file:
        fieldnames = ["bandwidth", "queue_size", "threshold"]
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)

        writer.writeheader()
        for permutation in permutations:
            writer.writerow(
                {
                    "bandwidth": permutation[0],
                    "queue_size": permutation[1],
                    "threshold": permutation[2],
                }
            )

    print(f"CSV file created at {file_path}")


def main():
    bandwidths = [10, 50]
    queue_sizes = [0.25, 0.5, 1]
    thresholds = [0.1, 0.25, 0.5, 1.0]

    permutations = create_permutations(bandwidths, queue_sizes, thresholds)
    create_csv("test_parameter_combinations.csv", permutations)


if __name__ == "__main__":
    main()
