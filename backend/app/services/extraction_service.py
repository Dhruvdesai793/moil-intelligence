from uuid import uuid4
from app.schemas.features import FeatureExtractionRequest
from app.schemas.jobs import ExtractionJobRequest, JobRecord, JobStatus


class ExtractionService:
    def __init__(self, features, jobs):
        self.features = features
        self.jobs = jobs

    def queue(self, request: FeatureExtractionRequest):
        if request.site_id:
            self.features.exploration.get_site(request.site_id)
        job = JobRecord(
            job_id=str(uuid4()),
            status=JobStatus.QUEUED,
            request=ExtractionJobRequest(**request.model_dump()),
            source="postgresql",
            is_stub=False,
            message="Extraction queued. The local extraction worker materializes features.",
            warning="Environmental measurements are not validated manganese predictions.",
        )
        return self.jobs.create(job)
