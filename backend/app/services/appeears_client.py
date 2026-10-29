from datetime import date, timedelta

import httpx

from app.config import get_settings
from app.services.cache import TTLCache
from app.services.earthdata_auth import get_token
from app.services.satellite_summary import SatelliteData, parse_results_csvs

BASE_URL = "https://appeears.earthdatacloud.nasa.gov/api"
NDVI_PRODUCT = "MOD13A1"
SOIL_MOISTURE_PRODUCT = "SPL3SMP"
NDVI_LAYER_SUFFIX = "_ndvi"
SOIL_MOISTURE_LAYERS = ("_soil_moisture", "_soil_moisture_pm")
# MODIS and SMAP products lag real time by a couple of weeks.
DATA_LAG_DAYS = 21

_layer_cache = TTLCache(ttl_seconds=7 * 24 * 3600)
_satellite_cache = TTLCache()


class AppEEARSError(Exception):
    pass


def date_window() -> tuple[date, date]:
    end = date.today() - timedelta(days=DATA_LAG_DAYS)
    start = end - timedelta(days=365 * get_settings().default_years)
    return start, end


def cache_key(lat: float, lon: float) -> tuple:
    start, end = date_window()
    return (round(lat, 3), round(lon, 3), start.isoformat(), end.isoformat())


def get_cached_satellite_data(lat: float, lon: float) -> SatelliteData | None:
    return _satellite_cache.get(cache_key(lat, lon))


def cache_satellite_data(lat: float, lon: float, data: SatelliteData) -> None:
    _satellite_cache.set(cache_key(lat, lon), data)


async def _request(method: str, path: str, **kwargs) -> httpx.Response:
    response: httpx.Response | None = None
    for attempt in range(2):
        token = await get_token(force_refresh=attempt > 0)
        try:
            async with httpx.AsyncClient(timeout=60, follow_redirects=True) as client:
                response = await client.request(
                    method, f"{BASE_URL}{path}", headers={"Authorization": f"Bearer {token}"}, **kwargs
                )
        except httpx.HTTPError as exc:
            raise AppEEARSError(f"AppEEARS request failed: {exc}") from exc
        if response.status_code != 403:
            break
    assert response is not None
    if response.status_code >= 400:
        raise AppEEARSError(f"AppEEARS returned HTTP {response.status_code}: {response.text[:200]}")
    return response


async def _latest_product_id(client: httpx.AsyncClient, product: str) -> str:
    response = await client.get(f"{BASE_URL}/product")
    response.raise_for_status()
    versions = [
        p["Version"]
        for p in response.json()
        if p["Product"] == product and p.get("Available") and not p.get("Deleted")
    ]
    if not versions:
        raise AppEEARSError(f"AppEEARS product {product} is not available")
    return f"{product}.{max(versions)}"


async def resolve_layers() -> list[dict[str, str]]:
    cached = _layer_cache.get("layers")
    if cached is not None:
        return cached

    layers: list[dict[str, str]] = []
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            for product, suffixes in (
                (NDVI_PRODUCT, (NDVI_LAYER_SUFFIX,)),
                (SOIL_MOISTURE_PRODUCT, SOIL_MOISTURE_LAYERS),
            ):
                product_id = await _latest_product_id(client, product)
                response = await client.get(f"{BASE_URL}/product/{product_id}")
                response.raise_for_status()
                names = [n for n in response.json() if n.lower().endswith(suffixes)]
                if not names:
                    raise AppEEARSError(f"No usable layers found for {product_id}")
                layers += [{"product": product_id, "layer": n} for n in names]
    except httpx.HTTPError as exc:
        raise AppEEARSError(f"Could not list AppEEARS products: {exc}") from exc

    _layer_cache.set("layers", layers)
    return layers


async def submit_point_task(lat: float, lon: float) -> str:
    start, end = date_window()
    body = {
        "task_type": "point",
        "task_name": f"crop-rotation-{lat:.3f}-{lon:.3f}",
        "params": {
            "dates": [{"startDate": start.strftime("%m-%d-%Y"), "endDate": end.strftime("%m-%d-%Y")}],
            "layers": await resolve_layers(),
            "coordinates": [{"latitude": lat, "longitude": lon, "id": "farm"}],
        },
    }
    response = await _request("POST", "/task", json=body)
    return response.json()["task_id"]


async def get_task_status(task_id: str) -> str:
    response = await _request("GET", f"/task/{task_id}")
    return response.json()["status"]


async def download_results(task_id: str) -> SatelliteData:
    bundle = (await _request("GET", f"/bundle/{task_id}")).json()
    csv_files = [f for f in bundle["files"] if f["file_name"].endswith("-results.csv")]
    texts = [(await _request("GET", f"/bundle/{task_id}/{f['file_id']}")).text for f in csv_files]
    return parse_results_csvs(texts)
