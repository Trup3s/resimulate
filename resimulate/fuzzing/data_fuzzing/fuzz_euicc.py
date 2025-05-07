import logging
import unittest

from hypothesis import given
from hypothesis import strategies as st

from resimulate.euicc.card import Card
from resimulate.euicc.exceptions import EuiccException, UndefinedError
from resimulate.euicc.transport.pcsc_link import PcscLink


class FuzzEuicc(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.link = PcscLink()
        cls.link.connect()
        cls.card = Card(cls.link)

    @classmethod
    def tearDownClass(cls):
        cls.link.disconnect()

    @given(
        address=st.text(min_size=1, max_size=300),
    )
    def test_set_default_dp_address(self, address: str):
        try:
            self.card.isd_r.set_default_dp_address(address=address)
        except UndefinedError:
            logging.info(f"Found interesting input: address={address}")
            return
        except EuiccException:
            return

    @given(
        reset_options=st.lists(
            st.integers(
                min_value=0,
                max_value=64,
            ),
            min_size=0,
            max_size=64,
        ),
    )
    def test_reset_euicc_memory(self, reset_options: list[int]):
        try:
            self.card.isd_r.reset_euicc_memory(reset_options=reset_options)
        except UndefinedError:
            logging.info(f"Found interesting input: reset_euicc_memory={reset_options}")
            return
        except EuiccException:
            return
