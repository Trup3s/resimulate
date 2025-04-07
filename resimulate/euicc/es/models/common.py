from typing import Literal

from osmocom.construct import GreedyBytes, HexAdapter
from osmocom.tlv import BER_TLV_IE
from pydantic import BaseModel, Field


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


class TransactionId(BER_TLV_IE, tag=0x80):
    _construct = HexAdapter(GreedyBytes)


class EuiccInfo1Raw(BER_TLV_IE, tag=0xBF20):
    _construct = GreedyBytes


class EuiccChallengeRaw(BER_TLV_IE, tag=0xBF21):
    _construct = GreedyBytes
