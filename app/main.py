import logging
import sys

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.activities.router import router as activities_router
from app.api.buildings.router import router as buildings_router
from app.api.organizations.router import router as organizations_router
from app.utils.settings.security import require_api_key

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
)

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Secunda REST API",
    version="0.1.0",
)

logger.info("Запуск приложения Secunda REST API")


app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"^http://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(buildings_router, dependencies=[Depends(require_api_key)])
app.include_router(activities_router, dependencies=[Depends(require_api_key)])
app.include_router(organizations_router, dependencies=[Depends(require_api_key)])


@app.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    return {"status": "ok"}

