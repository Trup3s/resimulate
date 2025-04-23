import logging
from hashlib import sha256

from osmocom.utils import b2h, h2b

from resimulate.asn import asn
from resimulate.euicc.applications import Application
from resimulate.euicc.exceptions import (
    NotificationException,
    ProfileInstallationException,
    ProfileInteractionException,
)
from resimulate.euicc.models import ActivationProfile
from resimulate.euicc.models.notification import (
    Notification,
    NotificationType,
    OtherSignedNotification,
    ProfileInstallationResult,
)
from resimulate.euicc.models.profile_info import Profile, ProfileClass
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
            "GetEuiccChallengeRequest",
            "GetEuiccChallengeResponse",
        )
        return b2h(euicc_challenge.get("euiccChallenge"))

    def get_euicc_info_1(self) -> dict:
        command = self.store_data("GetEuiccInfo1Request", "EUICCInfo1")
        return command

    def get_euicc_info_2(self) -> dict:
        command = self.store_data("GetEuiccInfo2Request", "EUICCInfo2")
        return command

    def get_configured_addresses(self) -> dict:
        command = self.store_data(
            "EuiccConfiguredAddressesRequest",
            "EuiccConfiguredAddressesResponse",
        )
        return command

    def get_eid(self) -> str:
        command = {"tagList": h2b("5A")}
        eid_data = self.store_data(
            "GetEuiccDataRequest", "GetEuiccDataResponse", command
        )
        return b2h(eid_data.get("eidValue"))

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
            "serverSigned1": authentication.server_signed_1,
            "serverSignature1": authentication.server_signature_1,
            "euiccCiPKIdToBeUsed": authentication.euicc_ci_pki_to_be_used,
            "serverCertificate": authentication.server_certificate,
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
        smdp_signed_2 = authenticate_client_response.smdp_signed_2
        smdp_signed_2_decoded = asn.decode("SmdpSigned2", smdp_signed_2)
        cc_required_flag = smdp_signed_2_decoded.get("ccRequiredFlag")

        if cc_required_flag and not confirmation_code:
            raise ValueError(
                "Confirmation code is required by the profile but not provided."
            )

        command = {
            "smdpSigned2": smdp_signed_2,
            "smdpSignature2": authenticate_client_response.smdp_signature_2,
            "smdpCertificate": authenticate_client_response.smdp_certificate,
        }
        if confirmation_code:
            command["confirmationCode"] = sha256(confirmation_code.encode()).hexdigest()

        data = self.store_data(
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
        bound_profile_package: dict = asn.decode(
            "BoundProfilePackage",
            get_bpp_response.bound_profile_package,
            check_constraints=True,
        )
        logging.debug(f"BoundProfilePackage: {bound_profile_package}")

        def send_and_check(
            data, label: str | None = None, request_type: str | None = None
        ) -> dict | None:
            if label:
                logging.debug(
                    f"Sending {label}: {b2h(data) if isinstance(data, bytes) else data}"
                )

            result = self.store_data(
                caller_func_name="label",
                request_type=request_type,
                response_type="ProfileInstallationResult",
                request_data=data,
            )

            if result:
                result_type, data = result.get("profileInstallationResultData", {}).get(
                    "finalResult", (None, None)
                )
                if result_type == "errorResult":
                    ProfileInstallationException.raise_from_result(data)
            return result

        # TODO: Move functions to isd-p

        # Step 1: initialise secure channel
        send_and_check(
            {
                "initialiseSecureChannelRequest": bound_profile_package.get(
                    "initialiseSecureChannelRequest"
                )
            },
            "initialiseSecureChannelRequest",
            "BoundProfilePackage",
        )

        # Step 2: Configure ISDP
        first_sequence_of_87 = bound_profile_package.get("firstSequenceOf87")
        for index, sequence in enumerate(first_sequence_of_87):
            send_and_check(
                sequence,
                f"firstSequenceOf87_{index + 1}",
            )

        # Step 3: Store Metadata
        sequence_of_88 = bound_profile_package.get("sequenceOf88")
        for index, sequence in enumerate(sequence_of_88):
            send_and_check(sequence, f"sequenceOf88_{index + 1}")

        # Step 4: Replace Session Keys (optional)
        if second_sequence := bound_profile_package.get("secondSequenceOf87"):
            for sequence in second_sequence:
                send_and_check(
                    sequence,
                    f"secondSequenceOf87_{index + 1}",
                )

        # Step 5: load profile elements
        sequence_of_86 = bound_profile_package.get("sequenceOf86")
        final_result = None
        for index, sequence in enumerate(sequence_of_86):
            final_result = send_and_check(sequence, f"sequenceOf86_{index + 1}")

        return final_result.get("profileInstallationResultData", {}).get(
            "notificationMetadata"
        )

    def enable_profile(
        self, iccid: str | None = None, isdp_aid: str | None = None
    ) -> bool:
        profile_identifier = {}
        if iccid:
            profile_identifier = ("iccid", h2b(iccid))

        if isdp_aid:
            profile_identifier = ("isdpAid", h2b(isdp_aid))

        response = self.store_data(
            "EnableProfileRequest",
            "EnableProfileResponse",
            {"profileIdentifier": profile_identifier, "refreshFlag": True},
        )
        logging.debug(f"EnableProfileResponse: {response}")

        if response["enableResult"] != 0:
            ProfileInteractionException.raise_from_result(response["enableResult"])

        return True

    def disable_profile(
        self, iccid: str | None = None, isdp_aid: str | None = None
    ) -> bool:
        profile_identifier = None
        if iccid:
            profile_identifier = ("iccid", h2b(iccid))

        if isdp_aid:
            profile_identifier = ("isdpAid", h2b(isdp_aid))

        response = self.store_data(
            "DisableProfileRequest",
            "DisableProfileResponse",
            {"profileIdentifier": profile_identifier, "refreshFlag": True},
        )
        logging.debug(f"DisableProfileResponse: {response}")

        if response["disableResult"] != 0:
            ProfileInteractionException.raise_from_result(response["disableResult"])

        return True

    def delete_profile(
        self, iccid: str | None = None, isdp_aid: str | None = None
    ) -> bool:
        profile_identifier = {}
        if iccid:
            profile_identifier = ("iccid", h2b(iccid))

        if isdp_aid:
            profile_identifier = ("isdpAid", h2b(isdp_aid))

        response = self.store_data(
            "DeleteProfileRequest",
            "DeleteProfileResponse",
            {"profileIdentifier": profile_identifier},
        )
        logging.debug(f"DeleteProfileResponse: {response}")

        if response["deleteResult"] != 0:
            ProfileInteractionException.raise_from_result(response["deleteResult"])

        return True

    def list_profiles(
        self,
        isdp_aid: str | None = None,
        iccid: str | None = None,
        profile_class: ProfileClass | None = None,
        tags: list[str] | None = None,
    ) -> list[Profile]:
        search_criteria = {}
        if isdp_aid:
            if len(isdp_aid) <= 16:
                raise ValueError("IDP AID must be at least 16 characters long.")

            search_criteria["isdpAid"] = isdp_aid

        if iccid:
            if len(iccid) != 10:
                raise ValueError("ICCID must be 10 digits long.")

            search_criteria["iccid"] = iccid

        if profile_class:
            search_criteria["profileClass"] = profile_class.value

        if tags:
            # TODO: Check how properly send tags
            search_criteria["tags"] = tags

        response = self.store_data(
            "ProfileInfoListRequest",
            "ProfileInfoListResponse",
        )

        logging.debug(f"ListProfilesResponse: {response}")

        key, data = response
        if key == "profileInfoListError":
            message = "Incorrect input values" if data == 1 else "Unknown error"
            raise NotificationException(message)

        return [Profile(**profile) for profile in data]

    def list_notifications(
        self, notification_type: NotificationType | None = None
    ) -> list[Notification]:
        filter = None
        if notification_type:
            filter = ("profileManagementOperation", notification_type.value)

        response = self.store_data(
            "ListNotificationRequest",
            "ListNotificationResponse",
            filter,
        )
        logging.debug(f"ListNotificationsResponse: {response}")

        key, data = response
        if key == "notificationError":
            raise NotificationException.raise_from_result(data)

        return [Notification(**notification) for notification in data]

    def retrieve_notification_list(
        self,
        seq_number: int | None = None,
        notification_type: NotificationType | None = None,
    ) -> list[ProfileInstallationResult | OtherSignedNotification]:
        search_criteria = None
        if seq_number:
            search_criteria = {"searchCriteria": ("seqNumber", seq_number)}

        if notification_type:
            search_criteria = {
                "searchCriteria": (
                    "profileManagementOperation",
                    notification_type.value,
                )
            }

        response = self.store_data(
            "RetrieveNotificationsListRequest",
            "RetrieveNotificationsListResponse",
            search_criteria,
        )
        logging.debug(f"RetrieveNotificationsListResponse: {response}")

        key, data = response
        if key == "notificationsListResultError":
            raise ProfileInteractionException.raise_from_result(data)

        notifications = []
        for key, notification in data:
            if key == "profileInstallationResult":
                notifications.append(
                    ProfileInstallationResult(**notification, raw_data=notification)
                )
            elif key == "otherSignedNotification":
                notifications.append(
                    OtherSignedNotification(**notification, raw_data=notification)
                )

        return notifications

    def download_profile(self, profile: ActivationProfile) -> dict:
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
