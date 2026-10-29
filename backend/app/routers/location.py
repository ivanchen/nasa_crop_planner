import asyncio

from fastapi import APIRouter, HTTPException

from app.models.schemas import AnalyzeRequest, JobResponse
from app.services import jobs
from app.services.power_client import ClimateUnavailableError, fetch_climate
from app.services.soilgrids_client import fetch_soil

router = APIRouter()


@router.post("/analyze", response_model=JobResponse)
async def analyze(request: AnalyzeRequest) -> JobResponse:
    try:
        climate, soil = await asyncio.gather(
            fetch_climate(request.lat, request.lon), fetch_soil(request.lat, request.lon)
        )
    except ClimateUnavailableError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    job = await jobs.start_job(request, climate, soil)
    return jobs.to_response(job)
