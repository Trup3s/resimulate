from pydantic import Field
from resimulate.euicc.encoder import HexStr
from resimulate.euicc.models import EuiccModel


class Ci(EuiccModel):
    ci_pkid: HexStr | None = Field(alias="ciPKId", default=None)
    ci_name: str | None = Field(alias="ciName", default=None)


class EuiccConfiguredData(EuiccModel):
    default_dp_address: str | None = Field(alias="defaultDpAddress", default=None)
    root_ds_address: str | None = Field(alias="rootDsAddress", default=None)
    additional_root_ds_address: str | None = Field(
        alias="additionalRootDsAddress", default=None
    )
    allowd_ci_pkid: HexStr | None = Field(alias="allowedCiPKId", default=None)
    ci_list: list[Ci] | None = Field(alias="ciList", default=None)
