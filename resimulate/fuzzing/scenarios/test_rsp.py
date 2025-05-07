import logging
import unittest

from hypothesis import given
from hypothesis import strategies as st

from resimulate.euicc.card import Card
from resimulate.euicc.exceptions import EuiccException, UndefinedError
from resimulate.euicc.transport.pcsc_link import PcscLink
from resimulate.smdp.models import (
    AuthenticateClientResponse,
    FunctionExecutionStatus,
    GetBoundProfilePackageResponse,
    Header,
    InitiateAuthenticationResponse,
)

status_strategy = st.sampled_from(["Executed-Success", "Failed"])
status_code_data_strategy = (
    st.dictionaries(
        st.text(min_size=1, max_size=5), st.text(min_size=1, max_size=10), max_size=3
    )
    | st.none()
)

function_execution_status_strategy = st.builds(
    FunctionExecutionStatus,
    status=status_strategy,
    status_code_data=status_code_data_strategy,
)

header_strategy = st.builds(
    Header, function_execution_status=function_execution_status_strategy
)


class TestRsp(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.link = PcscLink()
        cls.link.connect()
        cls.card = Card(cls.link)

    @classmethod
    def tearDownClass(cls):
        cls.link.disconnect()

    @given(
        authenticate_client_response=st.builds(
            AuthenticateClientResponse,
            header=header_strategy,
            transaction_id=st.text(min_size=0, max_size=256),
            profile_metadata=st.binary(min_size=0, max_size=64),
            smdp_signed_2=st.binary(min_size=0, max_size=64),
            smdp_signature_2=st.binary(min_size=0, max_size=64),
            smdp_certificate=st.binary(min_size=0, max_size=64),
        ),
        confirmation_code=st.text(min_size=0, max_size=256),
    )
    def test_prepare_download(
        self,
        authenticate_client_response: AuthenticateClientResponse,
        confirmation_code: str | None,
    ):
        try:
            self.card.isd_r.prepare_download(
                authenticate_client_response=authenticate_client_response,
                confirmation_code=confirmation_code,
            )
        except UndefinedError:
            logging.info(
                f"Found interesting input: authenticate_client_response={authenticate_client_response}, confirmation_code={confirmation_code}"
            )
            return
        except (EuiccException, TypeError):
            return

    @given(
        initiate_authentication_response=st.builds(
            InitiateAuthenticationResponse,
            header=header_strategy,
            transaction_id=st.text(min_size=0, max_size=256) | st.none(),
            server_signed_1=st.binary(min_size=0, max_size=64) | st.none(),
            server_signature_1=st.binary(min_size=0, max_size=64) | st.none(),
            euicc_ci_pki_to_be_used=st.binary(min_size=0, max_size=64) | st.none(),
            server_certificate=st.binary(min_size=0, max_size=64) | st.none(),
        ),
        matching_id=st.text(min_size=0, max_size=256) | st.none(),
        imei=st.text(min_size=0, max_size=256) | st.none(),
    )
    def test_authenticate_server(
        self,
        initiate_authentication_response: AuthenticateClientResponse,
        matching_id: str,
        imei: str | None,
    ):
        try:
            self.card.isd_r.authenticate_server(
                initiate_authentication_response=initiate_authentication_response,
                matching_id=matching_id,
                imei=imei,
            )
        except UndefinedError:
            logging.info(
                f"Found interesting input: initiate_authentication_response={initiate_authentication_response}"
            )
            return
        except (EuiccException, TypeError):
            return

    @given(
        get_bpp_response=st.builds(
            GetBoundProfilePackageResponse,
            header=header_strategy,
            transaction_id=st.text(min_size=0, max_size=256) | st.none(),
            bound_profile_package=st.binary(min_size=0, max_size=256) | st.none(),
        )
    )
    def test_load_bound_profile_package(
        self, get_bpp_response: GetBoundProfilePackageResponse
    ):
        try:
            self.card.isd_r.load_bound_profile_package(
                get_bpp_response=get_bpp_response
            )
        except UndefinedError:
            logging.info("Found interesting input: load_bound_profile_package")
            return
        except (EuiccException, TypeError):
            return
