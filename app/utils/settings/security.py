from fastapi import Depends, Header

from app.utils.exceptions.http_exceptions import INVALID_API_KEY
from app.utils.settings.config import Settings, get_settings


async def require_api_key(
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
    settings: Settings = Depends(get_settings),
) -> None:
    if x_api_key is None or x_api_key != settings.API_KEY:
        raise INVALID_API_KEY()

