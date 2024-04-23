import xgboost as xgb
import pandas as pd
import utils.util as utils
import sys
import time

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from argparse import ArgumentParser
from argparse import BooleanOptionalAction

output_path = ""
timestamp_mode = False


class EventHandler(FileSystemEventHandler):
    """Custom event handler for the watchdog observer.

    Monitors specific filesystem changes such as file modification, creation,
    deletion, and movement. The event handler is called when a change occurs
    and the corresponding method is called.

    Attributes:
        dir_path: The directory path that should be watched.
        file_path: Path to the file that should contain the input data.
        classifier: The classifier to use for the prediction.
        classification_threshold: The optional classification threshold to use for the prediction.
    """

    def __init__(
        self,
        dir_path: str,
        file_path: str,
        classifier: xgb.XGBClassifier,
        classification_threshold: float = None,
        *args,
        **kwargs,
    ):
        """Initializes the EventHandler with a specific file path.

        Args:
            file_path (str): Path to the file that should be loaded and parsed.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.
        """
        super().__init__(*args, **kwargs)
        self.dir_path = dir_path
        self.file_path = file_path
        self.classifier = classifier
        self.classification_threshold = classification_threshold
        self.timeout = time.time() + 5
        self.time_started = time.time()

    def on_modified(self, event):
        """Handles the file or directory modification event.

        When a file is modified, the relative_path is compared to
        the file_path. If they are equal, the file is loaded as a pandas
        dataframe and a prediction is performed using the classifier.

        Args:
            event (FileSystemEvent): Event representing filesystem change.
        """
        self.timeout = time.time() + 5

        if event.is_directory:
            return

        print("\n\nModified event")

        relative_path = utils.get_relative_path(event.src_path)
        if relative_path != self.file_path:
            print("Not the relevant output file.")
            return

        input = load_dataframe(self.file_path)
        if input is None:
            return

        prediction = predict(self.classifier, input, self.classification_threshold)
        if output_path != "" and timestamp_mode:
            timestamp = time.time() - self.time_started
            utils.append_to_file(output_path, f"{timestamp}: {int(prediction)}\n")
        elif output_path != "":
            utils.write_to_file(output_path, str(int(prediction)))

    def on_created(self, event):
        """Handles the file or directory creation event.

        When a file is created, the relative_path is compared to
        the file_path. If they are equal, the file is loaded as a pandas
        dataframe and a prediction is performed using the classifier.

        Args:
            event (FileSystemEvent): Event representing filesystem change.
        """
        self.timeout = time.time() + 5

        if event.is_directory:
            return

        print("\n\nCreated event")

        relative_path = utils.get_relative_path(event.src_path)
        print(f"Relative path: {relative_path}")
        if relative_path != self.file_path:
            print("Not the relevant output file.")
            return

        input = load_dataframe(self.file_path)
        if input is None:
            return

        prediction = predict(self.classifier, input, self.classification_threshold)
        if output_path != "" and timestamp_mode:
            timestamp = time.time() - self.time_started
            utils.append_to_file(output_path, f"{timestamp}: {int(prediction)}\n")
        elif output_path != "":
            utils.write_to_file(output_path, str(int(prediction)))

    def on_moved(self, event):
        """Handles the file or directory movement event.

        Args:
            event (FileSystemEvent): Event representing filesystem change.
        """
        # Not relevant.

    def on_deleted(self, event):
        """Handles the file or directory deletion event.

        Args:
            event (FileSystemEvent): Event representing filesystem change.
        """
        # Not relevant.


def init_argparse() -> ArgumentParser:
    """Initialize argparse with the required arguments.

    Returns:
        The initialized argument parser.
    """
    parser = ArgumentParser(
        description="Predict packet loss using the chosen classifier",
        usage="python %(prog)s -c <classifier> -d <directory_path> -i <input_file> -o <output_file> -t <classification_threshold>",
    )

    parser.add_argument(
        "-c",
        "--classifier_path",
        metavar="CLASSIFIERPATH",
        type=str,
        required=True,
        help="Path to the saved classifier to use for the prediction",
    )
    parser.add_argument(
        "-d",
        "--directory_path",
        metavar="DIRECTORY_PATH",
        type=str,
        required="--time" not in sys.argv,
        help="Path to the directory that should be watched for changes",
    )
    parser.add_argument(
        "-i",
        "--input_file",
        metavar="INPUT_FILE",
        type=str,
        required="--time" not in sys.argv,
        help="Path to the csv file that contains the input data",
    )
    parser.add_argument(
        "-o",
        "--output_file",
        metavar="OUTPUT_FILE",
        type=str,
        help="Path to the file that should contain the output data",
    )
    parser.add_argument(
        "-t",
        "--threshold",
        metavar="THRESHOLD",
        type=float,
        help="Classification threshold to use for the prediction",
    )
    parser.add_argument(
        "--timestamp_mode",
        metavar="TIMESTAMP_MODE",
        type=bool,
        action=BooleanOptionalAction,
        default=False,
        help="If predictions should be appended to the output file along with timestamps",
    )
    parser.add_argument(
        "--time",
        metavar="TIME",
        type=bool,
        action=BooleanOptionalAction,
        default=False,
        help="Time the execution of the module with the given classifier without running the observer",
    )

    return parser


