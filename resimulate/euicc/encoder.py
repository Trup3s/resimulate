from io import BytesIO
from typing import Any

from PIL import Image as PillowImage
from pydantic import GetCoreSchemaHandler
from pydantic_core import CoreSchema, core_schema


class Image(PillowImage.Image):
    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> CoreSchema:
        return core_schema.no_info_plain_validator_function(
            cls.validate,
            serialization=core_schema.plain_serializer_function_ser_schema(
                cls.serialize
            ),
        )

    @classmethod
    def validate(cls, value: Any) -> "Image":
        if isinstance(value, Image):
            return value
        if isinstance(value, PillowImage.Image):
            return cls(value)
        if isinstance(value, bytes) or isinstance(value, bytearray):
            try:
                img = PillowImage.open(BytesIO(value), formats=["PNG", "JPEG"]).copy()
                return img.copy()
            except Exception as e:
                raise ValueError(f"Invalid image data: {e}")
        raise TypeError(
            f"Expected bytes, Pillow Image, or Image, but got {type(value)}"
        )

    @classmethod
    def serialize(cls, value: "Image", *args, **kwargs) -> bytes:
        buffered = BytesIO()
        value.save(buffered, format="PNG")
        return buffered.getvalue()


class HexStr(str):
    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        return core_schema.no_info_plain_validator_function(
            cls.validate,
            serialization=core_schema.plain_serializer_function_ser_schema(
                cls.serialize
            ),
        )

    @classmethod
    def validate(cls, value: Any) -> "HexStr":
        if isinstance(value, HexStr):
            return value
        if isinstance(value, str):
            return cls(value)
        if isinstance(value, bytes) or isinstance(value, bytearray):
            try:
                decoded_bytes = value.hex()
                return cls(decoded_bytes)
            except Exception as e:
                raise ValueError(f"Invalid hexadecimal string: {e}")
        raise TypeError(f"Expected a hex string or bytes, got {type(value)}")

    @classmethod
    def serialize(cls, value: "HexStr", *args, **kwargs) -> str:
        return bytes.fromhex(value)
