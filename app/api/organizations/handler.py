from __future__ import annotations

import logging
import math

from fastapi import HTTPException
from sqlalchemy import Select, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.utils.db.models import Activity, Building, Organization, organization_activities
from app.utils.exceptions.http_exceptions import DATABASE_ERROR, INTERNAL_SERVER_ERROR, ORGANIZATION_NOT_FOUND
from app.utils.schemas.activity import ActivityOut
from app.utils.schemas.building import BuildingOut
from app.utils.schemas.organization import OrganizationOut

logger = logging.getLogger(__name__)


class OrganizationHandler:
    @classmethod
    def _haversine_km(cls, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        r = 6371.0
        d_lat = math.radians(lat2 - lat1)
        d_lon = math.radians(lon2 - lon1)
        a = (
            math.sin(d_lat / 2) ** 2
            + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lon / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return r * c

    @classmethod
    def _org_to_out(cls, org: Organization) -> OrganizationOut:
        phones: list[str] = []
        for p in org.phones:
            phones.append(p.phone)

        activities: list[ActivityOut] = []
        for a in org.activities:
            activities.append(ActivityOut.model_validate(a))

        return OrganizationOut(
            id=org.id,
            name=org.name,
            phones=phones,
            building=BuildingOut.model_validate(org.building),
            activities=activities,
        )

    @classmethod
    async def _load_orgs_stmt(cls) -> Select[tuple[Organization]]:
        return (
            select(Organization)
            .options(selectinload(Organization.building))
            .options(selectinload(Organization.phones))
            .options(selectinload(Organization.activities))
        )

    @classmethod
    async def get_organization(cls, session: AsyncSession, organization_id: int) -> OrganizationOut:
        try:
            logger.info(f"Получение организации с ID: {organization_id}")
            stmt = (await cls._load_orgs_stmt()).where(Organization.id == organization_id)
            res = await session.execute(stmt)
            org = res.scalars().first()
            if org is None:
                logger.warning(f"Организация с ID {organization_id} не найдена")
                raise ORGANIZATION_NOT_FOUND(organization_id)
            logger.info(f"Организация {org.name} успешно получена")
            return cls._org_to_out(org)
        except HTTPException:
            raise
        except SQLAlchemyError as e:
            logger.exception(f"Ошибка БД при получении организации {organization_id}")
            raise DATABASE_ERROR()
        except Exception as e:
            logger.exception(f"Неожиданная ошибка при получении организации {organization_id}")
            raise INTERNAL_SERVER_ERROR()

    @classmethod
    async def list_by_building(
        cls, session: AsyncSession, building_id: int, limit: int, offset: int
    ) -> list[OrganizationOut]:
        try:
            logger.info(f"Получение организаций для здания {building_id}, limit={limit}, offset={offset}")
            stmt = (
                (await cls._load_orgs_stmt())
                .where(Organization.building_id == building_id)
                .order_by(Organization.name.asc())
                .offset(offset)
                .limit(limit)
            )
            res = await session.execute(stmt)
            orgs = res.scalars().all()

            out: list[OrganizationOut] = []
            for org in orgs:
                out.append(cls._org_to_out(org))
            logger.info(f"Найдено {len(out)} организаций для здания {building_id}")
            return out
        except SQLAlchemyError as e:
            logger.exception(f"Ошибка БД при получении организаций для здания {building_id}")
            raise DATABASE_ERROR()
        except Exception as e:
            logger.exception(f"Неожиданная ошибка при получении организаций для здания {building_id}")
            raise INTERNAL_SERVER_ERROR()

    @classmethod
    async def list_by_activity(
        cls, session: AsyncSession, activity_id: int, limit: int, offset: int
    ) -> list[OrganizationOut]:
        try:
            logger.info(f"Получение организаций для деятельности {activity_id}, limit={limit}, offset={offset}")
            subq = (
                select(organization_activities.c.organization_id)
                .where(organization_activities.c.activity_id == activity_id)
                .distinct()
                .subquery()
            )

            stmt = (
                (await cls._load_orgs_stmt())
                .where(Organization.id.in_(select(subq.c.organization_id)))
                .order_by(Organization.name.asc())
                .offset(offset)
                .limit(limit)
            )

            res = await session.execute(stmt)
            orgs = res.scalars().all()

            out: list[OrganizationOut] = []
            for org in orgs:
                out.append(cls._org_to_out(org))
            logger.info(f"Найдено {len(out)} организаций для деятельности {activity_id}")
            return out
        except SQLAlchemyError as e:
            logger.exception(f"Ошибка БД при получении организаций для деятельности {activity_id}")
            raise DATABASE_ERROR()
        except Exception as e:
            logger.exception(f"Неожиданная ошибка при получении организаций для деятельности {activity_id}")
            raise INTERNAL_SERVER_ERROR()

    @classmethod
    async def _collect_activity_tree_ids(cls, session: AsyncSession, root_id: int) -> list[int]:
        # Ограничение вложенности 3 уровня: собираем root + детей + внуков.
        ids: list[int] = [root_id]
        current: list[int] = [root_id]

        for _ in range(0, 2):
            if len(current) == 0:
                break
            res = await session.execute(select(Activity.id).where(Activity.parent_id.in_(current)))
            next_ids = res.scalars().all()
            current = []
            for aid in next_ids:
                if aid not in ids:
                    ids.append(aid)
                    current.append(aid)

        return ids

    @classmethod
    async def search_by_activity_tree(
        cls, session: AsyncSession, activity_id: int, limit: int, offset: int
    ) -> list[OrganizationOut]:
        try:
            logger.info(f"Поиск организаций по дереву деятельности {activity_id}, limit={limit}, offset={offset}")
            ids = await cls._collect_activity_tree_ids(session, activity_id)
            logger.debug(f"Найдено {len(ids)} ID деятельностей в дереве для корня {activity_id}")

            subq = (
                select(organization_activities.c.organization_id)
                .where(organization_activities.c.activity_id.in_(ids))
                .distinct()
                .subquery()
            )

            stmt = (
                (await cls._load_orgs_stmt())
                .where(Organization.id.in_(select(subq.c.organization_id)))
                .order_by(Organization.name.asc())
                .offset(offset)
                .limit(limit)
            )

            res = await session.execute(stmt)
            orgs = res.scalars().all()

            out: list[OrganizationOut] = []
            for org in orgs:
                out.append(cls._org_to_out(org))
            logger.info(f"Найдено {len(out)} организаций по дереву деятельности {activity_id}")
            return out
        except SQLAlchemyError as e:
            logger.exception(f"Ошибка БД при поиске организаций по дереву деятельности {activity_id}")
            raise DATABASE_ERROR()
        except Exception as e:
            logger.exception(f"Неожиданная ошибка при поиске организаций по дереву деятельности {activity_id}")
            raise INTERNAL_SERVER_ERROR()

    @classmethod
    async def search_by_name(
        cls, session: AsyncSession, q: str, limit: int, offset: int
    ) -> list[OrganizationOut]:
        try:
            logger.info(f"Поиск организаций по названию: '{q}', limit={limit}, offset={offset}")
            stmt = (
                (await cls._load_orgs_stmt())
                .where(Organization.name.ilike(f"%{q}%"))
                .order_by(Organization.name.asc())
                .offset(offset)
                .limit(limit)
            )
            res = await session.execute(stmt)
            orgs = res.scalars().all()

            out: list[OrganizationOut] = []
            for org in orgs:
                out.append(cls._org_to_out(org))
            logger.info(f"Найдено {len(out)} организаций по запросу '{q}'")
            return out
        except SQLAlchemyError as e:
            logger.exception(f"Ошибка БД при поиске организаций по названию '{q}'")
            raise DATABASE_ERROR()
        except Exception as e:
            logger.exception(f"Неожиданная ошибка при поиске организаций по названию '{q}'")
            raise INTERNAL_SERVER_ERROR()

    @classmethod
    async def list_in_box(
        cls,
        session: AsyncSession,
        lat_min: float,
        lat_max: float,
        lon_min: float,
        lon_max: float,
        limit: int,
        offset: int,
    ) -> list[OrganizationOut]:
        try:
            logger.info(
                f"Поиск организаций в прямоугольной области: "
                f"lat[{lat_min}, {lat_max}], lon[{lon_min}, {lon_max}], limit={limit}, offset={offset}"
            )
            b_stmt = select(Building.id).where(
                Building.latitude >= lat_min,
                Building.latitude <= lat_max,
                Building.longitude >= lon_min,
                Building.longitude <= lon_max,
            )
            res = await session.execute(b_stmt)
            building_ids = res.scalars().all()
            if len(building_ids) == 0:
                logger.info("Зданий в указанной области не найдено")
                return []

            stmt = (
                (await cls._load_orgs_stmt())
                .where(Organization.building_id.in_(building_ids))
                .order_by(Organization.name.asc())
                .offset(offset)
                .limit(limit)
            )
            res = await session.execute(stmt)
            orgs = res.scalars().all()

            out: list[OrganizationOut] = []
            for org in orgs:
                out.append(cls._org_to_out(org))
            logger.info(f"Найдено {len(out)} организаций в прямоугольной области")
            return out
        except SQLAlchemyError as e:
            logger.exception("Ошибка БД при поиске организаций в прямоугольной области")
            raise DATABASE_ERROR()
        except Exception as e:
            logger.exception("Неожиданная ошибка при поиске организаций в прямоугольной области")
            raise INTERNAL_SERVER_ERROR()

    @classmethod
    async def list_in_radius(
        cls,
        session: AsyncSession,
        lat: float,
        lon: float,
        radius_km: float,
        limit: int,
        offset: int,
    ) -> list[OrganizationOut]:
        try:
            logger.info(
                f"Поиск организаций в радиусе: центр({lat}, {lon}), "
                f"радиус={radius_km} км, limit={limit}, offset={offset}"
            )
            # Быстрый pre-filter по bbox (без PostGIS)
            delta_lat = radius_km / 111.0
            cos_lat = math.cos(math.radians(lat))
            if abs(cos_lat) < 1e-6:
                delta_lon = 180.0
            else:
                delta_lon = radius_km / (111.0 * cos_lat)

            lat_min = lat - delta_lat
            lat_max = lat + delta_lat
            lon_min = lon - delta_lon
            lon_max = lon + delta_lon

            res = await session.execute(
                select(Building).where(
                    Building.latitude >= lat_min,
                    Building.latitude <= lat_max,
                    Building.longitude >= lon_min,
                    Building.longitude <= lon_max,
                )
            )
            buildings = res.scalars().all()

            allowed_building_ids: list[int] = []
            for b in buildings:
                d = cls._haversine_km(lat, lon, b.latitude, b.longitude)
                if d <= radius_km:
                    allowed_building_ids.append(b.id)

            if len(allowed_building_ids) == 0:
                logger.info("Зданий в указанном радиусе не найдено")
                return []

            stmt = (
                (await cls._load_orgs_stmt())
                .where(Organization.building_id.in_(allowed_building_ids))
                .order_by(Organization.name.asc())
                .offset(offset)
                .limit(limit)
            )
            res = await session.execute(stmt)
            orgs = res.scalars().all()

            out: list[OrganizationOut] = []
            for org in orgs:
                out.append(cls._org_to_out(org))
            logger.info(f"Найдено {len(out)} организаций в радиусе {radius_km} км")
            return out
        except SQLAlchemyError as e:
            logger.exception("Ошибка БД при поиске организаций в радиусе")
            raise DATABASE_ERROR()
        except Exception as e:
            logger.exception("Неожиданная ошибка при поиске организаций в радиусе")
            raise INTERNAL_SERVER_ERROR()

