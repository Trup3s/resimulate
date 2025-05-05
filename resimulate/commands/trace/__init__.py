import argparse

from rich_argparse import RichHelpFormatter
from resimulate.commands.trace import record, replay


def add_subparser(parent_parser: argparse._SubParsersAction) -> None:
    trace_parser: argparse.ArgumentParser = parent_parser.add_parser(
        "trace",
        help="Trace-level operations (record, replay)",
        formatter_class=RichHelpFormatter,
    )
    trace_subparsers = trace_parser.add_subparsers(dest="trace_command", required=True)
    record.add_subparser(trace_subparsers)
    replay.add_subparser(trace_subparsers)


def run(args: argparse.Namespace) -> None:
    if args.trace_command == "record":
        record.run(args)
    elif args.trace_command == "replay":
        replay.run(args)
    else:
        raise ValueError(f"Unknown trace command: {args.trace_command}")
