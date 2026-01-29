import pytest
from httpx import AsyncClient


pytestmark = pytest.mark.asyncio


async def test_health_no_key_ok(base_url):
    async with AsyncClient(base_url=base_url) as client:
        r = await client.get("/health")
        assert r.status_code == 200


async def test_buildings_no_key_401(base_url):
    async with AsyncClient(base_url=base_url) as client:
        r = await client.get("/buildings")
        assert r.status_code == 401


async def test_buildings_wrong_key_401(base_url):
    async with AsyncClient(base_url=base_url) as client:
        r = await client.get("/buildings", headers={"X-API-Key": "wrong"})
        assert r.status_code == 401


async def test_buildings_with_key_200(base_url, api_headers):
    async with AsyncClient(base_url=base_url) as client:
        r = await client.get("/buildings", headers=api_headers)
        # Даже если список пустой, код должен быть 200
        assert r.status_code == 200
