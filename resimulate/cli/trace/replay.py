import argparse

from rich_argparse import RichHelpFormatter

from resimulate.trace.replay import Replayer
from resimulate.util.enums import ISDR_AID


def add_subparser(
    parent_parser: argparse._SubParsersAction,
) -> None:
    parser: argparse.ArgumentParser = parent_parser.add_parser(
        "replay",
        formatter_class=RichHelpFormatter,
        help="Replay saved APDU commands to a target device.",
    )
    parser.add_argument(
        "-i", "--input", required=True, type=argparse.FileType("rb"), help="Input file"
    )
    parser.add_argument(
        "--target-isd-r",
        type=ISDR_AID.from_description,
        default=ISDR_AID.DEFAULT.description,
        choices=ISDR_AID.get_all_descriptions(),
        help="Target ISD-R. (default: %(default)s)",
    )
    parser.add_argument(
        "--mutate", action="store_true", default=False, help="Mutate APDUs"
    )


def run(args: argparse.Namespace) -> None:
    replayer: Replayer = Replayer(args.pcsc_device, args.target_isd_r, args.mutate)
    replayer.replay(args.input.name)
