import base64
import logging
from hashlib import sha256

from osmocom.utils import b2h, h2b

from resimulate.asn import asn
from resimulate.euicc.applications import Application
from resimulate.euicc.exceptions import ProfileInstallationException
from resimulate.euicc.models import Profile
from resimulate.smdp.client import SmdpClient
from resimulate.smdp.models import (
    AuthenticateClientResponse,
    GetBoundProfilePackageResponse,
    InitiateAuthenticationResponse,
)


class ISDR(Application):
    aid = "A0000005591010FFFFFFFF8900000100"
    name = "ISDR"
    alternative_aids = [
        "A0000005591010FFFFFFFF8900050500",  # 5Ber.esim
    ]

    def get_euicc_challenge(self) -> str:
        euicc_challenge = self.store_data(
            "get_euicc_challenge",
            "GetEuiccChallengeRequest",
            "GetEuiccChallengeResponse",
        )
        return b2h(euicc_challenge.get("euiccChallenge"))

    def get_euicc_info_1(self) -> dict:
        command = self.store_data(
            "get_euicc_info_1", "GetEuiccInfo1Request", "EUICCInfo1"
        )
        return command

    def get_euicc_info_2(self) -> dict:
        command = self.store_data(
            "get_euicc_info_2", "GetEuiccInfo2Request", "EUICCInfo2"
        )
        return command

    def get_configured_addresses(self) -> dict:
        command = self.store_data(
            "get_configured_addresses",
            "EuiccConfiguredAddressesRequest",
            "EuiccConfiguredAddressesResponse",
        )
        return command

    def get_eid(self) -> str:
        command = {"tagList": h2b("5A")}
        eid_data = self.store_data(
            "get_eid", "GetEuiccDataRequest", "GetEuiccDataResponse", command
        )
        return eid_data.get("eidValue")

    def authenticate_server(
        self,
        authentication: InitiateAuthenticationResponse,
        matching_id: str,
        imei: str | None = None,
    ) -> dict:
        device_info = {"tac": h2b("35290611"), "deviceCapabilities": dict()}
        if imei:
            device_info["imei"] = imei

        request = {
            "serverSigned1": base64.b64decode(authentication.server_signed_1),
            "serverSignature1": base64.b64decode(authentication.server_signature_1),
            "euiccCiPKIdToBeUsed": base64.b64decode(
                authentication.euicc_ci_pki_to_be_used
            ),
            "serverCertificate": base64.b64decode(authentication.server_certificate),
            "ctxParams1": (
                "ctxParamsForCommonAuthentication",
                {
                    "matchingId": matching_id,
                    "deviceInfo": device_info,
                },
            ),
        }

        logging.debug(f"AuthenticateServerRequest: {request}")

        data = self.store_data(
            "authenticate_server",
            "AuthenticateServerRequest",
            request_data=request,
        )
        response = asn.decode(
            "AuthenticateServerResponse",
            h2b(data),
            check_constraints=True,
        )

        logging.debug(f"AuthenticateServerResponse: {response}")

        result, error = response
        if result == "authenticateResponseError":
            code = error.get("authenticateErrorCode")
            raise Exception(f"AuthenticateServerResponseErrorCode: {code}")

        return data

    def prepare_download(
        self,
        authenticate_client_response: AuthenticateClientResponse,
        confirmation_code: str | None = None,
    ) -> str:
        smdp_signed_2 = base64.b64decode(authenticate_client_response.smdp_signed_2)
        smdp_signed_2_decoded = asn.decode("SmdpSigned2", smdp_signed_2)
        cc_required_flag = smdp_signed_2_decoded.get("ccRequiredFlag")

        if cc_required_flag and not confirmation_code:
            raise ValueError(
                "Confirmation code is required by the profile but not provided."
            )

        command = {
            "smdpSigned2": smdp_signed_2,
            "smdpSignature2": base64.b64decode(
                authenticate_client_response.smdp_signature_2
            ),
            "smdpCertificate": base64.b64decode(
                authenticate_client_response.smdp_certificate
            ),
        }
        if confirmation_code:
            command["confirmationCode"] = sha256(confirmation_code.encode()).hexdigest()

        data = self.store_data(
            "prepare_download",
            request_type="PrepareDownloadRequest",
            request_data=command,
        )
        response = asn.decode(
            "PrepareDownloadResponse",
            h2b(data),
            check_constraints=True,
        )

        result, error = response
        if result == "prepareDownloadError":
            code = error.get("prepareDownloadErrorCode")
            raise Exception(f"PrepareDownloadResponseErrorCode: {code}")

        return data

    def load_bound_profile_package(
        self, get_bpp_response: GetBoundProfilePackageResponse
    ) -> dict:
        bpp = base64.b64decode(get_bpp_response.bound_profile_package)
        bpp_decoded: dict = asn.decode(
            "BoundProfilePackage",
            bpp,
            check_constraints=True,
        )
        logging.debug(f"BoundProfilePackage: {bpp_decoded}")

        def send_and_check(
            data, label: str | None = None, request_type: str | None = None
        ) -> dict | None:
            if label:
                logging.debug(
                    f"Sending {label}: {b2h(data) if isinstance(data, bytes) else data}"
                )

            result = self.store_data(
                "load_bound_profile_package",
                request_type=request_type,
                response_type="ProfileInstallationResult",
                request_data=data,
            )

            if result:
                result_type, data = result.get("profileInstallationResultData", {}).get(
                    "finalResult", (None, None)
                )
                if result_type == "errorResult":
                    raise ProfileInstallationException(data)
            return result

        # Step 1: initialise secure channel
        send_and_check(
            {
                "initialiseSecureChannelRequest": bpp_decoded.get(
                    "initialiseSecureChannelRequest"
                )
            },
            "initialiseSecureChannelRequest",
            "BoundProfilePackage",
        )

        # Step 2: Configure ISDP
        first_sequence_of_87 = bpp_decoded.get("firstSequenceOf87")
        for index, sequence in enumerate(first_sequence_of_87):
            send_and_check(
                sequence,
                f"firstSequenceOf87 part {index + 1} of {len(first_sequence_of_87)}",
            )

        # Step 3: Store Metadata
        sequence_of_88 = bpp_decoded.get("sequenceOf88")
        for index, sequence in enumerate(sequence_of_88):
            send_and_check(
                sequence, f"sequenceOf88 part {index} of {len(sequence_of_88)}"
            )

        # Step 4: Replace Session Keys (optional)
        if second_sequence := bpp_decoded.get("secondSequenceOf87"):
            for sequence in second_sequence:
                send_and_check(
                    sequence,
                    "secondSequenceOf87",
                    f"secondSequenceOf87 part {index + 1} of {len(sequence)}",
                )

        # Step 5: load profile elements
        sequence_of_86 = bpp_decoded.get("sequenceOf86")
        final_result = None
        for index, sequence in enumerate(sequence_of_86):
            final_result = send_and_check(
                sequence, f"sequenceOf86 part {index + 1} of {len(sequence_of_86)}"
            )

        return final_result.get("profileInstallationResultData", {}).get(
            "notificationMetadata"
        )

    def download_profile(self, profile: Profile) -> dict:
        smdp_address = profile.smdpp_address
        if not smdp_address:
            smdp_address = self.get_configured_addresses().get("defaultDpAddress")

        smdp_client = SmdpClient(smdp_address=smdp_address, verify_ssl=False)

        logging.debug(f"Downloading profile from {smdp_address}")
        euicc_challenge = self.get_euicc_challenge()
        euicc_info_1 = self.get_euicc_info_1()

        init_auth = smdp_client.initiate_authentication(euicc_challenge, euicc_info_1)
        transaction_id = init_auth.transaction_id

        authenticate_server = self.authenticate_server(init_auth, profile.matching_id)
        authenticate_client = smdp_client.authenticate_client(
            transaction_id, authenticate_server
        )
        prepare_download = self.prepare_download(
            authenticate_client, profile.confirmation_code
        )
        get_bpp_response = smdp_client.get_bound_profile_package(
            transaction_id,
            prepare_download,
        )
        notification = self.load_bound_profile_package(get_bpp_response)
        return notification
