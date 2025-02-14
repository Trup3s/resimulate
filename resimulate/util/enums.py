import enum


class ISDR_AID(str, enum.Enum):
    DEFAULT = "a0000005591010ffffffff8900000100"
    AID_5BER = "a0000005591010ffffffff8900050500"

    @staticmethod
    def get_aid(aid_description: str) -> "ISDR_AID":
        mapping = {"default": ISDR_AID.DEFAULT, "5ber": ISDR_AID.AID_5BER}
        isdr_aid = mapping.get(aid_description)

        if not isdr_aid:
            raise ValueError(f"ISD-R AID {aid_description} is not supported!")

        return isdr_aid
