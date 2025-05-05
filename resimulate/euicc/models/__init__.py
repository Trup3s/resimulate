from pydantic import BaseModel, ConfigDict

from resimulate.euicc.encoder import BitString


class EuiccModel(BaseModel):
    model_config = ConfigDict(serialize_by_alias=True)


class PprIds(BitString):
    PPR_UPDATE_CONTROL = 0
    PPR1 = 1
    PPR2 = 2
