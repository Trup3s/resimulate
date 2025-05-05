import argparse

from rich import print

from resimulate.euicc.card import Card
from resimulate.euicc.models.notification import NotificationType


def add_subparser(
    parent_parser: argparse._SubParsersAction,
) -> None:
    notification_parser: argparse.ArgumentParser = parent_parser.add_parser(
        "notification",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        help="Notification operations on the euicc.",
    )
    notification_subparser = notification_parser.add_subparsers(
        dest="notification_command", required=True
    )

    list_parser: argparse.ArgumentParser = notification_subparser.add_parser(
        "list",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        help="List all notifications on the euicc.",
    )
    list_parser.add_argument(
        "-t",
        "--type",
        required=False,
        type=NotificationType,
        choices=list(NotificationType),
        help="Filter by notification type (e.g. '1' or '2')",
    )
    list_parser.add_argument(
        "-n",
        "--sequence-number",
        required=False,
        type=int,
        help="Filter by sequence number (e.g. '1' or '2')",
    )

    process_parser: argparse.ArgumentParser = notification_subparser.add_parser(
        "process",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        help="Process a notification on the euicc.",
    )
    process_parser.add_argument(
        "-n",
        "--sequence-numbers",
        type=int,
        nargs="+",
        help="Sequence numbers of the notifications to process (e.g. '1 2')",
    )
    process_parser.add_argument(
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
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        help="Remove a notification on the euicc.",
    )
    remove_parser.add_argument(
        "-n",
        "--sequence-numbers",
        nargs="+",
        type=int,
        help="Sequence numbers of the notifications to remove (e.g. '1 2')",
    )
    remove_parser.add_argument(
        "-a",
        "--all",
        action="store_true",
        default=False,
        help="Remove all notifications (overrides --sequence-numbers)",
    )


def run(args: argparse.Namespace, card: Card) -> None:
    if args.notification_command == "list":
        if args.type and args.sequence_number:
            raise ValueError(
                "Cannot specify both --type and --sequence-number at the same time."
            )

        print(
            card.isd_r.retrieve_notification_list(
                seq_number=args.sequence_number, notification_type=args.type
            )
        )
    elif args.notification_command == "process":
        notifications = card.isd_r.get_notifications()
        if args.all:
            card.isd_r.process_notifications(
                notifications=notifications, remove=args.remove
            )
        elif args.sequence_numbers:
            relevant_notifications = [
                notification
                for notification in notifications
                if notification.seq_number in args.sequence_numbers
            ]

            card.isd_r.process_notifications(
                notifications=relevant_notifications, remove=args.remove
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
                card.isd_r.remove_notification(seq_number=args.sequence_number)
        else:
            raise ValueError(
                "Must specify either --all or --sequence-number to remove notifications."
            )
