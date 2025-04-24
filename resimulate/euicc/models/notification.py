from enum import Enum
from typing import Literal, Union

from pydantic import BaseModel, ConfigDict, Field

from resimulate.euicc.encoder import HexStr


class EuiccModel(BaseModel):
    model_config = ConfigDict(serialize_by_alias=True)


class NotificationType(int, Enum):
    INSTALL = 0
    ENABLE = 1
    DISABLE = 2
    DELETE = 3


class Notification(EuiccModel):
    seq_number: int = Field(alias="seqNumber")
    event: tuple[bytes, NotificationType] = Field(alias="profileManagementOperation")
    address: str = Field(alias="notificationAddress")
    iccid: HexStr | None = Field(alias="iccid", default=None)


class BppCommandId(int, Enum):
    INITIALISE_SECURE_CHANNEL = 0
    CONFIGURE_ISDP = 1
    STORE_METADATA = 2
    STORE_METADATA2 = 3
    REPLACE_SESSION_KEYS = 4
    LOAD_PROFILE_ELEMENTS = 5


class ErrorReason(int, Enum):
    INCORRECT_INPUT_VALUES = 1
    INVALID_SIGNATURE = 2
    INVALID_TRANSACTION_ID = 3
    UNSUPPORTED_CRT_VALUES = 4
    UNSUPPORTED_REMOTE_OPERATION_TYPE = 5
    UNSUPPORTED_PROFILE_CLASS = 6
    SCP03T_STRUCTURE_ERROR = 7
    SCP03T_SECURITY_ERROR = 8
    INSTALL_FAILED_DUE_TO_ICCID_ALREADY_EXISTS_ON_EUICC = 9
    INSTALL_FAILED_DUE_TO_INSUFFICIENT_MEMORY_FOR_PROFILE = 10
    INSTALL_FAILED_DUE_TO_INTERRUPTION = 11
    INSTALL_FAILED_DUE_TO_PE_PROCESSING_ERROR = 12
    INSTALL_FAILED_DUE_TO_DATA_MISMATCH = 13
    TEST_PROFILE_INSTALL_FAILED_DUE_TO_INVALID_NAA_KEY = 14
    PPR_NOT_ALLOWED = 15
    INSTALL_FAILED_DUE_TO_UNKNOWN_ERROR = 127


class SuccessResult(EuiccModel):
    aid: HexStr = Field(alias="aid")
    sima_response: HexStr = Field(alias="simaResponse")


class ErrorResult(EuiccModel):
    bpp_command_id: BppCommandId = Field(alias="bppCommandId")
    error_reason: ErrorReason = Field(alias="errorReason")
    sima_response: HexStr = Field(alias="simaResponse", default="")


class ProfileInstallationResultData(EuiccModel):
    transaction_id: HexStr = Field(alias="transactionId")
    notification: Notification = Field(alias="notificationMetadata")
    smdp_oid: str = Field(alias="smdpOid")
    final_result: Union[
        tuple[Literal["successResult"], SuccessResult]
        | tuple[Literal["errorResult"], ErrorResult]
    ] = Field(alias="finalResult")


class ProfileInstallationResult(EuiccModel):
    data: ProfileInstallationResultData = Field(alias="profileInstallationResultData")
    euicc_sign_pir: HexStr = Field(alias="euiccSignPIR")


class OtherSignedNotification(EuiccModel):
    tbs_other_notification: Notification = Field(alias="tbsOtherNotification")
    euicc_notification_signature: HexStr = Field(alias="euiccNotificationSignature")
    euicc_certificate: HexStr = Field(alias="euiccCertificate")
    eum_certificate: HexStr = Field(alias="eumCertificate")
