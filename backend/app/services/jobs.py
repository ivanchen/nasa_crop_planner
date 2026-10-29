import asyncio
import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone

from app.config import get_settings
from app.models.schemas import (
    AnalyzeRequest,
    ClimateSummary,
    JobResponse,
    Location,
    MoistureSummary,
    Priorities,
    Recommendation,
    SoilSummary,
    VegetationSummary,
)
from app.services import appeears_client
from app.services.appeears_client import AppEEARSError
from app.services.earthdata_auth import EarthdataAuthError
from app.services.rotation_engine import recommend
from app.services.satellite_summary import SatelliteData, summarize_moisture, summarize_vegetation

logger = logging.getLogger(__name__)

JOB_RETENTION_SECONDS = 24 * 3600
FAILED_APPEEARS_STATUSES = {"error", "failed", "deleted"}


@dataclass
class Job:
    id: str
    location: Location
    priorities: Priorities
    climate: ClimateSummary
    soil: SoilSummary
    created_at: float = field(default_factory=time.monotonic)
    appeears_task_id: str | None = None
    appeears_status: str = "pending"
    done: bool = False
    analyzed_at: datetime | None = None
    vegetation: VegetationSummary | None = None
    moisture: MoistureSummary | None = None
    recommendations: list[Recommendation] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)


_jobs: dict[str, Job] = {}


def get_job(job_id: str) -> Job | None:
    return _jobs.get(job_id)


def _purge_old_jobs() -> None:
    cutoff = time.monotonic() - JOB_RETENTION_SECONDS
    for job_id in [j.id for j in _jobs.values() if j.created_at < cutoff]:
        del _jobs[job_id]


def to_response(job: Job) -> JobResponse:
    if job.done:
        progress = "Analysis complete."
    else:
        progress = f"Fetching satellite vegetation and soil moisture data (AppEEARS status: {job.appeears_status})."
    return JobResponse(
        job_id=job.id,
        status="done" if job.done else "processing",
        progress=progress,
        analyzed_at=job.analyzed_at,
        location=job.location,
        priorities=job.priorities,
        climate=job.climate,
        soil=job.soil,
        vegetation=job.vegetation,
        moisture=job.moisture,
        recommendations=job.recommendations,
        warnings=job.warnings,
    )


def _finalize(job: Job, satellite: SatelliteData | None, cached: bool = False) -> None:
    if satellite is not None:
        job.vegetation = summarize_vegetation(satellite.ndvi, satellite.fetched_at, cached)
        job.moisture = summarize_moisture(satellite.moisture, satellite.fetched_at, cached)
        if job.vegetation is None:
            job.warnings.append("Not enough MODIS NDVI observations were found for this location.")
        if job.moisture is None:
            job.warnings.append("Not enough SMAP soil moisture observations were found for this location.")

    if job.soil.source == "fallback":
        job.warnings.append(
            "SoilGrids has no data for this pixel or is unavailable; using a typical lowland soil profile instead."
        )

    job.recommendations = recommend(job.climate, job.soil, job.vegetation, job.moisture, job.priorities)
    if not job.recommendations:
        job.warnings.append("No suitable three-season rotation was found for this climate and soil.")
    job.analyzed_at = datetime.now(timezone.utc)
    job.done = True


async def start_job(request: AnalyzeRequest, climate: ClimateSummary, soil: SoilSummary) -> Job:
    _purge_old_jobs()
    job = Job(
        id=uuid.uuid4().hex,
        location=Location(lat=request.lat, lon=request.lon),
        priorities=request.priorities.normalized(),
        climate=climate,
        soil=soil,
    )
    _jobs[job.id] = job

    cached = appeears_client.get_cached_satellite_data(request.lat, request.lon)
    if cached is not None:
        _finalize(job, cached, cached=True)
    elif not get_settings().earthdata_configured:
        job.warnings.append(
            "Earthdata credentials are not configured, so satellite NDVI and soil moisture were skipped."
        )
        _finalize(job, None)
    else:
        try:
            job.appeears_task_id = await appeears_client.submit_point_task(request.lat, request.lon)
        except (AppEEARSError, EarthdataAuthError) as exc:
            logger.warning("AppEEARS submission failed: %s", exc)
            job.warnings.append(f"Satellite data unavailable: {exc}")
            _finalize(job, None)
    return job


async def refresh_job(job: Job) -> Job:
    if job.done or job.appeears_task_id is None:
        return job

    async with job.lock:
        if job.done:
            return job
        try:
            job.appeears_status = await appeears_client.get_task_status(job.appeears_task_id)
            if job.appeears_status == "done":
                satellite = await appeears_client.download_results(job.appeears_task_id)
                appeears_client.cache_satellite_data(job.location.lat, job.location.lon, satellite)
                _finalize(job, satellite)
            elif job.appeears_status in FAILED_APPEEARS_STATUSES:
                job.warnings.append("The satellite data request failed, so recommendations use climate and soil only.")
                _finalize(job, None)
        except (AppEEARSError, EarthdataAuthError) as exc:
            logger.warning("AppEEARS polling failed: %s", exc)
            if time.monotonic() - job.created_at > get_settings().job_timeout_seconds:
                job.warnings.append(f"Satellite data unavailable: {exc}")
                _finalize(job, None)

        if not job.done and time.monotonic() - job.created_at > get_settings().job_timeout_seconds:
            job.warnings.append("Satellite data took too long, so recommendations use climate and soil only.")
            _finalize(job, None)
    return job
