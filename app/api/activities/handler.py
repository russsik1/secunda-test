import logging

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.utils.db.models import Activity
from app.utils.exceptions.http_exceptions import DATABASE_ERROR, INTERNAL_SERVER_ERROR
from app.utils.schemas.activity import ActivityOut

logger = logging.getLogger(__name__)


class ActivityHandler:
    @classmethod
    async def list_activities(
        cls,
        session: AsyncSession,
        limit: int,
        offset: int,
    ) -> list[ActivityOut]:
        try:
            logger.info(f"Получение списка деятельностей, limit={limit}, offset={offset}")
            res = await session.execute(
                select(Activity).order_by(Activity.level.asc(), Activity.id.asc()).offset(offset).limit(limit)
            )
            items = res.scalars().all()

            out: list[ActivityOut] = []
            for a in items:
                out.append(ActivityOut.model_validate(a))
            logger.info(f"Найдено {len(out)} деятельностей")
            return out
        except SQLAlchemyError as e:
            logger.exception("Ошибка БД при получении списка деятельностей")
            raise DATABASE_ERROR()
        except Exception as e:
            logger.exception("Неожиданная ошибка при получении списка деятельностей")
            raise INTERNAL_SERVER_ERROR()

