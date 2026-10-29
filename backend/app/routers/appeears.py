from fastapi import APIRouter, HTTPException

from app.models.schemas import JobResponse
from app.services import jobs

router = APIRouter()


@router.get("/tasks/{job_id}", response_model=JobResponse)
async def get_task(job_id: str) -> JobResponse:
    job = jobs.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Unknown or expired analysis job")
    await jobs.refresh_job(job)
    return jobs.to_response(job)
