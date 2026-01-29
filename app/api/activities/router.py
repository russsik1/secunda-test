from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.activities.handler import ActivityHandler
from app.utils.db.session import get_session
from app.utils.schemas.activity import ActivityOut


router = APIRouter(prefix="/activities", tags=["activities"])


@router.get("", response_model=list[ActivityOut])
async def list_activities(
    limit: int = Query(default=200, ge=1, le=2000),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_session),
) -> list[ActivityOut]:
    return await ActivityHandler.list_activities(session=session, limit=limit, offset=offset)

