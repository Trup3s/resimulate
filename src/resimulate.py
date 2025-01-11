#!/usr/bin/env python
# PYTHON_ARGCOMPLETE_OK

import argparse, argcomplete

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

# Record command
record_parser = subparsers.add_parser(
    "record", help="Record APDU commands from a specified source."
)
record_parser.add_argument(
    "-o",
    "--output",
    required=True,
    type=str,
    help="File to save recorded APDU commands (e.g., 'commands.apdu').",
)
record_parser.add_argument(
    "-d",
    "--device",
    type=str,
    default="default_device",
    help="Device or interface to listen for APDU commands (default: 'default_device').",
)
record_parser.add_argument(
    "-t",
    "--timeout",
    type=int,
    default=30,
    help="Timeout in seconds for recording (default: 30).",
)

# Replay command
replay_parser = subparsers.add_parser(
    "replay", help="Replay saved APDU commands to a target device."
)
replay_parser.add_argument(
    "-i",
    "--input",
    required=True,
    type=str,
    help="File containing APDU commands to replay (e.g., 'commands.apdu').",
)
replay_parser.add_argument(
    "-d",
    "--device",
    type=str,
    default="default_device",
    help="Target simtrace device to send APDU commands (default: 'default_device').",
)
replay_parser.add_argument(
    "-v", "--verbose", action="store_true", help="Enable verbose output during replay."
)

if __name__ == "__main__":
    argcomplete.autocomplete(parser)
    args = parser.parse_args()
