import base64
import logging

from resimulate.euicc.applications import Application
from resimulate.euicc.es import es9p
from resimulate.euicc.es.models.authenticate_server import (
    AuthenticateServerRequest,
    AuthenticateServerResponse,
)
from resimulate.euicc.es.models.initiate_authentication import (
    InitiateAuthenticationResponse,
)
from resimulate.euicc.models import (
    EuiccConfiguredAddresses,
    EuiccInfo1,
    EuiccInfo2,
    GetEuiccChallenge,
    GetEuiccData,
    Profile,
    TagList,
)


class ISDR(Application):
    aid = "A0000005591010FFFFFFFF8900000100"
    name = "ISDR"
    alternative_aids = [
        "A0000005591010FFFFFFFF8900050500",  # 5Ber.esim
    ]

    def get_euicc_challenge(self) -> str:
        euicc_challenge = self.store_data_tlv(
            "get_euicc_challenge", GetEuiccChallenge()
        )
        return euicc_challenge.to_dict().get("get_euicc_challenge")[0][
            "euicc_challenge"
        ]

    def get_euicc_info_1(self) -> dict:
        command = self.store_data_tlv("get_euicc_info_1", EuiccInfo1())
        euicc_info = command.to_dict().get("euicc_info1")
        return self._merge_dicts(euicc_info)

    def get_euicc_info_1_raw(self) -> str:
        command = self.store_data_tlv("get_euicc_info_1_raw", EuiccInfo1())
        euicc_info = base64.b64encode(command.to_tlv()).decode()
        return euicc_info

    def get_euicc_info_2(self) -> dict:
        command = self.store_data_tlv("get_euicc_info_2", EuiccInfo2())
        euicc_info = command.to_dict().get("euicc_info2")
        return self._merge_dicts(euicc_info)

    def get_configured_addresses(self) -> str:
        command = self.store_data_tlv(
            "get_configured_addresses", EuiccConfiguredAddresses()
        )
        addresses = command.to_dict().get("euicc_configured_addresses")
        return self._merge_dicts(addresses)

    def get_eid(self) -> str:
        command = GetEuiccData(children=[TagList(decoded=[0x5A])])
        eid_data = self.store_data_tlv("get_eid", command, GetEuiccData())
        return eid_data.to_dict().get("get_euicc_data")[0]["eid_value"]

    def authenticate_server(
        self,
        authentication: InitiateAuthenticationResponse,
        matching_id: str,
        imei: str | None = None,
    ) -> AuthenticateServerResponse:
        request = AuthenticateServerRequest.build(
            matching_id,
            base64.b64decode(authentication.server_signed_1),
            base64.b64decode(authentication.server_signature_1),
            base64.b64decode(authentication.euicc_ci_pki_to_be_used),
            base64.b64decode(authentication.server_certificate),
            imei,
        )

        logging.debug(f"AuthenticateServerRequest: {request}")

        response = self.store_data_tlv(
            "authenticate_server",
            request,
            AuthenticateServerResponse(),
        )

        logging.debug(f"AuthenticateServerResponse: {response}")

        if error := response.to_dict().get("authenticate_response_error"):
            message = error[1].get("authenticate_error_code")
            raise Exception(f"AuthenticateServerResponseError: {message}")

        return response

    def download_profile(self, profile: Profile):
        smdpp_address = profile.smdpp_address
        if not smdpp_address:
            smdpp_address = self.get_configured_addresses().get("smdpp_address")

        logging.debug(f"Downloading profile from {smdpp_address}")
        euicc_challenge = self.get_euicc_challenge()
        euicc_info_1 = self.get_euicc_info_1_raw()

        init_auth = es9p.initiate_authentication(
            smdpp_address, euicc_challenge, euicc_info_1
        )
        transaction_id = init_auth.transaction_id

        authenticate_server = self.authenticate_server(init_auth, profile.matching_id)

        es9p.authenticate_client(smdpp_address, transaction_id, authenticate_server)
