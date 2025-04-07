from osmocom.construct import Enum, GreedyBytes, HexAdapter, Int8ub
from osmocom.tlv import BER_TLV_IE

from resimulate.euicc.es.models.common import TransactionId
from resimulate.euicc.es.models.ctx_params_1 import (
    CtxParams1,
    CtxParamsForCommonAuthentication,
    DeviceCapabilities,
    DeviceInfo,
    Imei,
    MatchingId,
    Tac,
)
from resimulate.euicc.es.models.euicc_signed_1 import EuiccSigned1
from resimulate.euicc.es.models.server_signed_1 import ServerSigned1


class ServerSignature1(BER_TLV_IE, tag=0x5F37):
    _construct = HexAdapter(GreedyBytes)


class EuiccCiPKIdToBeUsed(BER_TLV_IE, tag=0x04):
    _construct = HexAdapter(GreedyBytes)


class Certificate(BER_TLV_IE, tag=0x30):
    _construct = HexAdapter(GreedyBytes)


class EuiccCertificate(BER_TLV_IE, tag=0x30):
    _construct = HexAdapter(GreedyBytes)


class EumCertificate(BER_TLV_IE, tag=0x30):
    _construct = HexAdapter(GreedyBytes)


class AuthenticateServerRequest(
    BER_TLV_IE,
    tag=0xBF38,
    nested=[
        ServerSigned1,
        ServerSignature1,
        EuiccCiPKIdToBeUsed,
        Certificate,
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

    @classmethod
    def build(
        cls,
        profile_matching_id: str,
        server_signed_1: bytes,
        server_signature_1: bytes,
        euicc_ci_pki_to_be_used: bytes,
        server_certificate: bytes,
        imei: str | None = None,
    ):
        device_info_children = [
            Tac(decoded="35290611"),
            DeviceCapabilities(children=[]),
        ]
        if imei:
            device_info_children.append(Imei(decoded=imei))

        ctx_params_fca_children = [
            MatchingId(decoded=profile_matching_id),
            DeviceInfo(children=device_info_children),
        ]

        server_signed_1_cls = ServerSigned1()
        server_signed_1_cls.from_tlv(server_signed_1)

        server_signature_1_cls = ServerSignature1()
        server_signature_1_cls.from_tlv(server_signature_1)

        euicc_ci_pki_to_be_used_cls = EuiccCiPKIdToBeUsed()
        euicc_ci_pki_to_be_used_cls.from_tlv(euicc_ci_pki_to_be_used)

        server_certificate_cls = Certificate()
        server_certificate_cls.from_tlv(server_certificate)

        return cls(
            children=[
                server_signed_1_cls,
                server_signature_1_cls,
                euicc_ci_pki_to_be_used_cls,
                server_certificate_cls,
                CtxParams1(
                    children=[
                        CtxParamsForCommonAuthentication(
                            children=ctx_params_fca_children
                        )
                    ]
                ),
            ]
        )


class AuthenticateErrorCode(BER_TLV_IE, tag=0x02):
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
        invalidCertificate=1,
        invalidSignature=2,
        unsupportedCurve=3,
        noSessionContext=4,
        invalidOid=5,
        euiccChallengeMismatch=6,
        ciPKUnknown=7,
        undefinedError=127,
    )


class AuthenticateResponseError(
    BER_TLV_IE, tag=0xA1, nested=[TransactionId, AuthenticateErrorCode]
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
    tag=0xA0,
    nested=[EuiccSigned1, EuiccSignature1, Certificate, Certificate],
):
    """
    SGP.22 Section 5.7.13:: AuthenticateServerResponse
    AuthenticateResponseOk ::= SEQUENCE {
        euiccSigned1 EuiccSigned1, -- Signed information
        euiccSignature1 [APPLICATION 55] OCTET STRING, --EUICC_Sign1,tag 5F37
        euiccCertificate Certificate, -- eUICC Certificate (CERT.EUICC.ECDSA) signed by the EUM
        eumCertificate Certificate -- EUM Certificate (CERT.EUM.ECDSA) signed by the requested CI
    }
    """

    pass


class AuthenticateServerResponse(
    BER_TLV_IE,
    tag=0xBF38,
    nested=[AuthenticateResponseOk, AuthenticateResponseError],
):
    """
    SGP.22 Section 5.7.13:: AuthenticateServerResponse
    AuthenticateServerResponse ::= [56] CHOICE { -- Tag 'BF38'
        authenticateResponseOk AuthenticateResponseOk,
        authenticateResponseError AuthenticateResponseError
    }
    """

    pass
