from pydantic import BaseModel, ConfigDict

from app.utils.schemas.activity import ActivityOut
from app.utils.schemas.building import BuildingOut


class OrganizationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    phones: list[str]
    building: BuildingOut
    activities: list[ActivityOut]

