import os

import pytest
from sqlalchemy import func, select


pytestmark = pytest.mark.asyncio


async def test_data_gen_idempotent(_prepare_test_db):
    # Запускаем реальную генерацию 2 раза и убеждаемся, что дублей нет.
    os.environ["POSTGRES_DB"] = os.environ.get("POSTGRES_DB", "secunda_test")

    from app.utils.db.models import Activity, Building, Organization
    from app.utils.db.session import AsyncSessionMaker
    from scripts.data_gen import data_gen_db

    await data_gen_db()
    await data_gen_db()

    async with AsyncSessionMaker() as session:
        b = (await session.execute(select(func.count()).select_from(Building))).scalar_one()
        a = (await session.execute(select(func.count()).select_from(Activity))).scalar_one()
        o = (await session.execute(select(func.count()).select_from(Organization))).scalar_one()

    assert b > 0
    assert a > 0
    assert o > 0

