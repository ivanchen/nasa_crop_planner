import asyncio
import time

import httpx

from app.config import get_settings

LOGIN_URL = "https://appeears.earthdatacloud.nasa.gov/api/login"
# Tokens last ~48 hours; refresh well before that.
TOKEN_LIFETIME_SECONDS = 24 * 3600


class EarthdataAuthError(Exception):
    pass


_token: str | None = None
_token_acquired_at = 0.0
_lock = asyncio.Lock()


async def get_token(force_refresh: bool = False) -> str:
    global _token, _token_acquired_at

    settings = get_settings()
    if not settings.earthdata_configured:
        raise EarthdataAuthError(
            "Earthdata credentials are not configured. Register at https://urs.earthdata.nasa.gov/ "
            "and set EARTHDATA_USERNAME and EARTHDATA_PASSWORD."
        )

    async with _lock:
        expired = time.monotonic() - _token_acquired_at > TOKEN_LIFETIME_SECONDS
        if _token is None or expired or force_refresh:
            _token = await _login(settings.earthdata_username, settings.earthdata_password)
            _token_acquired_at = time.monotonic()
        return _token


async def _login(username: str, password: str) -> str:
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(LOGIN_URL, auth=(username, password))
    except httpx.HTTPError as exc:
        raise EarthdataAuthError(f"Could not reach the AppEEARS login service: {exc}") from exc

    if response.status_code in (401, 403):
        hint = (
            " EARTHDATA_PASSWORD looks like an Earthdata token; AppEEARS needs the account password instead."
            if password.startswith("eyJ")
            else ""
        )
        raise EarthdataAuthError(f"Earthdata login failed: check EARTHDATA_USERNAME and EARTHDATA_PASSWORD.{hint}")
    if response.status_code != 200:
        raise EarthdataAuthError(f"AppEEARS login returned HTTP {response.status_code}.")
    return response.json()["token"]
