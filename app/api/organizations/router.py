from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.organizations.handler import OrganizationHandler
from app.utils.db.session import get_session
from app.utils.schemas.organization import OrganizationOut


router = APIRouter(prefix="/organizations", tags=["organizations"])


@router.get("/{organization_id}", response_model=OrganizationOut)
async def get_organization(
    organization_id: int,
    session: AsyncSession = Depends(get_session),
) -> OrganizationOut:
    return await OrganizationHandler.get_organization(session=session, organization_id=organization_id)


@router.get("/by-building/{building_id}", response_model=list[OrganizationOut])
async def list_organizations_by_building(
    building_id: int,
    limit: int = Query(default=200, ge=1, le=2000),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_session),
) -> list[OrganizationOut]:
    return await OrganizationHandler.list_by_building(
        session=session, building_id=building_id, limit=limit, offset=offset
    )


@router.get("/by-activity/{activity_id}", response_model=list[OrganizationOut])
async def list_organizations_by_activity(
    activity_id: int,
    limit: int = Query(default=200, ge=1, le=2000),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_session),
) -> list[OrganizationOut]:
    return await OrganizationHandler.list_by_activity(
        session=session, activity_id=activity_id, limit=limit, offset=offset
    )


@router.get("/search/by-activity-tree/{activity_id}", response_model=list[OrganizationOut])
async def search_organizations_by_activity_tree(
    activity_id: int,
    limit: int = Query(default=500, ge=1, le=5000),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_session),
) -> list[OrganizationOut]:
    return await OrganizationHandler.search_by_activity_tree(
        session=session, activity_id=activity_id, limit=limit, offset=offset
    )


@router.get("/search/by-name", response_model=list[OrganizationOut])
async def search_organizations_by_name(
    q: str = Query(min_length=1, max_length=200),
    limit: int = Query(default=200, ge=1, le=2000),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_session),
) -> list[OrganizationOut]:
    return await OrganizationHandler.search_by_name(session=session, q=q, limit=limit, offset=offset)


@router.get("/geo/box", response_model=list[OrganizationOut])
async def list_organizations_in_box(
    lat_min: float,
    lat_max: float,
    lon_min: float,
    lon_max: float,
    limit: int = Query(default=500, ge=1, le=5000),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_session),
) -> list[OrganizationOut]:
    return await OrganizationHandler.list_in_box(
        session=session,
        lat_min=lat_min,
        lat_max=lat_max,
        lon_min=lon_min,
        lon_max=lon_max,
        limit=limit,
        offset=offset,
    )


@router.get("/geo/radius", response_model=list[OrganizationOut])
async def list_organizations_in_radius(
    lat: float,
    lon: float,
    radius_km: float = Query(ge=0.01, le=500.0),
    limit: int = Query(default=500, ge=1, le=5000),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_session),
) -> list[OrganizationOut]:
    return await OrganizationHandler.list_in_radius(
        session=session, lat=lat, lon=lon, radius_km=radius_km, limit=limit, offset=offset
    )

