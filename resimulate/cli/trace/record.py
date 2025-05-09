import argparse

from pySim.apdu_source.gsmtap import GsmtapApduSource
from rich_argparse import RichHelpFormatter

from resimulate.trace.record import Recorder
from resimulate.util.enums import ISDR_AID


def add_subparser(
    parent_parser: argparse._SubParsersAction,
) -> None:
    parser: argparse.ArgumentParser = parent_parser.add_parser(
        "record",
        formatter_class=RichHelpFormatter,
        help="Record APDU commands from a specified source.",
        description="Record APDU commands from a specified source. The recorder relies on simtrace-sniff to be running in the background and sending the apdus as udp packages to a local socket. First start the recording and the simtrace-sniff to not block the socket.",
    )
    parser.add_argument(
        "-o",
        "--output",
        required=True,
        type=str,
        help="Output file (e.g. 'commands.apdu')",
    )
    parser.add_argument(
        "--isd-r",
        type=ISDR_AID.from_description,
        default=ISDR_AID.DEFAULT.description,
        choices=ISDR_AID.get_all_descriptions(),
        help="ISD-R to use. (default: %(default)s)",
    )
    parser.add_argument(
        "-i",
        "--bind-ip",
        default="127.0.0.1",
        help="Local IP to bind. (default: %(default)s)",
    )
    parser.add_argument(
        "-p", "--bind-port", default=4729, help="Local UDP port. (default: %(default)s)"
    )
    parser.add_argument(
        "-t",
        "--timeout",
        type=int,
        default=15,
        help="Timeout in seconds. (default: %(default)s)",
    )


def run(args: argparse.Namespace) -> None:
    source: GsmtapApduSource = GsmtapApduSource(args.bind_ip, int(args.bind_port))
    recorder: Recorder = Recorder(source, args.isd_r)
    recorder.record(args.output, args.timeout)
