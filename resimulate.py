#!/usr/bin/env python
# PYTHON_ARGCOMPLETE_OK

import argparse
import logging
from argparse import Namespace

import argcomplete
from rich_argparse import RichHelpFormatter

from resimulate.commands import lpa, trace
from resimulate.util import get_pcsc_devices, get_version
from resimulate.util.logger import log

devices: list[str] = get_pcsc_devices()
parser = argparse.ArgumentParser(
    description="ReSIMulate is a terminal application and library built for eSIM and SIM-specific APDU analysis.",
    formatter_class=RichHelpFormatter,
)

parser.add_argument("--version", action="version", version=f"%(prog)s {get_version()}")

parser.add_argument(
    "-v", "--verbose", action="store_true", help="Enable verbose output during replay."
)
parser.add_argument(
    "-p",
    "--pcsc-device",
    type=int,
    default=0,
    choices=range(len(devices)),
    help=f"PC/SC device index (default: %(default)s). {' '.join(devices)}",
)

subparsers = parser.add_subparsers(
    title="Commands", dest="command", required=True, help="Available commands"
)

# Attach command subparsers
lpa.add_subparser(subparsers)
trace.add_subparser(subparsers)


def main():
    argcomplete.autocomplete(parser)
    args: Namespace = parser.parse_args()

    log.setLevel(logging.DEBUG if args.verbose else logging.INFO)

    if args.command == "trace":
        trace.run(args)
    elif args.command == "lpa":
        lpa.run(args)
    else:
        raise ValueError(f"Unsupported command: {args.command}")


if __name__ == "__main__":
    main()
