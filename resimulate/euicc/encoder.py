from osmocom.utils import b2h, h2b
from pydantic import EncodedBytes, EncoderProtocol
from typing_extensions import Annotated


class HexEncoder(EncoderProtocol):
    @classmethod
    def decode(cls, data: bytes) -> str:
        return b2h(data)

    @classmethod
    def encode(cls, value: bytes) -> bytes:
        return h2b(value)

    @classmethod
    def get_json_format(cls) -> str:
        return "hex-encoder"


HexStr = Annotated[bytes, EncodedBytes(encoder=HexEncoder)]
