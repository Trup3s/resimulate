from osmocom.construct import Bytes, GreedyBytes, HexAdapter, Utf8Adapter
from osmocom.tlv import BER_TLV_IE
from pySim.euicc import EuiccInfo2

from resimulate.euicc.es.models.common import TransactionId
from resimulate.euicc.es.models.ctx_params_1 import CtxParams1


class ServerAddress(BER_TLV_IE, tag=0x81):
    _construct = Utf8Adapter(GreedyBytes)


class ServerChallenge(BER_TLV_IE, tag=0x82):
    _construct = HexAdapter(Bytes(16))


class EuiccSigned1(
    BER_TLV_IE,
    tag=0xBF38,
    nested=[TransactionId, ServerAddress, ServerChallenge, EuiccInfo2, CtxParams1],
):
    """
    SGP.22 Section 5.7.13:: AuthenticateServerResponse
    EuiccSigned1 ::= SEQUENCE {
        transactionId [0] TransactionId,
        serverAddress [3] UTF8String, -- The RSP Server address as an FQDN
        serverChallenge [4] Octet16, -- The RSP Server Challenge
        euiccInfo2 [34] EUICCInfo2,
        ctxParams1 CtxParams1
    }
    """

    pass
