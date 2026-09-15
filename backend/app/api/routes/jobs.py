from fastapi import APIRouter, Depends

from app.api.dependencies import get_jobs
from app.schemas.jobs import JobRecord, JobRequest
from app.services.job_service import JobService

router = APIRouter(prefix="/jobs", tags=["Jobs"])


@router.post("", response_model=JobRecord, status_code=201)
def create_job(request: JobRequest, service: JobService = Depends(get_jobs)) -> JobRecord:
    return service.create(request)


@router.get("/{job_id}", response_model=JobRecord)
def get_job(job_id: str, service: JobService = Depends(get_jobs)) -> JobRecord:
    return service.get(job_id)
