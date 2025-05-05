import enum


class ISDR_AID(enum.Enum):
    DEFAULT = ("default", "a0000005591010ffffffff8900000100")
    _5BER = ("5ber", "a0000005591010ffffffff8900050500")
    XESIM = ("xesim", "A0000005591010FFFFFFFF8900000177")
    ESIM_ME = ("esim_me", "A0000005591010000000008900000300")

    def __init__(self, description: str, aid: str):
        self.description = description
        self.aid = aid

    @classmethod
    def from_description(cls, description: str) -> "ISDR_AID":
        for member in cls:
            if member.description == description:
                return member
        raise ValueError(f"ISD-R description '{description}' is not supported!")

    @classmethod
    def get_all_descriptions(cls) -> list[str]:
        return [member.description for member in cls]
