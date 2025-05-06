from enum import IntEnum

from resimulate.euicc.encoder import BitString


class ResetOption(IntEnum):
    DELETE_OPERATIONAL_PROFILES = 0
    DELETE_FIELD_LOADED_TEST_PROFILES = 1
    RESET_DEFAULT_SMDP_ADDRESS = 2
    DELETE_PRE_LOADED_TEST_PROFILES = 3  # RSP > v3.0.0
    DELETE_PROVISIONING_PROFILES = 4  # RSP > v3.0.0

    @staticmethod
    def all():
        return list(ResetOption)


class ResetOptionBitString(BitString, enum=ResetOption):
    pass
