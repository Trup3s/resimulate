from typing import Literal

from pydantic import BaseModel, Field, Base64Bytes

from resimulate.smdp.exceptions import SmdpException


class FunctionExecutionStatus(BaseModel):
    status: Literal["Executed-Success"] | Literal["Failed"]
    status_code_data: dict | None = Field(alias="statusCodeData", default=None)


class Header(BaseModel):
    function_execution_status: FunctionExecutionStatus = Field(
        alias="functionExecutionStatus"
    )


class SmdpResponse(BaseModel):
    header: Header
    transaction_id: str | None = Field(alias="transactionId", default=None)

    def success(self) -> bool:
        """Check if the authentication response was successful."""
        return self.header.function_execution_status.status == "Executed-Success"

    def raise_on_error(self):
        """Raise an exception if the response indicates an error."""
        if not self.success():
            raise SmdpException(
                f"Error in SMDP response: {self.header.function_execution_status.status_code_data}"
            )


class AuthenticateClientResponse(SmdpResponse):
    profile_metadata: Base64Bytes | None = Field(alias="profileMetadata", default=None)
    smdp_signed_2: Base64Bytes | None = Field(alias="smdpSigned2", default=None)
    smdp_signature_2: Base64Bytes | None = Field(alias="smdpSignature2", default=None)
    smdp_certificate: Base64Bytes | None = Field(alias="smdpCertificate", default=None)


class GetBoundProfilePackageResponse(SmdpResponse):
    bound_profile_package: str | None = Field(alias="boundProfilePackage", default=None)


class InitiateAuthenticationResponse(SmdpResponse):
    server_signed_1: Base64Bytes | None = Field(alias="serverSigned1", default=None)
    server_signature_1: Base64Bytes | None = Field(
        alias="serverSignature1", default=None
    )
    euicc_ci_pki_to_be_used: Base64Bytes | None = Field(
        alias="euiccCiPKIdToBeUsed", default=None
    )
    server_certificate: Base64Bytes | None = Field(
        alias="serverCertificate", default=None
    )
