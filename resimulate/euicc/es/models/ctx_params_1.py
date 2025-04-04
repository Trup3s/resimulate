from osmocom.construct import Bytes, GreedyBytes, HexAdapter, Utf8Adapter
from osmocom.tlv import BER_TLV_IE


class MatchingId(BER_TLV_IE, tag=0x80):
    _construct = Utf8Adapter(GreedyBytes)


class Tac(BER_TLV_IE, tag=0x80):
    _construct = HexAdapter(Bytes(4))


class DeviceCapabilities(BER_TLV_IE, tag=0xA1):
    _construct = GreedyBytes


class Imei(BER_TLV_IE, tag=0x82):
    _construct = HexAdapter(Bytes(8))


class DeviceInfo(BER_TLV_IE, tag=0xA1, nested=[Tac, DeviceCapabilities, Imei]):
    pass


class CtxParamsForCommonAuthentication(
    BER_TLV_IE, tag=0x80, nested=[MatchingId, DeviceInfo]
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
