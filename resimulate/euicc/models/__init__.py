from pydantic import BaseModel, ConfigDict


class EuiccModel(BaseModel):
    model_config = ConfigDict(serialize_by_alias=True)
