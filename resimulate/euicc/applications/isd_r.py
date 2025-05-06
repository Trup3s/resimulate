import logging
from hashlib import sha256

from resimulate.asn import asn
from resimulate.euicc.applications import Application
from resimulate.euicc.exceptions import (
    AuthenticateException,
    DownloadException,
    EuiccException,
    EuiccMemoryResetException,
    NotificationException,
    ProfileInstallationException,
    ProfileInteractionException,
)
from resimulate.euicc.models.activation_profile import ActivationProfile
from resimulate.euicc.models.configured_data import EuiccConfiguredData
from resimulate.euicc.models.info import EuiccInfo1, EuiccInfo2
from resimulate.euicc.models.notification import (
    LoadRpmPackageResultSigned,
    Notification,
    NotificationEvent,
    NotificationType,
    OtherSignedNotification,
    PendingNotification,
    ProfileInstallationResult,
)
from resimulate.euicc.models.profile import Profile, ProfileClass, ProfileInfoTag
from resimulate.euicc.models.reset_option import ResetOption, ResetOptionBitString
from resimulate.smdp.client import SmdpClient
from resimulate.smdp.models import (
    AuthenticateClientResponse,
    GetBoundProfilePackageResponse,
    InitiateAuthenticationResponse,
)
from resimulate.util import h2b, i2h


