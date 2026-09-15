from uuid import uuid4

from app.core.exceptions import NotFoundError
from app.repositories.jobs import JobRepository
from app.schemas.jobs import JobRecord, JobRequest, JobStatus
from app.schemas.prediction import ExplorationPredictionRequest
from app.services.prediction_orchestrator import PredictionOrchestrator


class JobService:
    def __init__(self, repository: JobRepository, orchestrator: PredictionOrchestrator):
        self.repository = repository
        self.orchestrator = orchestrator

    def create(self, request: JobRequest) -> JobRecord:
        job = JobRecord(job_id=str(uuid4()), status=JobStatus.QUEUED, request=request,
                        warning="In-memory demo; queued jobs have no worker and never advance. "
                                "Records reset on restart and oldest records expire after 1000 jobs.")
        if request.complete_immediately:
            prediction_request = ExplorationPredictionRequest.model_validate(
                request.model_dump(exclude={"task", "complete_immediately"}))
            job.result = self.orchestrator.exploration_prediction(prediction_request)
            job.status = JobStatus.COMPLETED
        return self.repository.save(job)

    def get(self, job_id: str) -> JobRecord:
        job = self.repository.get(job_id)
        if job is None:
            raise NotFoundError(f"Job '{job_id}' was not found or has expired.")
        return job
