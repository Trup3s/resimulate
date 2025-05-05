import argparse

from rich import print
from rich_argparse import RichHelpFormatter

from resimulate.euicc.card import Card
from resimulate.euicc.models.reset_option import ResetOption
from resimulate.util.enum_action import EnumAction


def add_subparser(
    parent_parser: argparse._SubParsersAction,
) -> None:
    euicc_parser: argparse.ArgumentParser = parent_parser.add_parser(
        "euicc",
        formatter_class=RichHelpFormatter,
        help="EUICC operations on the euicc.",
    )
    euicc_subparser = euicc_parser.add_subparsers(dest="euicc_command", required=True)

    euicc_subparser.add_parser(
        "info",
        formatter_class=RichHelpFormatter,
        help="Retrieves the EUICCInfo2 object from the euicc.",
    )

    euicc_subparser.add_parser(
        "info-1",
        formatter_class=RichHelpFormatter,
        help="Retrieves the EUICCInfo1 object from the euicc.",
    )

    euicc_subparser.add_parser(
        "configured-data",
        formatter_class=RichHelpFormatter,
        help="Retrieves the ConfiguredData object from the euicc.",
    )

    euicc_subparser.add_parser(
        "eid",
        formatter_class=RichHelpFormatter,
        help="Retrieves the EID from the euicc.",
    )

    set_default_smdp_parser: argparse.ArgumentParser = euicc_subparser.add_parser(
        "set-default-smdp",
        formatter_class=RichHelpFormatter,
        help="Set the default SM-DP+ for the euicc.",
    )
    set_default_smdp_parser.add_argument(
        "-s",
        "--smdp",
        required=True,
        type=str,
        help="SM-DP+ address (e.g. 'smdp.example.com')",
    )

    reset_euicc_memory_parser: argparse.ArgumentParser = euicc_subparser.add_parser(
        "reset",
        formatter_class=RichHelpFormatter,
        help="Reset the EUICC memory.",
    )
    reset_euicc_memory_parser.add_argument(
        "-o",
        "--option",
        required=False,
        type=ResetOption,
        action=EnumAction,
        help="Reset option",
    )
    reset_euicc_memory_parser.add_argument(
        "-a",
        "--all",
        action="store_true",
        default=False,
        help="Reset all options (overrides --options)",
    )


def run(args: argparse.Namespace, card: Card) -> None:
    if args.euicc_command == "info":
        print(card.isd_r.get_euicc_info_2())
    elif args.euicc_command == "info-1":
        print(card.isd_r.get_euicc_info_1())
    elif args.euicc_command == "configured-data":
        print(card.isd_r.get_configured_data())
    elif args.euicc_command == "eid":
        print(card.isd_r.get_eid())
    elif args.euicc_command == "set-default-smdp":
        card.isd_r.set_default_dp_address(address=args.smdp)
    elif args.euicc_command == "reset":
        if args.all:
            card.isd_r.reset_euicc_memory(reset_options=ResetOption.all())
        else:
            card.isd_r.reset_euicc_memory(reset_options=args.option)
    else:
        raise ValueError(f"Unknown euicc command: {args.euicc_command}")
