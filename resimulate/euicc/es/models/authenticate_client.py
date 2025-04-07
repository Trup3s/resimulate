from pydantic import Field

from resimulate.euicc.es.models.common import SmdppResponse


class AuthenticateClientResponse(SmdppResponse):
    profile_metadata: str | None = Field(alias="profileMetadata", default=None)
    smdp_signed_2: str | None = Field(alias="smdpSigned2", default=None)
    smdp_signature_2: str | None = Field(alias="smdpSignature2", default=None)
    smdp_certificate: str | None = Field(alias="smdpCertificate", default=None)