class ISDR(Application):
    aid = "A0000005591010FFFFFFFF8900000100"
    name = "ISDR"
    alternative_aids = [
        "A0000005591010FFFFFFFF8900050500",  # 5Ber.esim
        "A0000005591010FFFFFFFF8900000177",  # Xesim
        "A0000005591010000000008900000300",  # eSIM.me
    ]
    cla_byte = 0x80

    def get_euicc_challenge(self) -> str:
        euicc_challenge = self.store_data(
            "GetEuiccChallengeRequest",
            "GetEuiccChallengeResponse",
        )
        return euicc_challenge.get("euiccChallenge").hex()

    def get_euicc_info_1(self) -> EuiccInfo1:
        command = self.store_data("GetEuiccInfo1Request", "EUICCInfo1")
        if not command:
            raise EuiccException("Failed to retrieve EUICCInfo1")

        return EuiccInfo1(**command)

    def get_euicc_info_2(self) -> EuiccInfo2:
        command = self.store_data("GetEuiccInfo2Request", "EUICCInfo2")
        if not command:
            raise EuiccException("Failed to retrieve EUICCInfo2")

        return EuiccInfo2(**command)

    def get_configured_data(self) -> EuiccConfiguredData:
        command = self.store_data(
            "EuiccConfiguredDataRequest",
            "EuiccConfiguredDataResponse",
        )
        return EuiccConfiguredData(**command)

    def get_eid(self) -> str:
        command = {"tagList": bytes.fromhex("5A")}
        eid_data = self.store_data(
            "GetEuiccDataRequest", "GetEuiccDataResponse", command
        )
        return eid_data.get("eidValue").hex()

    def authenticate_server(
        self,
        authentication: InitiateAuthenticationResponse,
        matching_id: str,
        imei: str | None = None,
    ) -> dict:
        device_info = {"tac": bytes.fromhex("35290611"), "deviceCapabilities": dict()}
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
            bytes.fromhex(data),
            check_constraints=True,
        )

        logging.debug(f"AuthenticateServerResponse: {response}")

        result, error = response
        if result == "authenticateResponseError":
            code = error.get("authenticateErrorCode")
            raise AuthenticateException.raise_from_code(code)

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
            bytes.fromhex(data),
            check_constraints=True,
        )

        result, error = response
        if result == "downloadResponseError":
            code = error.get("downloadErrorCode")
            raise DownloadException.raise_from_code(code)

        return data

    def load_bound_profile_package(
        self, get_bpp_response: GetBoundProfilePackageResponse
    ) -> ProfileInstallationResult:
        bound_profile_package: dict = asn.decode(
            "BoundProfilePackage",
            get_bpp_response.bound_profile_package,
            check_constraints=True,
        )
        logging.debug(f"BoundProfilePackage: {bound_profile_package}")

        def send_and_check(
            data: bytes, label: str | None = None, request_type: str | None = None
        ) -> dict | None:
            if label:
                logging.debug(
                    f"Sending {label}: {data.hex() if isinstance(data, bytes) else data}"
                )

            result = self.store_data(
                caller_func_name=label,
                request_type=request_type,
                response_type="ProfileInstallationResult",
                request_data=data,
            )

            if result:
                result_type, data = result.get("profileInstallationResultData", {}).get(
                    "finalResult", (None, None)
                )
                if result_type == "errorResult":
                    ProfileInstallationException.raise_from_code(data)

            return result

        def register_list(data: list[bytes], tag: int):
            size = sum(len(seq) for seq in data)
            hex_data = [tag]
            data_len = len(i2h([size]))
            if data_len > 2:
                hex_data.append(0x80 + (data_len - 2))

            hex_data.append(size)
            self.store_data(request_data=bytes.fromhex(i2h(hex_data)))

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
        send_and_check(
            bound_profile_package.get("firstSequenceOf87"),
            "firstSequenceOf87",
        )

        # Step 3: Store Metadata
        sequence_of_88 = bound_profile_package.get("sequenceOf88")
        register_list(sequence_of_88, 0xA1)
        for index, sequence in enumerate(sequence_of_88):
            send_and_check(sequence, f"sequenceOf88_{index + 1}")

        # Step 4: Replace Session Keys (optional)
        if second_sequence := bound_profile_package.get("secondSequenceOf87"):
            register_list(second_sequence, 0xA2)
            for index, sequence in enumerate(second_sequence):
                send_and_check(
                    sequence,
                    f"secondSequenceOf87_{index + 1}",
                )

        # Step 5: load profile elements
        sequence_of_86 = bound_profile_package.get("sequenceOf86")
        register_list(sequence_of_86, 0xA3)
        final_result = None
        for index, sequence in enumerate(sequence_of_86):
            final_result = send_and_check(sequence, f"sequenceOf86_{index + 1}")

        return ProfileInstallationResult(**final_result)

    def enable_profile(
        self,
        iccid: str | None = None,
        isdp_aid: str | None = None,
        refresh: bool = False,
    ) -> bool:
        """Enable a profile on the eUICC.Enables the target profile and implicitly disables the Profile currently enabled.

        Args:
            iccid (str | None, optional): ICCID of the target profile. Defaults to None.
            isdp_aid (str | None, optional): ISD-P aid of the target profile. Defaults to None.
            refresh (bool, optional): Sets the refresh flag. For more information: SGP.22 v3.1 [5.6.1]. Defaults to False.

        Returns:
            bool: True, if the profile was enabled successfully.
        Raises:
            ProfileInteractionException: If the profile could not be enabled and some error occurred.
        """
        profile_identifier = {}
        if iccid:
            profile_identifier = ("iccid", bytes.fromhex(iccid))

        if isdp_aid:
            profile_identifier = ("isdpAid", bytes.fromhex(isdp_aid))

        response = self.store_data(
            "EnableProfileRequest",
            "EnableProfileResponse",
            {
                "profileIdentifier": profile_identifier,
                "refreshFlag": refresh,
            },
        )
        logging.debug(f"EnableProfileResponse: {response}")

        if response["enableResult"] != 0:
            ProfileInteractionException.raise_from_code(response["enableResult"])

        return True

    def disable_profile(
        self,
        iccid: str | None = None,
        isdp_aid: str | None = None,
        refresh: bool = False,
    ) -> bool:
        profile_identifier = None
        if iccid:
            profile_identifier = ("iccid", bytes.fromhex(iccid))

        if isdp_aid:
            profile_identifier = ("isdpAid", bytes.fromhex(isdp_aid))

        response = self.store_data(
            "DisableProfileRequest",
            "DisableProfileResponse",
            {"profileIdentifier": profile_identifier, "refreshFlag": refresh},
        )
        logging.debug(f"DisableProfileResponse: {response}")

        if response["disableResult"] != 0:
            ProfileInteractionException.raise_from_code(response["disableResult"])

        return True

    def delete_profile(
        self, iccid: str | None = None, isdp_aid: str | None = None
    ) -> bool:
        profile_identifier = None
        if iccid:
            profile_identifier = ("iccid", bytes.fromhex(iccid))

        if isdp_aid:
            profile_identifier = ("isdpAid", bytes.fromhex(isdp_aid))

        response = self.store_data(
            "DeleteProfileRequest",
            "DeleteProfileResponse",
            profile_identifier,
        )
        logging.debug(f"DeleteProfileResponse: {response}")

        if response["deleteResult"] != 0:
            ProfileInteractionException.raise_from_code(response["deleteResult"])

        return True

    def get_profiles(
        self,
        isdp_aid: str | None = None,
        iccid: str | None = None,
        profile_class: ProfileClass | None = None,
        tags: list[ProfileInfoTag] | None = None,
    ) -> list[Profile]:
        request_data = {}
        if isdp_aid:
            request_data["search_criteria"] = ("isdpAid", isdp_aid)
        elif iccid:
            request_data["search_criteria"] = ("iccid", iccid)
        elif profile_class:
            request_data["search_criteria"] = ("profileClass", profile_class.value)

        if tags:
            request_data["tagList"] = h2b(" ".join([tag.value for tag in tags]))

        response = self.store_data(
            "ProfileInfoListRequest",
            "ProfileInfoListResponse",
            request_data,
        )

        logging.debug(f"ListProfilesResponse: {response}")

        key, data = response
        if key == "profileInfoListError":
            message = "Incorrect input values" if data == 1 else "Unknown error"
            raise NotificationException(message)

        return [Profile(**profile) for profile in data]

    def get_notifications(
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
            raise NotificationException.raise_from_code(data)

        return [Notification(**notification) for notification in data]

    def retrieve_notification_list(
        self,
        seq_number: int | None = None,
        notification_type: NotificationType | None = None,
    ) -> list[PendingNotification]:
        search_criteria = None
        if seq_number:
            search_criteria = {"searchCriteria": ("seqNumber", seq_number)}

        if notification_type:
            bit_string = NotificationEvent.from_flags([notification_type.value])
            search_criteria = {
                "searchCriteria": (
                    "profileManagementOperation",
                    NotificationEvent.serialize(bit_string),
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
            raise ProfileInteractionException.raise_from_code(data)

        notifications = []
        for key, notification in data:
            if key == "profileInstallationResult":
                notifications.append(ProfileInstallationResult(**notification))
            elif key == "otherSignedNotification":
                notifications.append(OtherSignedNotification(**notification))
            elif key == "loadRpmPackageResultSigned":
                notifications.append(LoadRpmPackageResultSigned(**notification))

        return notifications

    def remove_notification(self, seq_number: int) -> bool:
        response = self.store_data(
            "NotificationSentRequest",
            "NotificationSentResponse",
            {"seqNumber": seq_number},
        )

        result_code = response.get("deleteNotificationStatus")
        if result_code == 0:
            return True

        NotificationException.raise_from_code(result_code)

    def process_notifications(
        self,
        pending_notifications: list[PendingNotification],
        remove: bool = True,
    ) -> list[int]:
        processed_notification_seq_numbers = []
        for pending_notification in pending_notifications:
            notification = pending_notification.get_notification()

            smdp_client = SmdpClient(
                smdp_address=notification.address, verify_ssl=False
            )
            logging.debug(f"Processing notification from {notification.address}")

            try:
                smdp_client.handle_notification(pending_notification)

                if remove:
                    self.remove_notification(notification.seq_number)
            except NotificationException as e:
                logging.error(f"Failed to process notification: {e}")
                continue

            processed_notification_seq_numbers.append(notification.seq_number)

        return processed_notification_seq_numbers

    def set_nickname(self, iccid: str, nickname: str) -> bool:
        response = self.store_data(
            "SetNicknameRequest",
            "SetNicknameResponse",
            {"iccid": bytes.fromhex(iccid), "profileNickname": nickname},
        )
        logging.debug(f"SetNicknameResponse: {response}")

        if response["setNicknameResult"] != 0:
            ProfileInteractionException.raise_from_code(response["setNicknameResult"])

        return True

    def set_default_dp_address(self, address: str) -> bool:
        response = self.store_data(
            "SetDefaultDpAddressRequest",
            "SetDefaultDpAddressResponse",
            {"defaultDpAddress": address},
        )
        logging.debug(f"SetDefaultDpAddressResponse: {response}")

        if response["setDefaultDpAddressResult"] != 0:
            raise EuiccException(
                f"Failed to set default DP address: {response['setDefaultDpAddressResult']}"
            )

        return True

    def reset_euicc_memory(
        self, reset_options: list[ResetOption] | ResetOption
    ) -> bool:
        """Deletes selected subsets of the Profiles stored in the eUICC regardless of
        their enabled status or any Profile Policy Rules.

        Args:
            reset_options (list[ResetOption] | ResetOption): Subset of the Profiles to be deleted.

        Returns:
            _type_: True, if the memory was reset successfully.
        Raises:
            EuiccMemoryResetException: If the memory could not be reset and some error occurred.
        """
        if not isinstance(reset_options, list):
            reset_options = [reset_options]

        bit_string = ResetOptionBitString.from_flags(
            [option.value for option in reset_options]
        )

        response = self.store_data(
            "EuiccMemoryResetRequest",
            "EuiccMemoryResetResponse",
            {
                "resetOptions": ResetOptionBitString.serialize(bit_string),
            },
        )
        logging.debug(f"ResetEuiccMemoryResponse: {response}")

        if response["resetResult"] != 0:
            EuiccMemoryResetException.raise_from_code(response["resetResult"])

        return True

    def download_profile(self, profile: ActivationProfile) -> ProfileInstallationResult:
        smdp_address = profile.smdp_address
        if not smdp_address:
            smdp_address = self.get_configured_data().default_dp_address

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
