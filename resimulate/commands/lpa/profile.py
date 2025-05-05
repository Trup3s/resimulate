import argparse

from rich import print
from rich_argparse import RichHelpFormatter

from resimulate.euicc.card import Card
from resimulate.euicc.models.profile import ProfileClass
from resimulate.util.enum_action import EnumAction


def add_subparser(
    parent_parser: argparse._SubParsersAction,
) -> None:
    profile_parser: argparse.ArgumentParser = parent_parser.add_parser(
        "profile",
        formatter_class=RichHelpFormatter,
        help="Profile operations on the euicc.",
    )
    profile_subparser = profile_parser.add_subparsers(
        dest="profile_command", required=True
    )

    list_parser: argparse.ArgumentParser = profile_subparser.add_parser(
        "list",
        formatter_class=RichHelpFormatter,
        help="List all profiles installed on the euicc.",
    )
    list_parser.add_argument(
        "-a",
        "--isdp-aid",
        required=False,
        type=str,
        help="Filter by ISDP AID (e.g. 'A0A4000002')",
    )
    list_parser.add_argument(
        "-i",
        "--iccid",
        required=False,
        type=str,
        help="Filter by ICCID (e.g. '89014103211118510720')",
    )
    list_parser.add_argument(
        "-c",
        "--profile-class",
        required=False,
        type=ProfileClass,
        action=EnumAction,
        help="Filter by profile class",
    )

    enable_parser: argparse.ArgumentParser = profile_subparser.add_parser(
        "enable",
        formatter_class=RichHelpFormatter,
        help="Enable a profile on the euicc.",
    )
    enable_parser.add_argument(
        "-a",
        "--isdp-aid",
        required=False,
        type=str,
        help="ISDP AID of the profile to enable (e.g. 'A0A4000002')",
    )
    enable_parser.add_argument(
        "-i",
        "--iccid",
        required=False,
        type=str,
        help="ICCID of the profile to enable (e.g. '89014103211118510720')",
    )
    enable_parser.add_argument(
        "--refresh",
        action="store_true",
        default=False,
        help="Sets the refresh flag. For more information: SGP.22 v3.1 [5.6.1]",
    )

    disable_parser: argparse.ArgumentParser = profile_subparser.add_parser(
        "disable",
        formatter_class=RichHelpFormatter,
        help="Disable a profile on the euicc.",
    )
    disable_parser.add_argument(
        "-a",
        "--isdp-aid",
        required=False,
        type=str,
        help="ISDP AID of the profile to disable (e.g. 'A0A4000002')",
    )
    disable_parser.add_argument(
        "-i",
        "--iccid",
        required=False,
        type=str,
        help="ICCID of the profile to disable (e.g. '89014103211118510720')",
    )
    disable_parser.add_argument(
        "--refresh",
        action="store_true",
        default=False,
        help="Sets the refresh flag. For more information: SGP.22 v3.1 [5.6.1]",
    )

    delete_parser: argparse.ArgumentParser = profile_subparser.add_parser(
        "delete",
        formatter_class=RichHelpFormatter,
        help="Delete a profile on the euicc.",
    )
    delete_parser.add_argument(
        "-i",
        "--iccid",
        required=False,
        type=str,
        help="ICCID of the profile to delete (e.g. '89014103211118510720')",
    )
    delete_parser.add_argument(
        "-a",
        "--isdp-aid",
        required=False,
        type=str,
        help="ISDP AID of the profile to delete (e.g. 'A0A4000002')",
    )

    nickname_parser: argparse.ArgumentParser = profile_subparser.add_parser(
        "nickname",
        formatter_class=RichHelpFormatter,
        help="Set the nickname of a profile on the euicc.",
    )

    nickname_parser.add_argument(
        "-i",
        "--iccid",
        required=True,
        type=str,
        help="ICCID of the profile to set the nickname (e.g. '89014103211118510720')",
    )
    nickname_parser.add_argument(
        "-n",
        "--nickname",
        required=True,
        type=str,
        help="Nickname of the profile to set (e.g. 'My Profile')",
    )

    download_parser: argparse.ArgumentParser = profile_subparser.add_parser(
        "download",
        formatter_class=RichHelpFormatter,
        help="Download a profile on the euicc.",
    )
    download_parser.add_argument(
        "-s",
        "--smdp-address",
        required=False,
        type=str,
        help="SMDP+ address of the profile to download (e.g. 'smdp.example.com')",
    )
    download_parser.add_argument(
        "-m",
        "--matching-id",
        required=False,
        type=str,
        help="Matching ID of the profile to download (e.g. 'A0A4000002')",
    )
    download_parser.add_argument(
        "-c",
        "--confirmation-code",
        required=False,
        type=str,
        help="Confirmation code of the profile to download (e.g. '12345678')",
    )
    download_parser.add_argument(
        "-a",
        "--activation-code",
        required=False,
        type=str,
        help="Activation code of the profile to download (e.g. 'LPA:1$smdp.example.com$12345678')",
    )


def run(args: argparse.Namespace, card: Card) -> None:
    if args.profile_command == "list":
        print(card.isd_r.get_profiles(args.isdp_aid, args.iccid, args.profile_class))
    elif args.profile_command == "enable":
        card.isd_r.enable_profile(args.iccid, args.isdp_aid, args.refresh)
    elif args.profile_command == "disable":
        card.isd_r.disable_profile(args.iccid, args.isdp_aid, args.refresh)
    elif args.profile_command == "delete":
        card.isd_r.delete_profile(args.iccid, args.isdp_aid)
    elif args.profile_command == "nickname":
        card.isd_r.set_profile_nickname(args.iccid, args.nickname)
    elif args.profile_command == "download":
        has_activation_profile_parts = (
            args.smdp_address is not None
            and args.matching_id is not None
            and args.confirmation_code is not None
        )

        if args.activation_code:
            card.isd_r.download_profile(args.activation_code)
        elif has_activation_profile_parts:
            card.isd_r.download_profile(
                args.smdp_address, args.matching_id, args.confirmation_code
            )
        else:
            raise ValueError(
                "Either activation code or SMDP address, matching ID, and confirmation code must be provided."
            )
    else:
        raise ValueError(f"Unknown profile command: {args.profile_command}")
