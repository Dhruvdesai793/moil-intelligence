from datetime import datetime
from enum import StrEnum

from pydantic import Field

from app.schemas.common import Metadata, utc_now
from app.schemas.prediction import ModelResult, Uncertainty


class Risk(StrEnum):
    HIGH = "HIGH"
    LOW = "LOW"
    UNKNOWN = "UNKNOWN"


class ProductionOverview(Metadata):
    target: float
    predicted: float | None
    unit: str = "demo_tonnes"
    shortfall_probability: float | None = Field(ge=0, le=1)
    risk: Risk
    status: str = "stub"
    model_version: str
    data_timestamp: datetime | None = None
    feature_version: str = "placeholder-v1"
    prediction_timestamp: datetime = Field(default_factory=utc_now)
    uncertainty: Uncertainty = Field(default_factory=Uncertainty)
    model: ModelResult
