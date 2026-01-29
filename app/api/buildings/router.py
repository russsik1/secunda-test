from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.buildings.handler import BuildingHandler
from app.utils.db.session import get_session
from app.utils.schemas.building import BuildingOut


router = APIRouter(prefix="/buildings", tags=["buildings"])


@router.get("", response_model=list[BuildingOut])
async def list_buildings(
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_session),
) -> list[BuildingOut]:
    return await BuildingHandler.list_buildings(session=session, limit=limit, offset=offset)

