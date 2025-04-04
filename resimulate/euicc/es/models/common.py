from osmocom.construct import GreedyBytes
from osmocom.tlv import BER_TLV_IE


class TransactionId(BER_TLV_IE, tag=0x80):
    _construct = GreedyBytes


class EuiccInfo1Raw(BER_TLV_IE, tag=0xBF20):
    _construct = GreedyBytes


class EuiccChallengeRaw(BER_TLV_IE, tag=0xBF21):
    _construct = GreedyBytes
