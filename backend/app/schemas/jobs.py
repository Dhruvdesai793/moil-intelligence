from enum import StrEnum
from typing import Literal
from app.schemas.common import Metadata
from app.schemas.prediction import ExplorationPrediction, ExplorationPredictionRequest
from app.schemas.features import FeatureBundle, FeatureExtractionRequest


class JobStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class JobRequest(ExplorationPredictionRequest):
    task: Literal["exploration_prediction"] = "exploration_prediction"
    complete_immediately: bool = True


class ExtractionJobRequest(FeatureExtractionRequest):
    task: Literal["feature_extraction"] = "feature_extraction"


class JobRecord(Metadata):
    job_id: str
    status: JobStatus
    request: JobRequest | ExtractionJobRequest
    result: ExplorationPrediction | FeatureBundle | None = None
    error: str | None = None
