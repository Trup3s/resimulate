#!/usr/bin/env python
# PYTHON_ARGCOMPLETE_OK

import argparse

import argcomplete
from pySim.apdu_source.gsmtap import GsmtapApduSource

from commands.record import Recorder

parser = argparse.ArgumentParser(
    description="ReSIMulate is a terminal application built for eSIM and SIM-specific APDU analysis. It captures APDU commands, saves them, and replays them to facilitate differential testing, ensuring accurate validation and debugging of SIM interactions.",
    formatter_class=argparse.ArgumentDefaultsHelpFormatter,
)

subparsers = parser.add_subparsers(
    title="Commands",
    dest="command",
    required=True,
    help="Available commands: record, replay",
)
parser.add_argument(
    "-v", "--verbose", action="store_true", help="Enable verbose output during replay."
)
parser.add_argument("--version", action="version", version="%(prog)s 0.1")

# Record command
record_parser = subparsers.add_parser(
    "record",
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
    "-i",
    "--bind-ip",
    default="127.0.0.1",
    help="Local IP address to which to bind the UDP port. (default: '127.0.0.1')",
)
record_parser.add_argument(
    "-p", "--bind-port", default=4729, help="Local UDP port. (default: '4729')"
)
record_parser.add_argument(
    "-t",
    "--timeout",
    type=int,
    default=10,
    help="Timeout in seconds for recording (default: 10).",
)

# Replay command
replay_parser = subparsers.add_parser(
    "replay", help="Replay saved APDU commands to a target device."
)
replay_parser.add_argument(
    "-i",
    "--input",
    required=True,
    type=argparse.FileType("r"),
    help="File containing APDU commands to replay (e.g., 'commands.apdu').",
)
replay_parser.add_argument(
    "-d",
    "--device",
    type=str,
    default="default_device",
    help="Target simtrace device to send APDU commands (default: 'default_device').",
)

if __name__ == "__main__":
    # TODO: Configure argcomplete for shell tab completion
    # argcomplete.autocomplete(parser)
    args = parser.parse_args()

    if args.command == "record":
        source = GsmtapApduSource(args.bind_ip, args.bind_port)
        recorder = Recorder(source)
        recorder.record(args.output, args.timeout)

    elif args.command == "replay":
        pass

    else:
        raise ValueError(f"Unsupported command: {args.command}")
