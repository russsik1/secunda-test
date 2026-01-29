import pytest
from httpx import AsyncClient


pytestmark = pytest.mark.asyncio


async def test_get_organization_ok(base_url, api_headers, seed_minimal):
    org1 = seed_minimal["organizations"]["org1"]
    async with AsyncClient(base_url=base_url) as client:
        r = await client.get(f"/organizations/{org1.id}", headers=api_headers)
        assert r.status_code == 200
        data = r.json()
        assert data["id"] == org1.id
        assert "building" in data
        assert "phones" in data
        assert isinstance(data["phones"], list)
        assert "activities" in data
        assert isinstance(data["activities"], list)


async def test_get_organization_404(base_url, api_headers):
    async with AsyncClient(base_url=base_url) as client:
        r = await client.get("/organizations/999999", headers=api_headers)
        assert r.status_code == 404


async def test_by_building_only_that_building(base_url, api_headers, seed_minimal):
    b1 = seed_minimal["buildings"]["b1"]
    async with AsyncClient(base_url=base_url) as client:
        r = await client.get(f"/organizations/by-building/{b1.id}", headers=api_headers)
        assert r.status_code == 200
        data = r.json()
        assert len(data) >= 1
        for item in data:
            assert item["building"]["id"] == b1.id


async def test_by_activity_exact(base_url, api_headers, seed_minimal):
    a11 = seed_minimal["activities"]["a11"]
    async with AsyncClient(base_url=base_url) as client:
        r = await client.get(f"/organizations/by-activity/{a11.id}", headers=api_headers)
        assert r.status_code == 200
        data = r.json()
        # org2 привязан к a11, org1 — нет
        names = set()
        for item in data:
            names.add(item["name"])
        assert "Организация 2" in names


async def test_by_activity_tree_includes_descendants(base_url, api_headers, seed_minimal):
    a1 = seed_minimal["activities"]["a1"]
    async with AsyncClient(base_url=base_url) as client:
        r = await client.get(f"/organizations/search/by-activity-tree/{a1.id}", headers=api_headers)
        assert r.status_code == 200
        data = r.json()
        names = set()
        for item in data:
            names.add(item["name"])
        # root включает leaf и child → значит включит и org1 (root+leaf) и org2 (child)
        assert "Организация 1" in names
        assert "Организация 2" in names


async def test_search_by_name_case_insensitive(base_url, api_headers, seed_minimal):
    async with AsyncClient(base_url=base_url) as client:
        r = await client.get("/organizations/search/by-name?q=организация", headers=api_headers)
        assert r.status_code == 200
        data = r.json()
        assert len(data) >= 2


async def test_search_by_name_empty_422(base_url, api_headers):
    async with AsyncClient(base_url=base_url) as client:
        r = await client.get("/organizations/search/by-name?q=", headers=api_headers)
        assert r.status_code == 422


async def test_geo_box(base_url, api_headers, seed_minimal):
    # box включает b1 (55.76, 37.62) и исключает b2 (56.00, 38.00)
    async with AsyncClient(base_url=base_url) as client:
        r = await client.get(
            "/organizations/geo/box?lat_min=55.70&lat_max=55.80&lon_min=37.60&lon_max=37.70",
            headers=api_headers,
        )
        assert r.status_code == 200
        data = r.json()
        assert len(data) >= 1
        for item in data:
            assert item["building"]["address"] == "Адрес 1"


async def test_geo_radius(base_url, api_headers, seed_minimal):
    # точка рядом с b1, радиус маленький
    async with AsyncClient(base_url=base_url) as client:
        r = await client.get(
            "/organizations/geo/radius?lat=55.76&lon=37.62&radius_km=2",
            headers=api_headers,
        )
        assert r.status_code == 200
        data = r.json()
        assert len(data) >= 1
        for item in data:
            assert item["building"]["address"] == "Адрес 1"


async def test_geo_radius_validation_422(base_url, api_headers):
    async with AsyncClient(base_url=base_url) as client:
        r = await client.get(
            "/organizations/geo/radius?lat=55&lon=37&radius_km=0",
            headers=api_headers,
        )
        assert r.status_code == 422

