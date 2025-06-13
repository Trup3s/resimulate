import logging
import string
import unittest

from hypothesis import given
from hypothesis import strategies as st

from resimulate.euicc.card import Card
from resimulate.euicc.exceptions import (
    EuiccException,
    IccidAlreadyExists,
    UndefinedError,
)
from resimulate.euicc.models.activation_profile import ActivationProfile
from resimulate.euicc.models.reset_option import ResetOption
from resimulate.euicc.transport.pcsc_link import PcscLink


class FuzzProfiles(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.link = PcscLink()
        cls.link.connect()
        cls.card = Card(cls.link)
        profile = ActivationProfile.from_activation_code(
            "LPA:1$rsp.truphone.com$QR-G-5C-1LS-1W1Z9P7"
        )
        try:
            pending_notification = cls.card.isd_r.download_profile(profile)
            notification = pending_notification.get_notification()
            cls.iccid = notification.iccid
        except IccidAlreadyExists:
            logging.info(
                "Profile with ICCID already exists, using existing profile instead."
            )
            profiles = cls.card.isd_r.get_profiles()
            cls.iccid = profiles[-1].iccid if profiles else None

    @classmethod
    def tearDownClass(cls):
        cls.card.isd_r.reset_euicc_memory(reset_options=ResetOption.all())
        notifications = cls.card.isd_r.retrieve_notification_list()
        cls.card.isd_r.process_notifications(notifications, remove=True)
        cls.link.disconnect()

    @given(
        use_iccid=st.booleans(),
        profile_class=st.one_of(st.integers(min_value=-20, max_value=20), st.none()),
        tags=st.one_of(
            st.lists(
                st.text(
                    min_size=2,
                    max_size=8,
                    alphabet=string.hexdigits,
                ).filter(lambda s: len(s) % 2 == 0),
                min_size=1,
                max_size=5,
            ),
            st.binary(max_size=8),
        ),
    )
    def test_get_profiles(
        self,
        use_iccid: bool,
        profile_class: str | None,
        tags: list[str] | bytes | None,
    ):
        iccid = self.iccid if use_iccid else None
        try:
            profiles = self.card.isd_r.get_profiles(
                iccid=iccid,
                profile_class=profile_class,
                tags=tags,
            )
        except UndefinedError:
            logging.info(
                f"Found interesting input: profile_class={profile_class}, tags={tags}, iccid={iccid}"
            )
            return
        except EuiccException:
            return

        if not profiles:
            return

        profile = profiles[-1]
        if profile.iccid:
            self.assertEqual(
                profile.iccid,
                self.iccid,
            )

    @given(
        iccid=st.text(min_size=0, max_size=20, alphabet=string.hexdigits).filter(
            lambda s: len(s) % 2 == 0
        ),
        nickname=st.text(min_size=1, max_size=300),
    )
    def test_set_nickname(self, iccid: str, nickname: str):
        iccid = self.iccid if iccid is None else iccid
        try:
            self.card.isd_r.set_nickname(iccid=iccid, nickname=nickname)
        except UndefinedError:
            logging.info(f"Found interesting input: iccid={iccid}, nickname={nickname}")
            return
        except EuiccException:
            return
