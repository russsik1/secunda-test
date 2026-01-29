import os

from app.utils.settings.config import get_settings


def test_database_url_builds_from_env(monkeypatch):
    monkeypatch.setenv("POSTGRES_HOST", "h")
    monkeypatch.setenv("POSTGRES_PORT", "5433")
    monkeypatch.setenv("POSTGRES_USER", "u")
    monkeypatch.setenv("POSTGRES_PASSWORD", "p")
    monkeypatch.setenv("POSTGRES_DB", "d")

    # lru_cache: сбрасываем кэш, чтобы env применился
    get_settings.cache_clear()
    s = get_settings()
    assert s.database_url == "postgresql+asyncpg://u:p@h:5433/d"
    # Возвращаем кэш в чистое состояние для остальных тестов
    get_settings.cache_clear()


def test_defaults(monkeypatch):
    for k in ("POSTGRES_HOST", "POSTGRES_PORT", "POSTGRES_USER", "POSTGRES_PASSWORD", "POSTGRES_DB"):
        monkeypatch.delenv(k, raising=False)
    get_settings.cache_clear()

    s = get_settings()
    assert "postgresql+asyncpg://" in s.database_url
    get_settings.cache_clear()


def test_db_echo_bool_parsing(monkeypatch):
    monkeypatch.setenv("DB_ECHO", "true")
    get_settings.cache_clear()
    s = get_settings()
    assert bool(s.DB_ECHO) is True
    get_settings.cache_clear()

