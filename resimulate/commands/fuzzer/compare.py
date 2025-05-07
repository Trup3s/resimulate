import argparse

from rich_argparse import RichHelpFormatter

from resimulate.euicc.recorder.recorder import OperationRecorder


def add_subparser(
    parent_parser: argparse._SubParsersAction,
) -> None:
    parser: argparse.ArgumentParser = parent_parser.add_parser(
        "compare",
        formatter_class=RichHelpFormatter,
        help="Compare recorded apdu fuzzings with fuzzing results of other cards.",
        description="Compare recorded apdu fuzzings with fuzzing results of other cards.",
    )
    parser.add_argument(
        "main_fuzzing_file",
        type=argparse.FileType("rb"),
        help="Path to the recorded main apdu fuzzing file (e.g. 'resimulate/recordings/fuzzing.resim')",
    )
    parser.add_argument(
        "compare_fuzzing_files",
        nargs="+",
        type=argparse.FileType("rb"),
        help="Paths to the recorded apdu fuzzing files to compare against (e.g. 'resimulate/recordings/fuzzing1.resim')",
    )


def run(args: argparse.Namespace) -> None:
    OperationRecorder.compare_files(
        args.main_fuzzing_file.name,
        [file.name for file in args.compare_fuzzing_files],
    )
