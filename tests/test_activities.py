import pytest
from httpx import AsyncClient


pytestmark = pytest.mark.asyncio


async def test_list_activities_sorted(base_url, api_headers, seed_minimal):
    async with AsyncClient(base_url=base_url) as client:
        r = await client.get("/activities?limit=100&offset=0", headers=api_headers)
        assert r.status_code == 200
        data = r.json()
        assert len(data) >= 3
        # Проверяем порядок: level не убывает
        prev = 0
        for item in data:
            level = item["level"]
            assert level >= prev
            prev = level


async def test_list_activities_validation_422(base_url, api_headers):
    async with AsyncClient(base_url=base_url) as client:
        r = await client.get("/activities?offset=-1", headers=api_headers)
        assert r.status_code == 422

