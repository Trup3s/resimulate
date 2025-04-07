from osmocom.construct import Bytes, GreedyBytes, HexAdapter, Utf8Adapter
from osmocom.tlv import BER_TLV_IE


class VersionType(BER_TLV_IE):
    _construct = HexAdapter(Bytes(3))


class GsmSupportedRelease(VersionType, tag=0x80):
    pass


class UtranSupportedRelease(VersionType, tag=0x81):
    pass


class Cdma2000onexSupportedRelease(VersionType, tag=0x82):
    pass


class Cdma2000hrpdSupportedRelease(VersionType, tag=0x83):
    pass


class Cdma2000ehrpdSupportedRelease(VersionType, tag=0x84):
    pass


class EutranEpcSupportedRelease(VersionType, tag=0x85):
    pass


class ContactlessSupportedRelease(VersionType, tag=0x86):
    pass


class RspCrlSupportedVersion(VersionType, tag=0x87):
    pass


class NrEpcSupportedRelease(VersionType, tag=0x88):
    pass


class Nr5gcSupportedRelease(VersionType, tag=0x89):
    pass


class Eutran5gcSupportedRelease(VersionType, tag=0x90):
    pass


class DeviceCapabilities(
    BER_TLV_IE,
    tag=0xA1,
    nested=[
        GsmSupportedRelease,
        UtranSupportedRelease,
        Cdma2000onexSupportedRelease,
        Cdma2000hrpdSupportedRelease,
        Cdma2000ehrpdSupportedRelease,
        EutranEpcSupportedRelease,
        ContactlessSupportedRelease,
        RspCrlSupportedVersion,
        NrEpcSupportedRelease,
        Nr5gcSupportedRelease,
        Eutran5gcSupportedRelease,
    ],
):
    """
    DeviceCapabilities ::= SEQUENCE { -- Highest fully supported release for each definition
        -- The device SHALL set all the capabilities it supports
        gsmSupportedRelease VersionType OPTIONAL,
        utranSupportedRelease VersionType OPTIONAL,
        cdma2000onexSupportedRelease VersionType OPTIONAL,
        cdma2000hrpdSupportedRelease VersionType OPTIONAL,
        cdma2000ehrpdSupportedRelease VersionType OPTIONAL,
        eutranEpcSupportedRelease VersionType OPTIONAL,
        contactlessSupportedRelease VersionType OPTIONAL,
        rspCrlSupportedVersion VersionType OPTIONAL,
        nrEpcSupportedRelease VersionType OPTIONAL,
        nr5gcSupportedRelease VersionType OPTIONAL,
        eutran5gcSupportedRelease VersionType OPTIONAL,
        lpaSvn VersionType OPTIONAL, -- Not defined in this version of SGP.22
        catSupportedClasses CatSupportedClasses OPTIONAL, -- Not defined in this version of SGP.22
        euiccFormFactorType EuiccFormFactorType OPTIONAL, -- Not defined in this version of SGP.22
        deviceAdditionalFeatureSupport DeviceAdditionalFeatureSupport OPTIONAL
    }
    """

    pass


class Imei(BER_TLV_IE, tag=0x82):
    _construct = HexAdapter(Bytes(8))


class Tac(BER_TLV_IE, tag=0x80):
    _construct = HexAdapter(Bytes(4))


class DeviceInfo(BER_TLV_IE, tag=0xA1, nested=[Tac, DeviceCapabilities, Imei]):
    pass


class MatchingId(BER_TLV_IE, tag=0x80):
    _construct = Utf8Adapter(GreedyBytes)


class CtxParamsForCommonAuthentication(
    BER_TLV_IE, tag=0xA0, nested=[MatchingId, DeviceInfo]
):
    """
    SGP.22 Section 5.7.13:: CtxParams1
    CtxParamsForCommonAuthentication ::= SEQUENCE {
        matchingId UTF8String OPTIONAL, -- The MatchingId could be the Activation code token or EventID or empty
        deviceInfo DeviceInfo -- The Device information
    }
    """

    pass


class CtxParams1(BER_TLV_IE, tag=0xA0, nested=[CtxParamsForCommonAuthentication]):
    """
    SGP.22 Section 5.7.13:: CtxParams1
    CtxParams1 ::= CHOICE {
        ctxParamsForCommonAuthentication CtxParamsForCommonAuthentication-- New contextual data objects MAY be defined for extensibility.
    }
    """

    pass
