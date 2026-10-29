import csv
import io
import re
import statistics
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone

from app.models.schemas import DataSourceMeta, MoistureSummary, SeriesPoint, VegetationSummary

NDVI_RANGE = (-0.2, 1.0)
MOISTURE_RANGE = (0.0, 0.8)
NDVI_TREND_THRESHOLD_PER_YEAR = 0.015
MOISTURE_CV_MODERATE = 0.15
MOISTURE_CV_HIGH = 0.30
SOIL_MOISTURE_COLUMN = re.compile(r"soil_moisture(_pm)?$", re.IGNORECASE)

Point = tuple[str, float]


@dataclass
class SatelliteData:
    ndvi: list[Point] = field(default_factory=list)
    moisture: list[Point] = field(default_factory=list)
    fetched_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


def parse_results_csvs(csv_texts: list[str]) -> SatelliteData:
    data = SatelliteData()
    for text in csv_texts:
        reader = csv.DictReader(io.StringIO(text))
        for row in reader:
            date = (row.get("Date") or "")[:10]
            if not date:
                continue
            for column, raw in row.items():
                if column is None:
                    continue
                value = _to_float(raw)
                if value is None:
                    continue
                if column.upper().endswith("NDVI") and NDVI_RANGE[0] <= value <= NDVI_RANGE[1]:
                    data.ndvi.append((date, value))
                elif SOIL_MOISTURE_COLUMN.search(column) and MOISTURE_RANGE[0] <= value <= MOISTURE_RANGE[1]:
                    data.moisture.append((date, value))
    return data


def _to_float(raw: str | None) -> float | None:
    try:
        return float(raw) if raw not in (None, "") else None
    except ValueError:
        return None


def monthly_means(points: list[Point]) -> list[SeriesPoint]:
    buckets: dict[str, list[float]] = defaultdict(list)
    for date, value in points:
        buckets[date[:7]].append(value)
    return [SeriesPoint(date=month, value=round(statistics.fmean(vals), 3)) for month, vals in sorted(buckets.items())]


def _meta(source: str, resolution: str, points: list[Point], fetched_at: datetime, cached: bool) -> DataSourceMeta:
    dates = [d for d, _ in points]
    return DataSourceMeta(
        source=source,
        fetched_at=fetched_at,
        period_start=min(dates),
        period_end=max(dates),
        resolution=resolution,
        cached=cached,
        disclaimer="coarse_resolution",
    )


def summarize_vegetation(points: list[Point], fetched_at: datetime, cached: bool = False) -> VegetationSummary | None:
    series = monthly_means(points)
    if len(series) < 6:
        return None
    slope_per_year = _slope_per_year([p.value for p in series])
    if slope_per_year <= -NDVI_TREND_THRESHOLD_PER_YEAR:
        trend = "declining"
    elif slope_per_year >= NDVI_TREND_THRESHOLD_PER_YEAR:
        trend = "improving"
    else:
        trend = "stable"
    return VegetationSummary(
        mean_ndvi=round(statistics.fmean(p.value for p in series), 3),
        trend=trend,
        series=series,
        meta=_meta("NASA MODIS MOD13A1 NDVI", "500 m, 16-day composite", points, fetched_at, cached),
    )


def summarize_moisture(points: list[Point], fetched_at: datetime, cached: bool = False) -> MoistureSummary | None:
    series = monthly_means(points)
    if len(series) < 6:
        return None
    values = [v for _, v in points]
    mean = statistics.fmean(values)
    cv = statistics.pstdev(values) / mean if mean > 0 else 0.0
    if cv >= MOISTURE_CV_HIGH:
        variability = "high"
    elif cv >= MOISTURE_CV_MODERATE:
        variability = "moderate"
    else:
        variability = "low"
    return MoistureSummary(
        mean_volumetric=round(mean, 3),
        variability=variability,
        series=series,
        meta=_meta("NASA SMAP SPL3SMP soil moisture", "36 km, daily (surface layer)", points, fetched_at, cached),
    )


def _slope_per_year(monthly_values: list[float]) -> float:
    n = len(monthly_values)
    xs = [i / 12 for i in range(n)]
    mean_x = statistics.fmean(xs)
    mean_y = statistics.fmean(monthly_values)
    denominator = sum((x - mean_x) ** 2 for x in xs)
    return sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, monthly_values)) / denominator
