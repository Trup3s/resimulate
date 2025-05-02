from enum import Enum

from pydantic import BaseModel, Field

from resimulate.asn import asn
from resimulate.euicc.encoder import HexStr


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
    identifiers_ppr_update_control = 0
    ppr1 = 1
    ppr2 = 2


class OperatorId(BaseModel):
    mcc_mnc: HexStr = Field(alias="mccMnc")
    gid_1: HexStr | None = Field(alias="gid1", default=None)
    gid_2: HexStr | None = Field(alias="gid2", default=None)


class Profile(BaseModel):
    iccid: HexStr | None = None
    isdp_aid: HexStr | None = Field(alias="isdpAid", default=None)
    profile_state: ProfileState | None = Field(alias="profileState", default=None)
    nickname: str | None = Field(alias="porfileNickname", default=None)
    service_provider_name: str | None = Field(alias="serviceProviderName", default=None)
    profile_name: str | None = Field(alias="profileName", default=None)
    icon_type: IconType | None = Field(alias="iconType", default=None)
    icon: bytes | None = Field(alias="icon", default=None)
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

    @classmethod
    def from_asn(cls, data: bytes) -> "Profile":
        """
        ProfileInfo ::= [PRIVATE 3] SEQUENCE { -- Tag 'E3'
            iccid          Iccid OPTIONAL,
            isdpAid        [APPLICATION 15] OctetTo16 OPTIONAL, -- AID of the ISD-P containing the Profile, tag '4F'
            profileState   [112] ProfileState OPTIONAL, -- Tag '9F70'
            profileNickname [16] UTF8String (SIZE (0..64)) OPTIONAL, -- Tag '90'
            serviceProviderName [17] UTF8String (SIZE (0..32)) OPTIONAL, -- Tag '91'
            profileName    [18] UTF8String (SIZE (0..64)) OPTIONAL, -- Tag '92'
            iconType       [19] IconType OPTIONAL, -- Tag '93'
            icon           [20] OCTET STRING (SIZE (0..1024)) OPTIONAL, -- Tag '94',
            profileClass   [21] ProfileClass OPTIONAL, -- Tag '95'
            notificationConfigurationInfo [22] SEQUENCE OF NotificationConfigurationInformation OPTIONAL, -- Tag 'B6'
            profileOwner   [23] OperatorId OPTIONAL, -- Tag 'B7'
            dpProprietaryData [24] DpProprietaryData OPTIONAL, -- Tag 'B8'
            profilePolicyRules [25] PprIds OPTIONAL, -- Tag '99'
            serviceSpecificDataStoredInEuicc [34] VendorSpecificExtension OPTIONAL, -- #SupportedFromV2.4.0# Tag 'BF22'
            rpmConfiguration [26] RpmConfiguration OPTIONAL, -- #SupportedForRpmV3.0.0# Tag 'BA'
            hriServerAddress [27] UTF8String OPTIONAL, -- #SupportedFromV3.0.0# Tag '9B'
            lprConfiguration [28] LprConfiguration OPTIONAL, -- #SupportedForLpaProxyV3.0.0# Tag 'BC'
            enterpriseConfiguration [29] EnterpriseConfiguration OPTIONAL, -- #SupportedForEnterpriseV3.0.0# Tag 'BD'
            serviceDescription [31] ServiceDescription OPTIONAL, -- #SupportedFromV3.0.0# Tag '9F1F'
            deviceChangeConfiguration [32] DeviceChangeConfiguration OPTIONAL, -- #SupportedForDcV3.0.0# Tag 'BF20'
            enabledOnEsimPort [36] INTEGER OPTIONAL, -- #SupportedForMEPV3.0.0# Tag '9F24'
            profileSize    [37] INTEGER OPTIONAL -- #SupportedFromV3.0.0# Tag '9F25'
        }
        """
        data = asn.decode("ProfileInfo", data, check_constraints=True)
        data = cls(**data)
