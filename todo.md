## TODO: Тестовое задание — REST API (FastAPI + Pydantic + SQLAlchemy async + Alembic + Docker)

### 0) Подготовка репозитория/структуры
- [x] **Создать структуру проекта**:
  - `app/main.py` (FastAPI, роуты, startup)
  - `app/core/config.py` (настройки через env)
  - `app/core/security.py` (проверка статического API ключа)
  - `app/db/session.py` (async engine + async_sessionmaker)
  - `app/db/base.py` (Base для моделей)
  - `app/db/models.py` (ORM модели)
  - `app/schemas/*.py` (Pydantic схемы ответов/запросов)
  - `app/api/{activities,buildings,organizations}/{router.py,handler.py}`
  - `scripts/seed.py` (заполнение тестовыми данными)
- [x] **Добавить зависимости**:
  - `requirements.txt` (fastapi, uvicorn[standard], pydantic-settings, sqlalchemy[asyncio], asyncpg, alembic)
- [x] **Добавить конфиги** (по мотивам `db example`):
  - `alembic.ini` с `sqlalchemy.url = postgresql+asyncpg://${POSTGRES_USER}:...`
  - `alembic/env.py` под async SQLAlchemy

### 1) Проектирование БД (схема + связи)
- [x] **Таблица `buildings`**:
  - поля: `id`, `address`, `latitude`, `longitude`
  - индексы: `address` (поиск/сортировка), `(latitude, longitude)` (поиск по области)
- [x] **Таблица `activities`** (дерево деятельностей, max 3 уровня):
  - поля: `id`, `name`, `parent_id` (self FK), `level` (1..3)
  - ограничения:
    - `CHECK (level between 1 and 3)`
    - (опционально) уникальность `name + parent_id` (чтобы в одном узле не было дублей)
- [x] **Таблица `organizations`**:
  - поля: `id`, `name`, `building_id` (FK -> buildings.id)
  - индексы: `name` (поиск по названию), `building_id`
- [x] **Таблица `organization_phones`**:
  - поля: `id`, `organization_id` (FK), `phone`
  - индексы: `organization_id`, (опционально) уникальность `(organization_id, phone)`
- [x] **M2M `organization_activities`**:
  - поля: `organization_id`, `activity_id` (оба FK, составной PK)
  - индексы: `activity_id`, `organization_id`

### 2) Миграции Alembic
- [x] **Инициализировать Alembic**: создать папку `alembic/` + `alembic/versions/`
- [x] **Сгенерировать миграции**:
  - миграция 1: создание таблиц + индексы + ограничения
- [x] **Проверить миграции**:
  - `alembic upgrade head` (должно применяться без ошибок)
  - `alembic downgrade base` (если нужно — убедиться, что откатывается)

### 3) Тестовые данные (seed)
- [x] **Подготовить набор данных**:
  - 3–6 зданий с координатами (Москва/СПб/и т.п.)
  - дерево деятельностей глубиной до 3 уровней (пример из задания)
  - 10–30 организаций: разные здания, 1–3 вида деятельностей, 1–3 телефона
- [x] **Реализовать сидинг** (`scripts/seed.py`):
  - подключение через async session
  - вставка данных с `commit`
  - идемпотентность (по возможности): если данные уже есть — не дублировать
- [x] **Интеграция с Docker**:
  - сидинг запускать отдельной командой/сервисом (например `python -m scripts.seed`)

### 4) Безопасность: статический API ключ
- [x] **Сделать зависимость FastAPI**:
  - заголовок: `X-API-Key`
  - сравнение с `API_KEY` из env
  - при ошибке: `401 Unauthorized`
- [x] **Подключить зависимость ко всем эндпоинтам** (или к общему роутеру)

### 5) Реализация API (только чтение, согласно ТЗ)
- [x] **Эндпоинт: список зданий**
  - `GET /buildings`
  - пагинация: `limit/offset` (минимально)
- [x] **Эндпоинт: получить организацию по id**
  - `GET /organizations/{organization_id}`
  - вернуть: `id`, `name`, `phones[]`, `building`, `activities[]`
- [x] **Эндпоинт: список организаций в здании**
  - `GET /organizations/by-building/{building_id}`
  - сортировка по названию (опционально)
- [x] **Эндпоинт: список организаций по конкретной деятельности**
  - `GET /organizations/by-activity/{activity_id}`
  - точное совпадение по activity_id (без потомков)
- [x] **Эндпоинт: поиск организаций по деятельности с учетом дерева**
  - `GET /organizations/search/by-activity-tree/{activity_id}`
  - если activity на уровне 1 — вернуть также организации по всем дочерним (уровни 2–3)
  - реализация: рекурсивный CTE в SQLAlchemy (предпочтительно) либо выборка потомков в несколько запросов (level <= 3)
- [x] **Эндпоинт: поиск организации по названию**
  - `GET /organizations/search/by-name`
  - query param: `q` (substring, case-insensitive)
- [x] **Эндпоинт: организации в радиусе от точки**
  - `GET /organizations/geo/radius`
  - query params: `lat`, `lon`, `radius_km`
  - реализация без PostGIS:
    - быстрый pre-filter по bbox
    - точный фильтр по haversine (в SQL выражении или в Python после выборки)
- [x] **Эндпоинт: организации в прямоугольной области**
  - `GET /organizations/geo/box`
  - query params: `lat_min`, `lat_max`, `lon_min`, `lon_max`

### 6) Pydantic схемы и единый формат ответов
- [x] **Схемы**:
  - `BuildingOut`
  - `ActivityOut`
  - `OrganizationOut` (+ `phones: list[str]`, `building: BuildingOut`, `activities: list[ActivityOut]`)
- [x] **Единообразные ответы**:
  - возвращать чистые JSON объекты/списки
  - ошибки: корректные HTTP коды и `detail`

### 7) Docker
- [x] **Dockerfile**:
  - установить зависимости
  - запуск `uvicorn app.main:app --host 0.0.0.0 --port 8000`
- [x] **docker-compose.yml**:
  - `postgres` (volume, healthcheck)
  - `api` (depends_on healthcheck)
  - env vars: `POSTGRES_*`, `API_KEY`
- [x] **Команды**:
  - запуск: `docker compose up --build` (внутри контейнера: `scripts/data_gen.sh` + `scripts/start.sh`)

### 8) Проверка функционала (ручная)
- [x] **Swagger**: открыть `/docs` и проверить все методы
- [x] **Проверить API-key**:
  - без ключа -> 401
  - с ключом -> 200
- [x] **Проверить кейсы**:
  - org by id
  - orgs by building
  - orgs by activity (точно)
  - orgs by activity-tree (с потомками)
  - name search
  - geo radius / geo box

### 9) Документация
- [x] **Обновить `readme` (или создать `README.md`)**:
  - как запустить через Docker
  - какие переменные окружения нужны
  - примеры запросов (curl) с `X-API-Key`