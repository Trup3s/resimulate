from pydantic import Field

from resimulate.euicc.es.models.common import SmdppResponse


class InitiateAuthenticationResponse(SmdppResponse):
    server_signed_1: str | None = Field(alias="serverSigned1", default=None)
    server_signature_1: str | None = Field(alias="serverSignature1", default=None)
    euicc_ci_pki_to_be_used: str | None = Field(
        alias="euiccCiPKIdToBeUsed", default=None
    )
    server_certificate: str | None = Field(alias="serverCertificate", default=None)
