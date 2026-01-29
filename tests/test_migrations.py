import os
import subprocess

import asyncpg
import pytest


pytestmark = pytest.mark.asyncio


async def test_migrations_upgrade_downgrade():
    # Отдельная БД, чтобы не ломать остальные тесты
    user = os.environ.get("POSTGRES_USER", "postgres")
    password = os.environ.get("POSTGRES_PASSWORD", "postgres")
    host = os.environ.get("POSTGRES_HOST", "postgres")
    port = os.environ.get("POSTGRES_PORT", "5432")
    admin_dsn = f"postgresql://{user}:{password}@{host}:{port}/postgres"

    db_name = "secunda_migrations_test"
    admin = await asyncpg.connect(admin_dsn)
    try:
        await admin.execute(f'DROP DATABASE IF EXISTS "{db_name}"')
        await admin.execute(f'CREATE DATABASE "{db_name}"')
    finally:
        await admin.close()

    env = os.environ.copy()
    env["POSTGRES_DB"] = db_name

    try:
        subprocess.run(["alembic", "upgrade", "head"], check=True, env=env)
        subprocess.run(["alembic", "downgrade", "base"], check=True, env=env)
        subprocess.run(["alembic", "upgrade", "head"], check=True, env=env)
    finally:
        admin = await asyncpg.connect(admin_dsn)
        try:
            await admin.execute(f'DROP DATABASE IF EXISTS "{db_name}"')
        finally:
            await admin.close()

