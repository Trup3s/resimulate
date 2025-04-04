from osmocom.construct import Enum, GreedyBytes, HexAdapter, Int8ub
from osmocom.tlv import BER_TLV_IE
from pySim.euicc import EuiccCertificate, EumCertificate

from resimulate.euicc.es.models.common import TransactionId
from resimulate.euicc.es.models.ctx_params_1 import CtxParams1
from resimulate.euicc.es.models.euicc_signed_1 import EuiccSigned1
from resimulate.euicc.es.models.server_signed_1 import ServerSigned1


class ServerSignature1(BER_TLV_IE, tag=0x5F37):
    _construct = HexAdapter(GreedyBytes)


class EuiccCiPKIdToBeUsed(BER_TLV_IE, tag=0x04):
    _construct = GreedyBytes


class ServerCertificate(BER_TLV_IE, tag=0x30):
    _construct = GreedyBytes


class AuthenticateServerRequest(
    BER_TLV_IE,
    tag=0xBF38,
    nested=[
        ServerSigned1,
        ServerSignature1,
        EuiccCiPKIdToBeUsed,
        ServerCertificate,
        CtxParams1,
    ],
):
    """
    SGP.22 Section 5.7.13:: AuthenticateServerRequest
    AuthenticateServerRequest ::= [56] SEQUENCE { -- Tag 'BF38'
        serverSigned1 ServerSigned1, -- Signed information
        serverSignature1 [APPLICATION 55] OCTET STRING, -- tag ‘5F37’
        euiccCiPKIdToBeUsed SubjectKeyIdentifier, -- CI Public Key Identifier to be used
        serverCertificate Certificate, -- RSP Server Certificate CERT.XXauth.ECDSA
        ctxParams1 CtxParams1
    }
    """

    pass


class AuthenticateErrorCode(BER_TLV_IE, tag=0x81):
    """
    SGP.22 Section 5.7.13:: AuthenticateServerResponse
    AuthenticateErrorCode ::= INTEGER {
        invalidCertificate(1),
        invalidSignature(2),
        unsupportedCurve(3),
        noSessionContext(4),
        invalidOid(5),
        euiccChallengeMismatch(6),
        ciPKUnknown(7),
        undefinedError(127)
    }
    """

    _construct = Enum(
        Int8ub,
        noError=0,
        invalidTransactionId=1,
        invalidSignature=2,
        invalidCertificate=3,
        invalidChallenge=4,
        invalidCertificateChain=5,
        unknownError=6,
    )


class AuthenticateResponseError(
    BER_TLV_IE, tag=0x81, nested=[TransactionId, AuthenticateErrorCode]
):
    """
    SGP.22 Section 5.7.13:: AuthenticateServerResponse
    AuthenticateResponseError ::= SEQUENCE {
        transactionId [0] TransactionId,
        authenticateErrorCode AuthenticateErrorCode
    }
    """

    pass


class EuiccSignature1(BER_TLV_IE, tag=0x5F37):
    _construct = HexAdapter(GreedyBytes)


class AuthenticateResponseOk(
    BER_TLV_IE,
    tag=0x80,
    nested=[EuiccSigned1, EuiccSignature1, EuiccCertificate, EumCertificate],
):
    """
    SGP.22 Section 5.7.13:: AuthenticateServerResponse
    AuthenticateResponseOk ::= SEQUENCE {
        euiccSigned1 EuiccSigned1, -- Signed information
        euiccSignature1 [APPLICATION 55] OCTET STRING, --EUICC_Sign1,
        tag 5F37 euiccCertificate Certificate, -- eUICC Certificate (CERT.EUICC.ECDSA) signed by the EUM
        eumCertificate Certificate -- EUM Certificate (CERT.EUM.ECDSA) signed by the requested CI
    }
    """

    pass


class AuthenticateServerResponse(
    BER_TLV_IE,
    tag=0xBF38,
    nested=[AuthenticateResponseError, AuthenticateResponseOk],
):
    """
    SGP.22 Section 5.7.13:: AuthenticateServerResponse
    AuthenticateServerResponse ::= [56] CHOICE { -- Tag 'BF38'
        authenticateResponseOk AuthenticateResponseOk,
        authenticateResponseError AuthenticateResponseError
    }
    """

    pass
