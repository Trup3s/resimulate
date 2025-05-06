from enum import IntEnum, StrEnum

import rich.repr
from pydantic import ConfigDict, Field

from resimulate.euicc.encoder import HexStr, Image
from resimulate.euicc.models import EuiccModel, PprIds
from resimulate.euicc.models.notification import NotificationEvent


class ProfileInfoTag(StrEnum):
    ICCID = "5A"
    ISDP_AID = "4F"
    PROFILE_STATE = "9F70"
    NICKNAME = "90"
    SERVICE_PROVIDER_NAME = "91"
    PROFILE_NAME = "92"
    ICON_TYPE = "93"
    ICON = "94"
    PROFILE_CLASS = "95"
    NOTIFICATION_CONFIGURATION_INFO = "B6"
    PROFILE_OWNER = "B7"
    DP_PROPRIETARY_DATA = "B8"
    PROFILE_POLICY_RULES = "99"
    SERVICE_SPECIFIC_DATA_STORED_IN_EUICC = "BF22"
    RPM_CONFIGURATION = "BA"
    HRI_SERVER_ADDRESS = "9B"
    LPR_CONFIGURATION = "BC"
    ENTERPRISE_CONFIGURATION = "BD"
    SERVICE_DESCRIPTION = "9F1F"
    DEVICE_CHANGE_CONFIGURATION = "BF20"
    ENABLED_ON_ESIM_PORT = "9F24"
    PROFILE_SIZE = "9F25"


class ProfileState(IntEnum):
    DISABLED = 0
    ENABLED = 1


class IconType(IntEnum):
    JPG = 0
    PNG = 1


class ProfileClass(IntEnum):
    TEST = 0
    PROVISIONING = 1
    PRODUCTION = 2


class OperatorId(EuiccModel):
    mcc_mnc: HexStr = Field(alias="mccMnc")
    gid_1: HexStr | None = Field(alias="gid1", default=None)
    gid_2: HexStr | None = Field(alias="gid2", default=None)


class NotificationConfigurationInfo(EuiccModel):
    profile_management_operation: NotificationEvent = Field(
        alias="profileManagementOperation"
    )
    notification_address: str = Field(alias="notificationAddress")


@rich.repr.auto
class Profile(EuiccModel):
    iccid: HexStr | None = None
    isdp_aid: HexStr | None = Field(alias="isdpAid", default=None)
    profile_state: ProfileState | None = Field(alias="profileState", default=None)
    nickname: str | None = Field(alias="porfileNickname", default=None)
    service_provider_name: str | None = Field(alias="serviceProviderName", default=None)
    profile_name: str | None = Field(alias="profileName", default=None)
    icon_type: IconType | None = Field(alias="iconType", default=None)
    icon: Image | None = Field(alias="icon", default=None)
    profile_class: ProfileClass | None = Field(alias="profileClass", default=None)
    notification_configuration_info: list[NotificationConfigurationInfo] | None = Field(
        alias="notificationConfigurationInfo", default=None
    )
    profile_owner: OperatorId | None = Field(alias="profileOwner", default=None)
    dp_proprietary_data: dict | None = Field(alias="dpProprietaryData", default=None)
    profile_policy_rules: PprIds | None = Field(
        alias="profilePolicyRules", default=None
    )
    service_specific_data_stored_in_euicc: dict | None = Field(
        alias="serviceSpecificDataStoredInEuicc", default=None
    )
    rpm_configuration: dict | None = Field(alias="rpmConfiguration", default=None)
    hri_server_address: str | None = Field(alias="hriServerAddress", default=None)
    lpr_configuration: dict | None = Field(alias="lprConfiguration", default=None)
    enterprise_configuration: dict | None = Field(
        alias="enterpriseConfiguration", default=None
    )
    service_description: dict | None = Field(alias="serviceDescription", default=None)
    device_change_configuration: dict | None = Field(
        alias="deviceChangeConfiguration", default=None
    )
    enabled_on_esim_port: int | None = Field(alias="enabledOnEsimPort", default=None)
    profile_size: int | None = Field(alias="profileSize", default=None)

    model_config = ConfigDict(arbitrary_types_allowed=True)
