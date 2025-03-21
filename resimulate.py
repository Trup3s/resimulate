#!/usr/bin/env python
# PYTHON_ARGCOMPLETE_OK

import argparse
import argcomplete
import logging

from pySim.apdu_source.gsmtap import GsmtapApduSource
from rich_argparse import RichHelpFormatter

from resimulate import util
from resimulate.commands.record import Recorder
from resimulate.commands.replay import Replayer
from resimulate.util import get_version
from resimulate.util.logger import log

parser = argparse.ArgumentParser(
    description="ReSIMulate is a terminal application built for eSIM and SIM-specific APDU analysis. It captures APDU commands, saves them, and replays them to facilitate differential testing, ensuring accurate validation and debugging of SIM interactions.",
    formatter_class=RichHelpFormatter,
)
parser.add_argument(
    "--version",
    action="version",
    version=f"%(prog)s {get_version()}",
)
parser.add_argument(
    "-v",
    "--verbose",
    action="store_true",
    help="Enable verbose output during replay.",
    required=False,
)

global_arg_parser = argparse.ArgumentParser(
    add_help=False, formatter_class=RichHelpFormatter
)

subparsers = parser.add_subparsers(
    title="Commands",
    dest="command",
    required=True,
    help="Available commands: record, replay",
)

# Record command
record_parser = subparsers.add_parser(
    "record",
    parents=[global_arg_parser],
    formatter_class=RichHelpFormatter,
    help="Record APDU commands from a specified source. Uses the SIMtrace2 GSMTAP to capture APDUs via UDP.",
)
record_parser.add_argument(
    "-o",
    "--output",
    required=True,
    type=str,
    help="File to save recorded APDU commands (e.g., 'commands.apdu').",
)
record_parser.add_argument(
    "--isd-r",
    type=str,
    default="default",
    choices=["default", "5ber"],
    help="ISD-R to use for recording APDU commands (default: '%(default)s').",
)
record_parser.add_argument(
    "-i",
    "--bind-ip",
    default="127.0.0.1",
    help="Local IP address to which to bind the UDP port. (default: %(default)s)",
)
record_parser.add_argument(
    "-p", "--bind-port", default=4729, help="Local UDP port. (default: %(default)s)"
)
record_parser.add_argument(
    "-t",
    "--timeout",
    type=int,
    default=15,
    help="Timeout in seconds for recording (default: 10).",
)

# Replay command
replay_parser = subparsers.add_parser(
    "replay",
    parents=[global_arg_parser],
    formatter_class=RichHelpFormatter,
    help="Replay saved APDU commands to a target device.",
)
replay_parser.add_argument(
    "-i",
    "--input",
    required=True,
    type=argparse.FileType("rb"),
    help="File containing APDU commands to replay (e.g., 'commands.apdu').",
)
replay_parser.add_argument(
    "-p",
    "--pcsc-device",
    type=int,
    default=0,
    choices=range(len(util.get_pcsc_devices())),
    help=f"Target PC/SC device to send APDU commands (default: %(default)s). {'\n'.join(util.get_pcsc_devices())}",
)
replay_parser.add_argument(
    "--target-isd-r",
    type=str,
    default="default",
    choices=["default", "5ber"],
    help="Target ISD-R AID to use for replaying APDU commands (default: '%(default)s').",
)
replay_parser.add_argument(
    "--mutate",
    action="store_true",
    default=False,
    help="Mutate APDU commands to test for protocol errors (default: '%(default)s').",
)

argcomplete.autocomplete(parser)

if __name__ == "__main__":
    # TODO: Configure argcomplete for shell tab completion
    # argcomplete.autocomplete(parser)
    args = parser.parse_args()

    log.setLevel(logging.DEBUG if args.verbose else logging.INFO)

    if args.command == "record":
        source = GsmtapApduSource(args.bind_ip, args.bind_port)
        recorder = Recorder(source, args.isd_r)
        recorder.record(args.output, args.timeout)

    elif args.command == "replay":
        replayer = Replayer(args.pcsc_device, args.target_isd_r, args.mutate)
        replayer.replay(args.input.name)

    else:
        raise ValueError(f"Unsupported command: {args.command}")
