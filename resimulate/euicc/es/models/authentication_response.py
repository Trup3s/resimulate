from typing import Literal

from pydantic import BaseModel, Field


class FunctionExecutionStatus(BaseModel):
    status: Literal["Executed-Success"] | Literal["Failed"]
    status_code_data: dict | None = Field(alias="statusCodeData", default=None)


class Header(BaseModel):
    function_execution_status: FunctionExecutionStatus = Field(
        alias="functionExecutionStatus"
    )


class AuthenticationResponse(BaseModel):
    header: Header
    transaction_id: str | None = Field(alias="transactionId", default=None)
    server_signed_1: str | None = Field(alias="serverSigned1", default=None)
    server_signature_1: str | None = Field(alias="serverSignature1", default=None)
    euicc_ci_pki_to_be_used: str | None = Field(
        alias="euiccCiPKIdToBeUsed", default=None
    )
    server_certificate: str | None = Field(alias="serverCertificate", default=None)

    def success(self) -> bool:
        """Check if the authentication response was successful."""
        return self.header.function_execution_status.status == "Executed-Success"
