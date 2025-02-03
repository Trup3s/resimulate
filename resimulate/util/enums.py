import enum
from typing import Union


class ISDR_AID(str, enum.Enum):
    _DEFAULT = "A0000005591010FFFFFFFF8900000100"
    _5BER = "A0000005591010FFFFFFFF8900050500"

    @staticmethod
    def get_aid(aid_description: str) -> Union["ISDR_AID", None]:
        mapping = {"default": ISDR_AID._DEFAULT, "5ber": ISDR_AID._5BER}
        return mapping.get(aid_description)
