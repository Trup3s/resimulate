import argparse

from rich import print
from rich_argparse import RichHelpFormatter

from resimulate.euicc.card import Card
from resimulate.euicc.models.notification import NotificationType
from resimulate.util.enum_action import EnumAction


def add_subparser(
    parent_parser: argparse._SubParsersAction,
) -> None:
    notification_parser: argparse.ArgumentParser = parent_parser.add_parser(
        "notification",
        formatter_class=RichHelpFormatter,
        help="Notification operations on the euicc.",
    )
    notification_subparser = notification_parser.add_subparsers(
        dest="notification_command", required=True
    )

    list_parser: argparse.ArgumentParser = notification_subparser.add_parser(
        "list",
        formatter_class=RichHelpFormatter,
        help="List all notifications on the euicc.",
    )
    list_parser.add_argument(
        "-t",
        "--type",
        required=False,
        type=NotificationType,
        action=EnumAction,
        help="Filter by notification type",
    )

    process_parser: argparse.ArgumentParser = notification_subparser.add_parser(
        "process",
        formatter_class=RichHelpFormatter,
        help="Process a notification on the euicc.",
    )
    process_group = process_parser.add_mutually_exclusive_group(required=True)
    process_group.add_argument(
        "-n",
        "--sequence-numbers",
        type=int,
        nargs="+",
        help="Sequence numbers of the notifications to process (e.g. '1 2')",
    )
    process_group.add_argument(
        "-a",
        "--all",
        action="store_true",
        default=False,
        help="Process all notifications (overrides --sequence-numbers)",
    )
    process_parser.add_argument(
        "-r",
        "--remove",
        action="store_true",
        default=False,
        help="Remove the notification after processing",
    )

    remove_parser: argparse.ArgumentParser = notification_subparser.add_parser(
        "remove",
        formatter_class=RichHelpFormatter,
        help="Remove a notification on the euicc.",
    )
    remove_group = remove_parser.add_mutually_exclusive_group(required=True)
    remove_group.add_argument(
        "-n",
        "--sequence-numbers",
        nargs="+",
        type=int,
        help="Sequence numbers of the notifications to remove (e.g. '1 2')",
    )
    remove_group.add_argument(
        "-a",
        "--all",
        action="store_true",
        default=False,
        help="Remove all notifications (overrides --sequence-numbers)",
    )


def run(args: argparse.Namespace, card: Card) -> None:
    if args.notification_command == "list":
        print(card.isd_r.get_notifications(notification_type=args.type))
    elif args.notification_command == "process":
        pending_notifications = card.isd_r.retrieve_notification_list()
        if args.all:
            card.isd_r.process_notifications(
                pending_notifications=pending_notifications, remove=args.remove
            )
        elif args.sequence_numbers:
            relevant_notifications = [
                pending_notification
                for pending_notification in pending_notifications
                if pending_notification.get_notification().seq_number
                in args.sequence_numbers
            ]

            card.isd_r.process_notifications(
                pending_notifications=relevant_notifications, remove=args.remove
            )
        else:
            raise ValueError(
                "Must specify either --all or --sequence-numbers to process notifications."
            )
    elif args.notification_command == "remove":
        if args.all:
            notifications = card.isd_r.get_notifications()
            for notification in notifications:
                card.isd_r.remove_notification(seq_number=notification.seq_number)
        elif args.sequence_numbers:
            for seq_number in args.sequence_numbers:
                card.isd_r.remove_notification(seq_number=seq_number)
        else:
            raise ValueError(
                "Must specify either --all or --sequence-number to remove notifications."
            )
