from pydantic import Field

from resimulate.euicc.es.models.common import SmdppResponse


class GetBoundProfilePackageResponse(SmdppResponse):
    bound_profile_package: str | None = Field(alias="boundProfilePackage", default=None)