def observe(
    dir_path: str,
    file_path: str,
    classifier_path: str,
    classification_threshold: float = None,
) -> None:
    """Observe the directory with the given path for changes and perform a prediction.

    Observes the directory with the given path for changes. If there is a change,
    an event handler is called that loads the csv file located at the given path
    and performs a prediction using the given classifier and classification threshold
    if supplied.

    Args:
        dir_path: The directory path that should be watched.
        file_path: The path to the text file that should be loaded and parsed.
        classifier_path: The path to the saved classifier to use for the prediction.
        classification_threshold: The optional classification threshold to use for the prediction.
    """
    classifier = load_classifier(classifier_path)
    event_handler = EventHandler(
        dir_path, file_path, classifier, classification_threshold
    )

    observer = Observer()
    observer.schedule(event_handler, path=dir_path)
    observer.start()

    print("Prediction module started. Waiting for changes...\n\n")

    try:
        while observer.is_alive() and time.time() < event_handler.timeout:
            observer.join(1)
    finally:
        observer.stop()
        observer.join()


def load_dataframe(input_path: str) -> pd.DataFrame | None:
    """Load the input data as a pandas dataframe.

    Args:
        input_path: The path to the csv file containing the ss data.

    Returns:
        The loaded data as a pandas dataframe or None if an error occurred.
    """
    try:
        return pd.read_csv(input_path)
    except Exception as e:
        print(f"Error loading input data: {e}")
        return None


def load_classifier(classifier_path: str) -> object:
    """Load the classifier for the given classifier path.

    Args:
        classifier_path: The path to the saved classifier.

    Returns:
        The loaded classifier.
    """
    classifier = xgb.XGBClassifier()

    try:
        classifier.load_model(classifier_path)
    except Exception as e:
        print(f"Error loading classifier: {e}")
        raise SystemExit()

    return classifier


def predict(
    classifier: xgb.XGBClassifier,
    input: pd.DataFrame,
    classification_threshold: float = None,
) -> bool:
    """Use the given classifier and input data to predict the result with an optional classification threshold.

    Performs a prediction using the given classifier and input data. If a classification threshold is given,
    the probability is predicted and compared to the threshold and the result is returned.

    Args:
        classifier: The classifier to use for the prediction.
        input: The input data to use for the prediction.
        classification_threshold: The optional classification threshold to use for the prediction.

    Returns:
        The result of the prediction.
    """

    if classification_threshold is None:
        return bool(classifier.predict(input)[0])

    prediction = classifier.predict_proba(input)
    prediction = prediction[0][1]

    return prediction >= classification_threshold


def predict_test(classifier_path: str) -> None:
    """Perform a test prediction using the given classifier and example input data.

    Args:
        classifier_path: The path to the classifier to use for the prediction.
    """
    classifier = load_classifier(classifier_path)
    input = load_dataframe("output/test/predict/input_data.csv")

    predict(classifier, input)


def main():
    parser = init_argparse()
    args = parser.parse_args()

    global output_path
    if args.output_file:
        output_path = args.output_file

    global timestamp_mode
    if args.timestamp_mode:
        timestamp_mode = True

    if args.time:
        utils.time_execution(
            lambda: predict_test(args.classifier_path),
            "predict_test",
            num_executions=10000,
        )
    else:
        if args.threshold:
            observe(
                args.directory_path,
                args.input_file,
                args.classifier_path,
                args.threshold,
            )
        else:
            observe(args.directory_path, args.input_file, args.classifier_path)


if __name__ == "__main__":
    main()
