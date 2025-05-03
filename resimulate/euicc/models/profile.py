from enum import Enum

from pydantic import ConfigDict, Field

from resimulate.euicc.encoder import HexStr, Image
from resimulate.euicc.models import EuiccModel


class ProfileState(int, Enum):
    DISABLED = 0
    ENABLED = 1


class IconType(int, Enum):
    JPG = 0
    PNG = 1


class ProfileClass(int, Enum):
    TEST = 0
    PROVISIONING = 1
    PRODUCTION = 2


class PprIds(int, Enum):
    ppr_update_control = 0
    ppr1 = 1
    ppr2 = 2


class OperatorId(EuiccModel):
    mcc_mnc: HexStr = Field(alias="mccMnc")
    gid_1: HexStr | None = Field(alias="gid1", default=None)
    gid_2: HexStr | None = Field(alias="gid2", default=None)


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
    notification_configuration_info: list[str] | None = Field(
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
