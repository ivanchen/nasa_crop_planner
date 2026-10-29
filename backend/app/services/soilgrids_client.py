import logging
from datetime import datetime, timezone

import httpx

from app.models.schemas import DataSourceMeta, SoilSummary
from app.services.cache import TTLCache

logger = logging.getLogger(__name__)

SOILGRIDS_URL = "https://rest.isric.org/soilgrids/v2.0/properties/query"
PROPERTIES = ["phh2o", "soc", "sand", "clay", "silt"]
DEPTHS = {"0-5cm": 5, "5-15cm": 10, "15-30cm": 15}
MAX_ATTEMPTS = 2

# Typical Java lowland Inceptisol/Alfisol profile, used when SoilGrids is unreachable.
FALLBACK_SOIL = {"ph": 5.8, "soc_g_kg": 18.0, "sand_pct": 28.0, "clay_pct": 38.0, "silt_pct": 34.0}

_cache = TTLCache()


async def fetch_soil(lat: float, lon: float) -> SoilSummary:
    key = (round(lat, 3), round(lon, 3))
    cached = _cache.get(key)
    if cached is not None:
        return cached.model_copy(update={"meta": cached.meta.model_copy(update={"cached": True})})

    values = await _query_soilgrids(lat, lon)
    if values is None:
        return _build_summary(FALLBACK_SOIL, source="fallback")

    summary = _build_summary(values, source="soilgrids")
    _cache.set(key, summary)
    return summary


async def _query_soilgrids(lat: float, lon: float) -> dict[str, float] | None:
    params = [("lat", lat), ("lon", lon), ("value", "mean")]
    params += [("property", p) for p in PROPERTIES]
    params += [("depth", d) for d in DEPTHS]

    for attempt in range(MAX_ATTEMPTS):
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(SOILGRIDS_URL, params=params)
            if response.status_code != 200:
                logger.warning("SoilGrids returned %s (attempt %s)", response.status_code, attempt + 1)
                continue
            return _parse_layers(response.json())
        except (httpx.HTTPError, ValueError, KeyError) as exc:
            logger.warning("SoilGrids request failed (attempt %s): %s", attempt + 1, exc)
    return None


def _parse_layers(payload: dict) -> dict[str, float] | None:
    averaged: dict[str, float] = {}
    for layer in payload["properties"]["layers"]:
        d_factor = layer.get("unit_measure", {}).get("d_factor") or 1
        weighted_sum = 0.0
        weight_total = 0
        for depth in layer["depths"]:
            mean = depth["values"].get("mean")
            weight = DEPTHS.get(depth["label"].split()[0])
            if mean is None or weight is None:
                continue
            weighted_sum += (mean / d_factor) * weight
            weight_total += weight
        if weight_total:
            averaged[layer["name"]] = weighted_sum / weight_total

    if any(p not in averaged for p in PROPERTIES):
        # SoilGrids masks urban/water pixels with null values.
        return None

    return {
        "ph": averaged["phh2o"],
        "soc_g_kg": averaged["soc"],
        "sand_pct": averaged["sand"],
        "clay_pct": averaged["clay"],
        "silt_pct": averaged["silt"],
    }


def _build_summary(values: dict[str, float], source: str) -> SoilSummary:
    if source == "soilgrids":
        meta = DataSourceMeta(
            source="ISRIC SoilGrids",
            fetched_at=datetime.now(timezone.utc),
            resolution="250 m, depth 0–30 cm",
            disclaimer="modelled_soil",
        )
    else:
        meta = DataSourceMeta(
            source="Typical lowland soil profile (estimate)",
            fetched_at=datetime.now(timezone.utc),
            disclaimer="fallback_soil",
        )
    return SoilSummary(
        meta=meta,
        ph=round(values["ph"], 1),
        soc_g_kg=round(values["soc_g_kg"], 1),
        sand_pct=round(values["sand_pct"], 1),
        clay_pct=round(values["clay_pct"], 1),
        silt_pct=round(values["silt_pct"], 1),
        texture=classify_texture(values["sand_pct"], values["clay_pct"]),
        source=source,
    )


def classify_texture(sand: float, clay: float) -> str:
    silt = 100 - sand - clay
    if clay >= 40:
        return "clay"
    if clay >= 27:
        return "clay loam" if sand < 45 else "sandy clay loam"
    if sand >= 70:
        return "sandy loam" if clay >= 7 else "loamy sand"
    if silt >= 50:
        return "silt loam"
    return "loam"
