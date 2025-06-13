from abc import ABC, abstractmethod
from enum import IntEnum
from io import BytesIO
from typing import Any

from PIL import Image as PillowImage
from pydantic import GetCoreSchemaHandler
from pydantic_core import CoreSchema, core_schema


class PydanticSerializableMixin:
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


class Image(PillowImage.Image, PydanticSerializableMixin):
    @classmethod
    def validate(cls, value: Any) -> "Image":
        if isinstance(value, cls):
            return value
        if isinstance(value, PillowImage.Image):
            return value.copy()
        if isinstance(value, (bytes, bytearray)):
            try:
                img = PillowImage.open(BytesIO(value), formats=["PNG", "JPEG"])
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


class HexBase(str, ABC, PydanticSerializableMixin):
    @classmethod
    def validate(cls, value: Any) -> "HexBase":
        if isinstance(value, cls):
            return value
        if isinstance(value, str):
            return cls(value)
        if isinstance(value, (bytes, bytearray)):
            try:
                return cls(cls.decode_bytes(value))
            except Exception as e:
                raise ValueError(f"Invalid hexadecimal input: {e}")
        raise TypeError(f"Expected a hex string or bytes, got {type(value)}")

    @classmethod
    @abstractmethod
    def decode_bytes(cls, value: bytes) -> str: ...

    @classmethod
    @abstractmethod
    def serialize(cls, value: "HexBase", *args, **kwargs) -> bytes: ...


class HexStr(HexBase):
    @classmethod
    def decode_bytes(cls, value: bytes) -> str:
        return value.hex()

    @classmethod
    def serialize(cls, value: "HexStr", *args, **kwargs) -> bytes:
        return bytes.fromhex(value)


class VersionType(HexBase):
    @classmethod
    def decode_bytes(cls, value: bytes) -> str:
        hex_str = value.hex()
        return ".".join(
            str(int(hex_str[i : i + 2], 16)) for i in range(0, len(hex_str), 2)
        )

    @classmethod
    def serialize(cls, value: "VersionType", *args, **kwargs) -> bytes:
        return bytes.fromhex("".join(part.zfill(2) for part in value.split(".")))


class BitStringMeta(type):
    _flags: dict[str, int | IntEnum]

    def __new__(mcs, name, bases, namespace, **kwargs):
        if enum := kwargs.get("enum"):
            if not issubclass(enum, IntEnum):
                raise TypeError("enum must be an IntEnum subclass")

            members = enum.__members__
        else:
            members: dict[str, int] = namespace

        flags = {
            key: value
            for key, value in members.items()
            if not key.startswith("_") and isinstance(value, int)
        }
        namespace["_flags"] = flags
        return super().__new__(mcs, name, bases, namespace)


class BitString(PydanticSerializableMixin, metaclass=BitStringMeta):
    def __init__(self, bitstring: bytes, length: int = None):
        self._bitstring = bitstring
        self._length = length or len(bitstring)

    @classmethod
    def validate(cls, value: Any) -> "BitString":
        if isinstance(value, cls):
            return value
        if isinstance(value, tuple):
            bit_string, length = value
            return cls(bit_string, length)
        raise TypeError(f"Expected bytes or (bytes, length) tuple, got {type(value)}")

    @classmethod
    def serialize(cls, value: "BitString", *args, **kwargs) -> tuple[bytes, int]:
        return value._bitstring, value._length

    def is_set(self, flag_name: str) -> bool:
        if flag_name not in self._flags:
            raise ValueError(f"Unknown flag: {flag_name}")

        bit_position = self._flags[flag_name]
        byte_index = bit_position // 8
        bit_index = 7 - (bit_position % 8)

        if byte_index >= len(self._bitstring):
            return False

        return bool((self._bitstring[byte_index] >> bit_index) & 1)

    @classmethod
    def from_flags(cls, flags: list[int]) -> "BitString":
        """Create a BitString from a list of flags.

        Args:
            flags (list[int]): indexes of the flags to set

        Returns:
            BitString: BitString object with the specified flags set
        """
        if not flags:
            return cls(bytes(), 0)

        bitstring = bytearray((0,) * ((max(flags) // 8) + 1))
        for flag in flags:
            byte_index = flag // 8
            bit_index = 7 - (flag % 8)
            bitstring[byte_index] |= 1 << bit_index

        return cls(bytes(bitstring), len(bitstring) * 8)

    def __repr__(self) -> str:
        flags = [name for name in self._flags if self.is_set(name)]
        return f"<{self.__class__.__name__} flags={flags}>"
