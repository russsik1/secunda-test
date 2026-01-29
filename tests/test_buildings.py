import pytest
from httpx import AsyncClient


pytestmark = pytest.mark.asyncio


async def test_list_buildings_pagination(base_url, api_headers, seed_minimal):
    async with AsyncClient(base_url=base_url) as client:
        r = await client.get("/buildings?limit=1&offset=0", headers=api_headers)
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        assert len(data) == 1


async def test_list_buildings_validation_422(base_url, api_headers):
    async with AsyncClient(base_url=base_url) as client:
        r = await client.get("/buildings?limit=0", headers=api_headers)
        assert r.status_code == 422

