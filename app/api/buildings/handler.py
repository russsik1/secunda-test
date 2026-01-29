import logging

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.utils.db.models import Building
from app.utils.exceptions.http_exceptions import DATABASE_ERROR, INTERNAL_SERVER_ERROR
from app.utils.schemas.building import BuildingOut

logger = logging.getLogger(__name__)


class BuildingHandler:
    @classmethod
    async def list_buildings(
        cls,
        session: AsyncSession,
        limit: int,
        offset: int,
    ) -> list[BuildingOut]:
        try:
            logger.info(f"Получение списка зданий, limit={limit}, offset={offset}")
            res = await session.execute(select(Building).offset(offset).limit(limit))
            buildings = res.scalars().all()

            out: list[BuildingOut] = []
            for b in buildings:
                out.append(BuildingOut.model_validate(b))
            logger.info(f"Найдено {len(out)} зданий")
            return out
        except SQLAlchemyError as e:
            logger.exception("Ошибка БД при получении списка зданий")
            raise DATABASE_ERROR()
        except Exception as e:
            logger.exception("Неожиданная ошибка при получении списка зданий")
            raise INTERNAL_SERVER_ERROR()

