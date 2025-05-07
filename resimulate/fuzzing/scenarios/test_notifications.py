import logging
import unittest

from hypothesis import given
from hypothesis import strategies as st

from resimulate.euicc.card import Card
from resimulate.euicc.exceptions import EuiccException, UndefinedError
from resimulate.euicc.models.activation_profile import ActivationProfile
from resimulate.euicc.models.reset_option import ResetOption
from resimulate.euicc.transport.pcsc_link import PcscLink


class TestNotifications(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.link = PcscLink()
        cls.link.connect()
        cls.card = Card(cls.link)
        profile = ActivationProfile.from_activation_code(
            "LPA:1$rsp.truphone.com$QR-G-5C-1LS-1W1Z9P7"
        )
        pending_notification = cls.card.isd_r.download_profile(profile)
        cls.notification = pending_notification.get_notification()

    @classmethod
    def tearDownClass(cls):
        cls.card.isd_r.reset_euicc_memory(reset_options=ResetOption.all())
        notifications = cls.card.isd_r.retrieve_notification_list()
        cls.card.isd_r.process_notifications(notifications, remove=True)
        cls.link.disconnect()

    @given(
        seq_number=st.one_of(st.integers(min_value=-1000, max_value=100000), st.none()),
        notification_type=st.one_of(
            st.integers(min_value=0, max_value=1000), st.none()
        ),
    )
    def test_retrieve_notifications(self, seq_number: int, notification_type: int):
        try:
            pending_notifications = self.card.isd_r.retrieve_notification_list(
                seq_number=seq_number, notification_type=notification_type
            )
        except UndefinedError:
            logging.info(
                f"Found interesting input: notification_type={notification_type}"
            )
            return
        except EuiccException:
            return

        if not pending_notifications:
            if (
                seq_number is not None
                and notification_type is None
                and seq_number != self.notification.seq_number
            ):
                self.assertFalse(pending_notifications)
            return

        self.assertEqual(len(pending_notifications), 1)
        notification = pending_notifications[0].get_notification()

        self.assertEqual(self.notification.seq_number, notification.seq_number)
        if seq_number is not None and notification_type is None:
            self.assertEqual(seq_number, notification.seq_number)

        self.assertEqual(self.notification.iccid, notification.iccid)

    @given(
        notification_type=st.one_of(st.integers(min_value=0, max_value=1000), st.none())
    )
    def test_get_notifications(self, notification_type: int | None):
        try:
            notifications = self.card.isd_r.get_notifications(
                notification_type=notification_type
            )
        except UndefinedError:
            logging.info(
                f"Found interesting input: notification_type={notification_type}"
            )
            return
        except EuiccException:
            return

        if not notifications:
            self.assertTrue(notification_type is not None)
            return

        self.assertEqual(len(notifications), 1)
        notification = notifications[0]

        self.assertEqual(self.notification.seq_number, notification.seq_number)
        self.assertEqual(self.notification.iccid, notification.iccid)
