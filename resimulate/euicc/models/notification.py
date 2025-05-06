from abc import ABC, abstractmethod
from enum import IntEnum
from typing import Literal, Union

import rich.repr
from pydantic import Field

from resimulate.euicc.encoder import BitString, HexStr
from resimulate.euicc.models import EuiccModel


class NotificationType(IntEnum):
    INSTALL = 0
    LOCAL_ENABLE = 1
    LOCAL_DISABLE = 2
    LOCAL_DELETE = 3
    RPM_ENABLE = 4
    RPM_DISABLE = 5
    RPM_DELETE = 6
    LOAD_RPM_PACKAGE_RESULT = 7


class NotificationEvent(BitString, enum=NotificationType):
    pass


@rich.repr.auto
class Notification(EuiccModel):
    seq_number: int = Field(alias="seqNumber")
    event: NotificationEvent = Field(alias="profileManagementOperation")
    address: str = Field(alias="notificationAddress")
    iccid: HexStr | None = Field(alias="iccid", default=None)


class BppCommandId(IntEnum):
    INITIALISE_SECURE_CHANNEL = 0
    CONFIGURE_ISDP = 1
    STORE_METADATA = 2
    STORE_METADATA2 = 3
    REPLACE_SESSION_KEYS = 4
    LOAD_PROFILE_ELEMENTS = 5


class ErrorReason(IntEnum):
    INCORRECT_INPUT_VALUES = 1
    INVALID_SIGNATURE = 2
    INVALID_TRANSACTION_ID = 3
    UNSUPPORTED_CRT_VALUES = 4
    UNSUPPORTED_REMOTE_OPERATION_TYPE = 5
    UNSUPPORTED_PROFILE_CLASS = 6
    BSP_STRUCTURE_ERROR = 7
    BSP_SECURITY_ERROR = 8
    INSTALL_FAILED_DUE_TO_ICCID_ALREADY_EXISTS_ON_EUICC = 9
    INSTALL_FAILED_DUE_TO_INSUFFICIENT_MEMORY_FOR_PROFILE = 10
    INSTALL_FAILED_DUE_TO_INTERRUPTION = 11
    INSTALL_FAILED_DUE_TO_PE_PROCESSING_ERROR = 12
    INSTALL_FAILED_DUE_TO_DATA_MISMATCH = 13
    TEST_PROFILE_INSTALL_FAILED_DUE_TO_INVALID_NAA_KEY = 14
    PPR_NOT_ALLOWED = 15
    ENTERPRISE_PROFILES_NOT_SUPPORTED = 17
    ENTERPRISE_RULES_NOT_ALLOWED = 18
    ENTERPRISE_PROFILE_NOT_ALLOWED = 19
    ENTERPRISE_OID_MISMATCH = 20
    ENTERPRISE_RULES_ERROR = 21
    ENTERPRISE_PROFILES_ONLY = 22
    LPR_NOT_SUPPORTED = 23
    UNKNOWN_TLV_IN_METADATA = 26
    INSTALL_FAILED_DUE_TO_UNKNOWN_ERROR = 127


class SuccessResult(EuiccModel):
    aid: HexStr = Field(alias="aid")
    ppi_response: HexStr = Field(alias="ppiResponse")


class ErrorResult(EuiccModel):
    bpp_command_id: BppCommandId = Field(alias="bppCommandId")
    error_reason: ErrorReason = Field(alias="errorReason")
    ppi_response: HexStr = Field(alias="ppiResponse", default="")


class ProfileInstallationResultData(EuiccModel):
    transaction_id: HexStr = Field(alias="transactionId")
    notification: Notification = Field(alias="notificationMetadata")
    smdp_oid: str = Field(alias="smdpOid")
    final_result: Union[
        tuple[Literal["successResult"], SuccessResult]
        | tuple[Literal["errorResult"], ErrorResult]
    ] = Field(alias="finalResult")


class PendingNotification(EuiccModel, ABC):
    @abstractmethod
    def get_notification(self) -> Notification:
        pass


@rich.repr.auto
class ProfileInstallationResult(PendingNotification):
    data: ProfileInstallationResultData = Field(alias="profileInstallationResultData")
    euicc_sign_pir: HexStr = Field(alias="euiccSignPIR")

    def get_notification(self) -> Notification:
        return self.data.notification


@rich.repr.auto
class OtherSignedNotification(PendingNotification):
    tbs_other_notification: Notification = Field(alias="tbsOtherNotification")
    euicc_notification_signature: HexStr = Field(alias="euiccNotificationSignature")
    euicc_certificate: HexStr = Field(alias="euiccCertificate")
    next_cert_in_chain: HexStr = Field(alias="nextCertInChain")
    other_certs_in_chain: list[HexStr] = Field(alias="otherCertsInChain", default=[])

    def get_notification(self) -> Notification:
        return self.tbs_other_notification


class RpmCommandResult(EuiccModel):
    iccid: HexStr = Field(alias="iccid")
    rpm_command_result_data: tuple[str, dict | int] = Field(
        alias="rpmCommandResultData"
    )


class LoadRpmPackageResultDataSigned(EuiccModel):
    transaction_id: HexStr = Field(alias="transactionId")
    notification: Notification = Field(alias="notificationMetadata")
    smdp_oid: str = Field(alias="smdpOid")
    final_result: Union[
        tuple[Literal["rpmPackageExecutionResult"], list[dict]]
        | tuple[Literal["errorResult"], ErrorResult]
    ] = Field(alias="finalResult")


@rich.repr.auto
class LoadRpmPackageResultSigned(PendingNotification):
    load_rpm_package_result_data_signed: LoadRpmPackageResultDataSigned = Field(
        alias="loadRpmPackageResultDataSigned"
    )
    euicc_sign_rpr: HexStr = Field(alias="euiccSignRPR")

    def get_notification(self) -> Notification:
        return self.load_rpm_package_result_data_signed.notification
