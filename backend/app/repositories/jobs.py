from sqlalchemy.orm import Session

from app.models.job import Job
from app.schemas.common import utc_now
from app.schemas.jobs import JobRecord


class JobRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, job: JobRecord) -> JobRecord:
        return self.save(job)

    def save(self, job: JobRecord) -> JobRecord:
        row = self.session.get(Job, job.job_id)
        if row is None:
            row = Job(id=job.job_id, job_type=job.request.task, created_at=job.generated_at)
            self.session.add(row)
        row.status = job.status.value
        row.payload = job.model_dump(mode="json")
        row.result = job.result.model_dump(mode="json") if job.result else None
        row.updated_at = utc_now()
        self.session.flush()
        return job

    def get(self, job_id: str) -> JobRecord | None:
        row = self.session.get(Job, job_id)
        return JobRecord.model_validate(row.payload) if row else None

    def update_status(self, job: JobRecord) -> JobRecord:
        return self.save(job)
