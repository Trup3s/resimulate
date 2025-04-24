from pydantic import EncodedBytes, EncoderProtocol
from typing_extensions import Annotated


class HexEncoder(EncoderProtocol):
    @classmethod
    def decode(cls, data: bytes) -> str:
        return data.hex()

    @classmethod
    def encode(cls, value: str) -> bytes:
        return bytes.fromhex(value)

    @classmethod
    def get_json_format(cls) -> str:
        return "hex-encoder"


HexStr = Annotated[bytes, EncodedBytes(encoder=HexEncoder)]
