from enum import StrEnum


class MutationType(StrEnum):
    BITFLIP = "bitflip"
    RANDOM_BYTE = "random_byte"
    ZERO_BLOCK = "zero_block"
    SHUFFLE_BLOCKS = "shuffle_blocks"
    TRUNCATE = "truncate"
    NONE = "none"
