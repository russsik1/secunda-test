import os
import sys
import subprocess
import time
from collections.abc import AsyncGenerator

import asyncpg
import pytest
from httpx import AsyncClient


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

@pytest.fixture(scope="session")
def event_loop():
    # Единый event loop на всю сессию, чтобы asyncpg/SQLAlchemy не ловили "different loop".
    import asyncio

    loop = asyncio.new_event_loop()
    try:
        yield loop
    finally:
        loop.close()


def _db_admin_dsn() -> str:
    user = os.environ.get("POSTGRES_USER", "postgres")
    password = os.environ.get("POSTGRES_PASSWORD", "postgres")
    host = os.environ.get("POSTGRES_HOST", "postgres")
    port = os.environ.get("POSTGRES_PORT", "5432")
    return f"postgresql://{user}:{password}@{host}:{port}/postgres"


def _db_name() -> str:
    return os.environ.get("TEST_POSTGRES_DB", "secunda_test")


@pytest.fixture(scope="session", autouse=True)
def _set_test_env() -> None:
    # Важно: `app/db/session.py` читает env при импорте.
    os.environ["API_KEY"] = "test-api-key"
    os.environ["POSTGRES_HOST"] = os.environ.get("POSTGRES_HOST", "postgres")
    os.environ["POSTGRES_PORT"] = os.environ.get("POSTGRES_PORT", "5432")
    os.environ["POSTGRES_USER"] = os.environ.get("POSTGRES_USER", "postgres")
    os.environ["POSTGRES_PASSWORD"] = os.environ.get("POSTGRES_PASSWORD", "postgres")
    os.environ["POSTGRES_DB"] = _db_name()
    os.environ["DB_ECHO"] = "false"

    # На всякий случай сбрасываем кэш настроек (lru_cache)
    try:
        from app.utils.settings.config import get_settings

        get_settings.cache_clear()
    except Exception:
        pass


@pytest.fixture(scope="session")
async def _prepare_test_db(_set_test_env: None) -> AsyncGenerator[None, None]:
    db_name = _db_name()
    admin = await asyncpg.connect(_db_admin_dsn())
    try:
        # Не дропаем БД (часто ловится ObjectInUseError).
        # Если БД уже существует — просто используем её.
        try:
            await admin.execute(f'CREATE DATABASE "{db_name}"')
        except asyncpg.DuplicateDatabaseError:
            pass
    finally:
        await admin.close()

    # Миграции
    env = os.environ.copy()
    subprocess.run(["alembic", "upgrade", "head"], check=True, env=env)

    yield
    # Закрываем пул на завершении сессии тестов
    try:
        from app.utils.db.session import engine

        await engine.dispose()
    except Exception:
        return


@pytest.fixture(autouse=True)
async def _dispose_engine_between_tests(_prepare_test_db: None):
    # anyio/pytest может создавать разные event loop'ы для тестов.
    # Соединения в пуле asyncpg привязаны к loop, поэтому после каждого теста
    # принудительно очищаем пул.
    yield
    try:
        from app.utils.db.session import engine

        await engine.dispose()
    except Exception:
        # На ранних стадиях (до импорта приложения) engine может быть недоступен
        return


def _server_port() -> int:
    return int(os.environ.get("TEST_API_PORT", "8001"))


@pytest.fixture(scope="session")
def api_server(_prepare_test_db: None) -> AsyncGenerator[None, None]:
    # Поднимаем реальный uvicorn в отдельном процессе (внутри контейнера).
    # Так мы избегаем проблем с event loop/pool при ASGITransport.
    env = os.environ.copy()
    port = _server_port()

    proc = subprocess.Popen(
        ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", str(port)],
        cwd=PROJECT_ROOT,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    # Ждём readiness по /health
    import urllib.request

    url = f"http://127.0.0.1:{port}/health"
    deadline = time.time() + 30
    last_err: Exception | None = None
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=1) as resp:
                if resp.status == 200:
                    break
        except Exception as e:
            last_err = e
            time.sleep(0.5)
    else:
        try:
            out = ""
            if proc.stdout is not None:
                out = proc.stdout.read()[-4000:]
        except Exception:
            out = ""
        proc.terminate()
        proc.wait(timeout=5)
        raise RuntimeError(f"Uvicorn didn't start. Last error: {last_err}. Output tail:\n{out}")

    try:
        yield
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except Exception:
            proc.kill()
            proc.wait(timeout=5)


@pytest.fixture
def base_url(api_server: None) -> str:
    port = _server_port()
    return f"http://127.0.0.1:{port}"


@pytest.fixture
def api_headers() -> dict[str, str]:
    return {"X-API-Key": os.environ.get("API_KEY", "test-api-key")}


@pytest.fixture
async def clean_db(_prepare_test_db: None) -> None:
    # Чистим таблицы перед каждым тестом (простая изоляция без cross-loop транзакций).
    from sqlalchemy import text

    from app.utils.db.session import AsyncSessionMaker

    async with AsyncSessionMaker() as session:
        async with session.begin():
            await session.execute(
                text(
                    "TRUNCATE TABLE organization_activities, organization_phones, organizations, activities, buildings RESTART IDENTITY CASCADE"
                )
            )


@pytest.fixture
async def seed_minimal(clean_db: None):
    # Минимальные данные для API тестов
    from sqlalchemy import select, text

    from app.utils.db.models import Activity, Building, Organization, OrganizationPhone, organization_activities
    from app.utils.db.session import AsyncSessionMaker

    async with AsyncSessionMaker() as session:
        async with session.begin():
            b1 = Building(address="Адрес 1", latitude=55.76, longitude=37.62)
            b2 = Building(address="Адрес 2", latitude=56.00, longitude=38.00)
            session.add_all([b1, b2])
            await session.flush()

            # Дерево деятельностей: root(1) -> child(2) -> leaf(3)
            a1 = Activity(name="Деятельность 1", parent_id=None, level=1)
            session.add(a1)
            await session.flush()
            a11 = Activity(name="Деятельность 1.1", parent_id=a1.id, level=2)
            session.add(a11)
            await session.flush()
            a111 = Activity(name="Деятельность 1.1.1", parent_id=a11.id, level=3)
            session.add(a111)
            await session.flush()

            org1 = Organization(name="Организация 1", building_id=b1.id)
            org2 = Organization(name="Организация 2", building_id=b2.id)
            session.add_all([org1, org2])
            await session.flush()

            session.add_all(
                [
                    OrganizationPhone(organization_id=org1.id, phone="111-111"),
                    OrganizationPhone(organization_id=org1.id, phone="222-222"),
                    OrganizationPhone(organization_id=org2.id, phone="333-333"),
                ]
            )

            # org1 привязываем к root и leaf; org2 привязываем только к child
            await session.execute(
                organization_activities.insert().values(organization_id=org1.id, activity_id=a1.id)
            )
            await session.execute(
                organization_activities.insert().values(organization_id=org1.id, activity_id=a111.id)
            )
            await session.execute(
                organization_activities.insert().values(organization_id=org2.id, activity_id=a11.id)
            )

            # sanity: activity ids доступны
            res = await session.execute(select(Activity.id))
            _ = res.scalars().all()

    return {
        "buildings": {"b1": b1, "b2": b2},
        "activities": {"a1": a1, "a11": a11, "a111": a111},
        "organizations": {"org1": org1, "org2": org2},
    }

