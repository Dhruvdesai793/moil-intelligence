from enum import StrEnum
from typing import Literal

from app.schemas.common import Metadata
from app.schemas.prediction import ExplorationPrediction, ExplorationPredictionRequest


class JobStatus(StrEnum):
    QUEUED = "queued"
    COMPLETED = "completed"
    FAILED = "failed"


class JobRequest(ExplorationPredictionRequest):
    task: Literal["exploration_prediction"] = "exploration_prediction"
    complete_immediately: bool = True


class JobRecord(Metadata):
    job_id: str
    status: JobStatus
    request: JobRequest
    result: ExplorationPrediction | None = None
    error: str | None = None
