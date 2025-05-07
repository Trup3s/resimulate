import argparse

from rich_argparse import RichHelpFormatter

from resimulate.commands.fuzzer import apdu_fuzz, compare, fuzz


def add_subparser(parent: argparse._SubParsersAction) -> None:
    fuzzer_parser: argparse.ArgumentParser = parent.add_parser(
        "fuzzer",
        help="Fuzzer operations",
        formatter_class=RichHelpFormatter,
    )

    fuzzer_subparsers = fuzzer_parser.add_subparsers(
        dest="fuzzer_command", required=True
    )
    fuzz.add_subparser(fuzzer_subparsers)
    apdu_fuzz.add_subparser(fuzzer_subparsers)
    compare.add_subparser(fuzzer_subparsers)


def run(args: argparse.Namespace) -> None:
    if args.fuzzer_command == "fuzz":
        fuzz.run(args)
    elif args.fuzzer_command == "apdu_fuzz":
        apdu_fuzz.run(args)
    elif args.fuzzer_command == "compare":
        compare.run(args)
    else:
        raise ValueError(f"Unknown fuzzer command: {args.fuzzer_command}")
