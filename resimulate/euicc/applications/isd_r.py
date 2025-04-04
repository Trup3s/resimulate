import base64
import logging

from resimulate.euicc.applications import Application
from resimulate.euicc.es import es9p
from resimulate.euicc.es.models.authenticate_server import (
    AuthenticateServerRequest,
    AuthenticateServerResponse,
    EuiccCiPKIdToBeUsed,
    ServerCertificate,
    ServerSignature1,
)
from resimulate.euicc.es.models.authenticate_client import AuthenticationClientResponse
from resimulate.euicc.es.models.ctx_params_1 import (
    CtxParams1,
    CtxParamsForCommonAuthentication,
    DeviceInfo,
    Imei,
    MatchingId,
)
from resimulate.euicc.es.models.server_signed_1 import ServerSigned1
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

    def get_euicc_challenge_raw(self) -> str:
        command = self.store_data_tlv(
            "get_euicc_challenge_raw",
            GetEuiccChallenge(),
        )
        euicc_challenge = base64.b64encode(command.to_tlv()).decode("utf-8")
        return euicc_challenge

    def get_euicc_info_1(self) -> dict:
        command = self.store_data_tlv("get_euicc_info_1", EuiccInfo1())
        euicc_info = command.to_dict().get("euicc_info1")
        return self._merge_dicts(euicc_info)

    def get_euicc_info_1_raw(self) -> str:
        command = self.store_data_tlv("get_euicc_info_1_raw", EuiccInfo1())
        euicc_info = base64.b64encode(command.to_tlv()).decode("utf-8")
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
        authentication: AuthenticationClientResponse,
        matching_id: str,
        imei: str | None = None,
    ) -> str:
        ctx_params_fca_children = [MatchingId(decoded=matching_id)]

        if imei:
            ctx_params_fca_children.append(DeviceInfo(children=[Imei(decoded=imei)]))

        server_signed_1, remainder = ServerSigned1().from_tlv(
            base64.b64decode(authentication.server_signed_1.encode())
        )
        server_signature_1, _ = ServerSignature1().from_tlv(
            base64.b64decode(authentication.server_signature_1.encode())
        )
        euicc_ci_pki_to_be_used, _ = EuiccCiPKIdToBeUsed().from_tlv(
            base64.b64decode(authentication.euicc_ci_pki_to_be_used.encode())
        )
        server_certificate, _ = ServerCertificate().from_tlv(
            base64.b64decode(authentication.server_certificate.encode())
        )
        print(f"Server signed 1: {server_signed_1}, remainder: {remainder}")

        request = AuthenticateServerRequest(
            children=[
                server_signed_1,
                server_signature_1,
                euicc_ci_pki_to_be_used,
                server_certificate,
                CtxParams1(
                    children=[
                        CtxParamsForCommonAuthentication(
                            children=ctx_params_fca_children
                        )
                    ]
                ),
            ]
        )

        authenticate_server_response = self.store_data_tlv(
            "authenticate_server",
            request,
            AuthenticateServerResponse(),
        )
        server_response = authenticate_server_response.to_dict().get(
            "authenticate_server_response"
        )
        return server_response

    def download_profile(self, profile: Profile):
        smdpp_address = profile.smdpp_address
        if not smdpp_address:
            smdpp_address = self.get_configured_addresses().get("smdpp_address")

        logging.info(f"Downloading profile from {smdpp_address}")
        euicc_challenge = self.get_euicc_challenge_raw()
        euicc_info_1 = self.get_euicc_info_1_raw()
        authentication_response = es9p.initiate_authentication(
            smdpp_address, euicc_challenge, euicc_info_1
        )
        self.authenticate_server(authentication_response, profile.matching_id)
