import argparse

from rich_argparse import RichHelpFormatter

from resimulate.cli.lpa import euicc, notification, profile
from resimulate.euicc.card import Card
from resimulate.euicc.transport.pcsc_link import PcscLink


def add_subparser(parent: argparse._SubParsersAction) -> None:
    lpa_parser: argparse.ArgumentParser = parent.add_parser(
        "lpa",
        help="Local Profile Assistant operations",
        formatter_class=RichHelpFormatter,
    )
    lpa_parser.add_argument(
        "--max-apdu-size",
        type=int,
        default=255,
        required=False,
        help="Max APDU size (default: %(default)s)",
    )

    lpa_subparsers = lpa_parser.add_subparsers(dest="lpa_command", required=True)
    profile.add_subparser(lpa_subparsers)
    notification.add_subparser(lpa_subparsers)
    euicc.add_subparser(lpa_subparsers)


def run(args: argparse.Namespace) -> None:
    with PcscLink(apdu_data_size=args.max_apdu_size) as link:
        card = Card(link)
        if args.lpa_command == "profile":
            profile.run(args, card)
        elif args.lpa_command == "notification":
            notification.run(args, card)
        elif args.lpa_command == "euicc":
            euicc.run(args, card)
        else:
            raise ValueError(f"Unknown lpa command: {args.lpa_command}")
