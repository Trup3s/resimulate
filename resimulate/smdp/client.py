import base64
import logging

import httpx
from osmocom.utils import b2h, h2b

from resimulate.asn import asn
from resimulate.euicc.models.notification import (
    OtherSignedNotification,
    ProfileInstallationResult,
)
from resimulate.smdp.exceptions import SmdpException
from resimulate.smdp.models import (
    AuthenticateClientResponse,
    GetBoundProfilePackageResponse,
    InitiateAuthenticationResponse,
)


class SmdpClient(httpx.Client):
    def __init__(self, smdp_address: str, verify_ssl: bool = True):
        self.smdp_address = smdp_address

        super().__init__(
            base_url=f"https://{smdp_address}",
            verify=verify_ssl,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "gsma-rsp-lpad",
                "X-Admin-Protocol": "gsma/rsp/v2.6.0",
            },
        )

    def initiate_authentication(
        self, euicc_challenge: str, euicc_info_1: str
    ) -> InitiateAuthenticationResponse:
        b64_euicc_challenge = base64.b64encode(h2b(euicc_challenge)).decode()
        b64_euicc_info_1 = base64.b64encode(
            asn.encode("EUICCInfo1", euicc_info_1)
        ).decode()

        response = self.post(
            url="/gsma/rsp2/es9plus/initiateAuthentication",
            json={
                "smdpAddress": self.smdp_address,
                "euiccChallenge": b64_euicc_challenge,
                "euiccInfo1": b64_euicc_info_1,
            },
        )
        if response.status_code != 200:
            raise SmdpException(
                f"Failed to initiate authentication: {response.status_code} - {response.text}"
            )

        authentication_response = InitiateAuthenticationResponse(**response.json())
        authentication_response.raise_on_error()

        logging.debug(
            f"Initiate Authentication response: {authentication_response.model_dump_json()}"
        )

        return authentication_response

    def authenticate_client(
        self, transaction_id: str, authenticate_server_response: str
    ) -> AuthenticateClientResponse:
        b64_authenticate_server = base64.b64encode(
            h2b(authenticate_server_response)
        ).decode()

        response = self.post(
            url="/gsma/rsp2/es9plus/authenticateClient",
            json={
                "transactionId": transaction_id,
                "authenticateServerResponse": b64_authenticate_server,
            },
        )
        if response.status_code != 200:
            raise SmdpException(
                f"Failed to authenticate client: {response.status_code} - {response.text}"
            )

        authentication_response = AuthenticateClientResponse(**response.json())
        authentication_response.raise_on_error()

        profile_metadata = asn.decode(
            "StoreMetadataRequest",
            authentication_response.profile_metadata,
            check_constraints=True,
        )
        logging.info(
            f"Loading profile {profile_metadata.get('profileName')} ({b2h(profile_metadata.get('iccid'))})"
        )

        return authentication_response

    def get_bound_profile_package(
        self,
        transaction_id: str,
        prepare_download_response: str,
    ) -> GetBoundProfilePackageResponse:
        b64_prepare_download_response = base64.b64encode(
            h2b(prepare_download_response)
        ).decode()

        response = self.post(
            url="gsma/rsp2/es9plus/getBoundProfilePackage",
            json={
                "transactionId": transaction_id,
                "prepareDownloadResponse": b64_prepare_download_response,
            },
        )
        if response.status_code != 200:
            raise SmdpClient(
                f"Failed to get bound profile package: {response.status_code} - {response.text}"
            )

        bpp_response = GetBoundProfilePackageResponse(**response.json())
        bpp_response.raise_on_error()

        return bpp_response

    def handle_notification(
        self, pending_notification: ProfileInstallationResult | OtherSignedNotification
    ) -> None:
        data = pending_notification.model_dump()
        if isinstance(pending_notification, ProfileInstallationResult):
            notification = {"profileInstallationResult": data}
        else:
            notification = {"otherSignedNotification": data}

        encoded_notification = asn.encode(
            "PendingNotification",
            notification,
            check_constraints=True,
        )
        b64_pending_notification = base64.b64encode(h2b(encoded_notification)).decode()

        response = self.post(
            url="/gsma/rsp2/es9plus/handleNotification",
            json={
                "pendingNotification": b64_pending_notification,
            },
        )
        if response.status_code != 200:
            raise SmdpException(
                f"Failed to handle notification: {response.status_code} - {response.text}"
            )

        logging.debug(f"Handled notification: {response.json()}")
