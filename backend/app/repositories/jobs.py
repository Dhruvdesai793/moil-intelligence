from collections import OrderedDict
from threading import Lock

from app.schemas.jobs import JobRecord


class JobRepository:
    def __init__(self):
        self._records: OrderedDict[str, JobRecord] = OrderedDict()
        self._lock = Lock()

    def save(self, job: JobRecord) -> JobRecord:
        with self._lock:
            self._records[job.job_id] = job.model_copy(deep=True)
            if len(self._records) > 1000:
                self._records.popitem(last=False)
        return job

    def get(self, job_id: str) -> JobRecord | None:
        with self._lock:
            job = self._records.get(job_id)
            return job.model_copy(deep=True) if job else None
