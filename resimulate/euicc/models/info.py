from enum import Enum

import rich.repr
from pydantic import Field

from resimulate.euicc.encoder import BitString, HexStr, VersionType
from resimulate.euicc.models import EuiccModel, PprIds


class EuiccRspCapability(BitString):
    ADDITIONAL_PROFILE = 0
    LOAD_CRL_SUPPORT = 1
    RPM_SUPPORT = 2
    TEST_PROFILE_SUPPORT = 3
    DEVICE_INFO_EXTENSIBILITY_SUPPORT = 4
    SERVICE_SPECIFIC_DATA_SUPPORT = 5
    HRI_SERVER_ADDRESS_SUPPORT = 6
    SERVICE_PROVIDER_MESSAGE_SUPPORT = 7
    LPA_PROXY_SUPPORT = 8
    ENTERPRISE_PROFILES_SUPPORT = 9
    SERVICE_DESCRIPTION_SUPPORT = 10
    DEVICE_CHANGE_SUPPORT = 11
    ENCRYPTED_DEVICE_CHANGE_DATA_SUPPORT = 12
    ESTIMATED_PROFILE_SIZE_INDICATION_SUPPORT = 13
    PROFILE_SIZE_IN_PROFILES_INFO_SUPPORT = 14
    CRL_STAPLING_V3_SUPPORT = 15
    CERT_CHAIN_V3_VERIFICATION_SUPPORT = 16
    SIGNED_SMDS_RESPONSE_V3_SUPPORT = 17
    EUICC_RSP_CAP_IN_INFO1 = 18
    OS_UPDATE_SUPPORT = 19
    CANCEL_FOR_EMPTY_SPN_PN_SUPPORT = 20
    UPDATE_NOTIF_CONFIG_INFO_SUPPORT = 21
    UPDATE_METADATA_V3_SUPPORT = 22
    V3_OBJECTS_IN_CTX_PARAMS_CA_SUPPORT = 23
    PUSH_SERVICE_REGISTRATION_SUPPORT = 24


class UICCCapability(BitString):
    CONTACTLESS_SUPPORT = 0
    USIM_SUPPORT = 1
    ISIM_SUPPORT = 2
    CSIM_SUPPORT = 3
    AKA_MILENAGE = 4
    AKA_CAVE = 5
    AKA_TUAK128 = 6
    AKA_TUAK256 = 7
    USIM_TEST_ALGORITHM = 8
    GBA_AUTHEN_USIM = 10
    GBA_AUTHEN_ISIM = 11
    MBMS_AUTHEN_USIM = 12
    EAP_CLIENT = 13
    JAVACARD = 14
    MULTOS = 15
    MULTIPLE_USIM_SUPPORT = 16
    MULTIPLE_ISIM_SUPPORT = 17
    MULTIPLE_CSIM_SUPPORT = 18
    BER_TLV_FILE_SUPPORT = 19
    DF_LINK_SUPPORT = 20
    CAT_TP = 21
    GET_IDENTITY = 22
    PROFILE_A_X25519 = 23
    PROFILE_B_P256 = 24
    SUCI_CALCULATOR_API = 25
    DNS_RESOLUTION = 26
    SCP11AC = 27
    SCP11C_AUTHORIZATION_MECHANISM = 28
    S16_MODE = 29
    EAKA = 30
    IOT_MINIMAL = 31
    SUCI_NSWO = 32
    NETWORK_ID = 33
    COAP = 34
    GBAU_API = 35
    UIR_5G_PROSE = 36
    SSIM_EAP_TLS = 37
    SSIM_EAP_AKA_PRIME = 38
    USAT_APP_PAIRING = 39


class EuiccCategory(int, Enum):
    OTHER = 0
    BASIC_EUICC = 1
    MEDIUM_EUICC = 2
    CONTACTLESS_EUICC = 3


class TreProperties(BitString):
    IS_DISCRETE = 0
    IS_INTEGRATED = 1
    USES_REMOTE_MEMORY = 2


class CertificationDataObject(EuiccModel):
    platform_label: str = Field(alias="platformLabel")
    discovery_base_url: str = Field(alias="discoveryBaseURL")


class LpaMode(int, Enum):
    LPA_D = 0
    LPA_E = 1


class IotSpecificInfo(EuiccModel):
    pass


@rich.repr.auto
class EuiccInfo2(EuiccModel):
    base_profile_package_version: VersionType = Field(alias="baseProfilePackageVersion")
    lowest_svn: VersionType = Field(alias="lowestSvn")
    euicc_firmware_version: VersionType = Field(alias="euiccFirmwareVersion")
    ext_card_resource: HexStr = Field(alias="extCardResource")
    uicc_capability: UICCCapability = Field(alias="uiccCapability")
    ts102241_version: VersionType | None = Field(alias="ts102241Version", default=None)
    globalplatform_version: VersionType | None = Field(
        alias="globalplatformVersion", default=None
    )
    euicc_rsp_capability: EuiccRspCapability = Field(alias="euiccRspCapability")
    euicc_ci_pkid_list_for_verification: list[HexStr] = Field(
        alias="euiccCiPKIdListForVerification"
    )
    euicc_ci_pkid_list_for_signing: list[HexStr] = Field(
        alias="euiccCiPKIdListForSigning"
    )
    euicc_category: EuiccCategory | None = Field(alias="euiccCategory", default=None)
    forbidden_profile_policy_rules: PprIds | None = Field(
        alias="forbiddenProfilePolicyRules", default=None
    )
    pp_version: VersionType = Field(alias="ppVersion")
    sas_accreditation_number: str | None = Field(
        alias="sasAcreditationNumber", default=None
    )
    certification_data_object: CertificationDataObject | None = Field(
        alias="certificationDataObject", default=None
    )
    tre_properties: TreProperties | None = Field(alias="treProperties", default=None)
    tre_product_reference: str | None = Field(alias="treProductReference", default=None)
    additional_profile_package_versions: list[VersionType] | None = Field(
        alias="additionalProfilePackageVersions", default=None
    )
    lpa_mode: LpaMode | None = Field(alias="lpaMode", default=None)
    euicc_ci_pkid_list_for_signing_v3: list[HexStr] | None = Field(
        alias="euiccCiPKIdListForSigningV3", default=None
    )
    additional_euicc_info: HexStr | None = Field(
        alias="additionalEuiccInfo", default=None
    )
    highest_svn: VersionType | None = Field(alias="highestSvn", default=None)
    iot_specific_info: IotSpecificInfo | None = Field(
        alias="iotSpecificInfo", default=None
    )


@rich.repr.auto
class EuiccInfo1(EuiccModel):
    lowest_svn: VersionType = Field(alias="lowestSvn")
    euicc_ci_pkid_list_for_verification: list[HexStr] = Field(
        alias="euiccCiPKIdListForVerification"
    )
    euicc_ci_pkid_list_for_signing: list[HexStr] = Field(
        alias="euiccCiPKIdListForSigning"
    )
    euicc_ci_pkid_list_for_signing_v3: list[HexStr] | None = Field(
        alias="euiccCiPKIdListForSigningV3", default=None
    )
    euicc_rsp_capability: EuiccRspCapability | None = Field(
        alias="euiccRspCapability", default=None
    )
    highest_svn: VersionType | None = Field(alias="highestSvn", default=None)
