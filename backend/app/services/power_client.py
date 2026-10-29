from collections import defaultdict
from datetime import date, datetime, timezone

import httpx

from app.config import get_settings
from app.models.schemas import ClimateSummary, DataSourceMeta, MonthlyClimate
from app.services.cache import TTLCache

POWER_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"
PARAMETERS = "T2M,T2M_MAX,T2M_MIN,PRECTOTCORR,ALLSKY_SFC_SW_DWN"
FILL_VALUE = -999
DRY_MONTH_RAINFALL_MM = 100

_cache = TTLCache()


class ClimateUnavailableError(Exception):
    pass


async def fetch_climate(lat: float, lon: float) -> ClimateSummary:
    years = get_settings().default_years
    last_full_year = date.today().year - 1
    first_year = last_full_year - years + 1
    key = (round(lat, 2), round(lon, 2), first_year, last_full_year)

    cached = _cache.get(key)
    if cached is not None:
        return cached.model_copy(update={"meta": cached.meta.model_copy(update={"cached": True})})

    params = {
        "parameters": PARAMETERS,
        "community": "AG",
        "longitude": lon,
        "latitude": lat,
        "start": f"{first_year}0101",
        "end": f"{last_full_year}1231",
        "format": "JSON",
    }
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.get(POWER_URL, params=params)
            response.raise_for_status()
            payload = response.json()
        parameters = payload["properties"]["parameter"]
    except (httpx.HTTPError, KeyError, ValueError) as exc:
        raise ClimateUnavailableError(f"NASA POWER request failed: {exc}") from exc

    summary = summarize_climate(parameters, years, first_year, last_full_year)
    _cache.set(key, summary)
    return summary


def _valid(values: dict[str, float]) -> dict[str, float]:
    return {day: v for day, v in values.items() if v is not None and v != FILL_VALUE}


def summarize_climate(
    parameters: dict[str, dict[str, float]], years: int, first_year: int, last_year: int
) -> ClimateSummary:
    temp = _valid(parameters["T2M"])
    temp_max = _valid(parameters["T2M_MAX"])
    temp_min = _valid(parameters["T2M_MIN"])
    rain = _valid(parameters["PRECTOTCORR"])
    solar = _valid(parameters["ALLSKY_SFC_SW_DWN"])

    if not temp or not rain:
        raise ClimateUnavailableError("NASA POWER returned no data for this location")

    monthly_temp: dict[int, list[float]] = defaultdict(list)
    for day, value in temp.items():
        monthly_temp[int(day[4:6])].append(value)

    rain_by_year_month: dict[tuple[int, int], float] = defaultdict(float)
    for day, value in rain.items():
        rain_by_year_month[(int(day[:4]), int(day[4:6]))] += value

    monthly_rain: dict[int, list[float]] = defaultdict(list)
    for (_, month), total in rain_by_year_month.items():
        monthly_rain[month].append(total)

    monthly = [
        MonthlyClimate(
            month=m,
            temp_c=round(_mean(monthly_temp[m]), 1),
            rainfall_mm=round(_mean(monthly_rain[m]), 1),
        )
        for m in range(1, 13)
    ]

    return ClimateSummary(
        mean_temp_c=round(_mean(list(temp.values())), 1),
        min_temp_c=round(_mean(list(temp_min.values())), 1),
        max_temp_c=round(_mean(list(temp_max.values())), 1),
        annual_rainfall_mm=round(sum(m.rainfall_mm for m in monthly)),
        dry_months=sum(1 for m in monthly if m.rainfall_mm < DRY_MONTH_RAINFALL_MM),
        mean_solar_mj_m2_day=round(_mean(list(solar.values())), 1),
        monthly=monthly,
        years=years,
        meta=DataSourceMeta(
            source="NASA POWER",
            fetched_at=datetime.now(timezone.utc),
            period_start=f"{first_year}-01-01",
            period_end=f"{last_year}-12-31",
            resolution="0.5° × 0.625° grid (~50 km)",
            disclaimer="coarse_resolution",
        ),
    )


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0
