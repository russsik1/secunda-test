import asyncio
import logging
from dataclasses import dataclass

from sqlalchemy import insert, select
from sqlalchemy.exc import SQLAlchemyError

from app.utils.db.models import Activity, Building, Organization, OrganizationPhone, organization_activities
from app.utils.db.session import AsyncSessionMaker

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class DataGenBuilding:
    name: str
    address: str
    latitude: float
    longitude: float


@dataclass(frozen=True, slots=True)
class DataGenActivity:
    name: str
    parent_name: str | None
    level: int


@dataclass(frozen=True, slots=True)
class DataGenOrganization:
    name: str
    building_name: str
    phones: list[str]
    activity_names: list[str]


def build_data_gen_buildings(count: int = 5) -> list[DataGenBuilding]:
    buildings: list[DataGenBuilding] = []
    base_lat = 55.7500
    base_lon = 37.6100

    for i in range(1, count + 1):
        buildings.append(
            DataGenBuilding(
                name=f"Здание {i}",
                address=f"Адрес {i}",
                latitude=base_lat + (i * 0.01),
                longitude=base_lon + (i * 0.01),
            )
        )

    return buildings


def build_data_gen_activities() -> list[DataGenActivity]:
    # Дерево глубиной до 3 уровней (все имена простые/шаблонные).
    activities: list[DataGenActivity] = []

    # Уровень 1
    for i in range(1, 4):
        activities.append(DataGenActivity(name=f"Деятельность {i}", parent_name=None, level=1))

    # Уровень 2 (по 2 подтипа на каждый тип 1 уровня)
    for i in range(1, 4):
        for j in range(1, 3):
            activities.append(
                DataGenActivity(
                    name=f"Деятельность {i}.{j}",
                    parent_name=f"Деятельность {i}",
                    level=2,
                )
            )

    # Уровень 3 (по 2 подтипа на каждый тип 2 уровня)
    for i in range(1, 4):
        for j in range(1, 3):
            for k in range(1, 3):
                activities.append(
                    DataGenActivity(
                        name=f"Деятельность {i}.{j}.{k}",
                        parent_name=f"Деятельность {i}.{j}",
                        level=3,
                    )
                )

    return activities


def build_data_gen_organizations(count: int = 15) -> list[DataGenOrganization]:
    organizations: list[DataGenOrganization] = []
    buildings = build_data_gen_buildings()
    activities = build_data_gen_activities()

    level1_activity_names: list[str] = []
    for a in activities:
        if a.level == 1:
            level1_activity_names.append(a.name)

    for i in range(1, count + 1):
        building = buildings[(i - 1) % len(buildings)]

        phones: list[str] = []
        phones_count = 1 + ((i - 1) % 3)
        for p in range(1, phones_count + 1):
            phones.append(f"000-000-{i:02d}-{p}")

        activity_names: list[str] = []
        activity_names.append(level1_activity_names[(i - 1) % len(level1_activity_names)])

        # Периодически добавляем ещё один вид деятельности
        if i % 2 == 0:
            activity_names.append(level1_activity_names[(i) % len(level1_activity_names)])

        organizations.append(
            DataGenOrganization(
                name=f"Организация {i}",
                building_name=building.name,
                phones=phones,
                activity_names=activity_names,
            )
        )

    return organizations


async def data_gen_db() -> None:
    try:
        buildings_data = build_data_gen_buildings()
        activities_data = build_data_gen_activities()
        organizations_data = build_data_gen_organizations()

        logger.info(
            "data_gen: start (buildings=%s, activities=%s, organizations=%s)",
            len(buildings_data),
            len(activities_data),
            len(organizations_data),
        )

        async with AsyncSessionMaker() as session:
            async with session.begin():
                # 1) Buildings (идемпотентно по address)
                existing_buildings: dict[str, Building] = {}
                res = await session.execute(select(Building))
                for b in res.scalars().all():
                    existing_buildings[b.address] = b

                for sb in buildings_data:
                    if sb.address in existing_buildings:
                        continue
                    b = Building(address=sb.address, latitude=sb.latitude, longitude=sb.longitude)
                    session.add(b)
                    existing_buildings[sb.address] = b

                await session.flush()

                buildings_by_name: dict[str, Building] = {}
                for sb in buildings_data:
                    b = existing_buildings.get(sb.address)
                    if b is not None:
                        buildings_by_name[sb.name] = b

                # 2) Activities (идемпотентно по (parent_id, name))
                existing_activities: dict[tuple[int | None, str], Activity] = {}
                res = await session.execute(select(Activity))
                for a in res.scalars().all():
                    existing_activities[(a.parent_id, a.name)] = a

                activities_by_name: dict[str, Activity] = {}

                # создаём по уровням: 1 -> 2 -> 3, чтобы parent_id уже был известен
                for level in (1, 2, 3):
                    for sa in activities_data:
                        if sa.level != level:
                            continue

                        parent_id: int | None = None
                        if sa.parent_name is not None:
                            parent = activities_by_name.get(sa.parent_name)
                            if parent is None:
                                continue
                            parent_id = parent.id

                        key = (parent_id, sa.name)
                        existing = existing_activities.get(key)
                        if existing is None:
                            a = Activity(name=sa.name, parent_id=parent_id, level=sa.level)
                            session.add(a)
                            existing_activities[key] = a
                            activities_by_name[sa.name] = a
                        else:
                            activities_by_name[sa.name] = existing

                    await session.flush()

                # 3) Organizations (идемпотентно по name)
                existing_org_names: set[str] = set()
                res = await session.execute(select(Organization.name))
                for name in res.scalars().all():
                    existing_org_names.add(name)

                for so in organizations_data:
                    if so.name in existing_org_names:
                        continue

                    building = buildings_by_name.get(so.building_name)
                    if building is None:
                        continue

                    org = Organization(name=so.name, building_id=building.id)
                    session.add(org)
                    await session.flush()

                    for phone in so.phones:
                        session.add(OrganizationPhone(organization_id=org.id, phone=phone))

                    for an in so.activity_names:
                        a = activities_by_name.get(an)
                        if a is None:
                            continue
                        await session.execute(
                            insert(organization_activities).values(
                                organization_id=org.id,
                                activity_id=a.id,
                            )
                        )

                    existing_org_names.add(so.name)

        logger.info("data_gen: done")
    except SQLAlchemyError:
        logger.exception("data_gen: database error")
        raise
    except Exception:
        logger.exception("data_gen: unexpected error")
        raise


async def run() -> None:
    # Если data_gen запускается отдельно (до uvicorn), настроим минимальное логирование.
    root = logging.getLogger()
    if len(root.handlers) == 0:
        logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    await data_gen_db()


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()

