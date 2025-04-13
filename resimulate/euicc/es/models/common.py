from typing import Literal

import asn1tools
from pydantic import BaseModel, Field

asn = asn1tools.compile_files(
    [
        "/home/niklas/Documents/documents/uni/master_thesis/resimulate/asn/pkix1_explicit_88.asn",
        "/home/niklas/Documents/documents/uni/master_thesis/resimulate/asn/pkix1_implicit_88.asn",
        "/home/niklas/Documents/documents/uni/master_thesis/resimulate/asn/pe_definitions_v3_4.asn",
        "/home/niklas/Documents/documents/uni/master_thesis/resimulate/asn/rsp_definitions_v2_6.asn",
    ],
    codec="ber",
    cache_dir=".cache",
)


class FunctionExecutionStatus(BaseModel):
    status: Literal["Executed-Success"] | Literal["Failed"]
    status_code_data: dict | None = Field(alias="statusCodeData", default=None)


class Header(BaseModel):
    function_execution_status: FunctionExecutionStatus = Field(
        alias="functionExecutionStatus"
    )


class SmdppResponse(BaseModel):
    header: Header
    transaction_id: str | None = Field(alias="transactionId", default=None)

    def success(self) -> bool:
        """Check if the authentication response was successful."""
        return self.header.function_execution_status.status == "Executed-Success"
