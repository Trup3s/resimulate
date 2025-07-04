import base64
import logging

import httpx

from resimulate.asn import asn
from resimulate.euicc.models.info import EuiccInfo1
from resimulate.euicc.models.notification import (
    LoadRpmPackageResultSigned,
    OtherSignedNotification,
    PendingNotification,
    ProfileInstallationResult,
)
from resimulate.smdp.exceptions import SmdpException
from resimulate.smdp.models import (
    AuthenticateClientResponse,
    GetBoundProfilePackageResponse,
    InitiateAuthenticationResponse,
)


class SmdpClient(httpx.Client):
    def __init__(
        self, smdp_address: str, verify_ssl: bool = True, protocol: str = "https"
    ) -> None:
        self.smdp_address = smdp_address
        print(f"Connecting to SMDP+ server at {smdp_address}")
        print(f"SSL verification is {'enabled' if verify_ssl else 'disabled'}")
        super().__init__(
            base_url=f"{protocol}://{smdp_address}",
            verify=verify_ssl,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "gsma-rsp-lpad",
                "X-Admin-Protocol": "gsma/rsp/v3.1.0",
            },
        )

    def initiate_authentication(
        self, euicc_challenge: str, euicc_info_1: EuiccInfo1
    ) -> InitiateAuthenticationResponse:
        b64_euicc_challenge = base64.b64encode(bytes.fromhex(euicc_challenge)).decode()
        b64_euicc_info_1 = base64.b64encode(
            asn.encode("EUICCInfo1", euicc_info_1.model_dump(exclude_none=True))
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
            bytes.fromhex(authenticate_server_response)
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
            f"Loading profile {profile_metadata.get('profileName')} ({profile_metadata.get('iccid').hex()})"
        )

        return authentication_response

    def get_bound_profile_package(
        self,
        transaction_id: str,
        prepare_download_response: str,
    ) -> GetBoundProfilePackageResponse:
        b64_prepare_download_response = base64.b64encode(
            bytes.fromhex(prepare_download_response)
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
        self,
        pending_notification: PendingNotification,
    ) -> None:
        data = pending_notification.model_dump(by_alias=True, exclude_none=True)
        seq_number = None
        if isinstance(pending_notification, ProfileInstallationResult):
            notification = ("profileInstallationResult", data)
            seq_number = pending_notification.data.notification.seq_number
        elif isinstance(pending_notification, OtherSignedNotification):
            notification = ("otherSignedNotification", data)
            seq_number = pending_notification.tbs_other_notification.seq_number
        elif isinstance(pending_notification, LoadRpmPackageResultSigned):
            notification = ("loadRpmPackageResultDataSigned", data)
            seq_number = pending_notification.load_rpm_package_result_data_signed.notification.seq_number
        else:
            raise SmdpException(
                f"Unsupported notification type: {type(pending_notification)}"
            )

        encoded_notification = asn.encode(
            "PendingNotification",
            notification,
            check_constraints=True,
        )
        b64_pending_notification = base64.b64encode(encoded_notification).decode()

        response = self.post(
            url="/gsma/rsp2/es9plus/handleNotification",
            json={
                "pendingNotification": b64_pending_notification,
            },
        )
        if response.status_code != 204:
            raise SmdpException(
                f"Failed to handle notification: {response.status_code} - {response.text}"
            )

        logging.debug(f"Handled notification with sequence number {seq_number}")
