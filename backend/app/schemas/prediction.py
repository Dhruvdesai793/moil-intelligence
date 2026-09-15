from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from app.schemas.common import Metadata, Readiness, utc_now


class Coordinates(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


class ExplorationPredictionRequest(BaseModel):
    site_id: str | None = Field(default=None, min_length=1)
    coordinates: Coordinates | None = None
    requested_resolution_m: float | None = Field(default=None, gt=0)
    as_of: datetime | None = None
    allow_demo_features: bool = False

    @model_validator(mode="after")
    def validate_origin(self):
        if (self.site_id is None) == (self.coordinates is None):
            raise ValueError("Provide exactly one of site_id or coordinates.")
        if self.as_of is not None and self.as_of.utcoffset() is None:
            raise ValueError("as_of must include a timezone.")
        if self.as_of is not None and self.as_of > utc_now():
            raise ValueError("as_of cannot be in the future.")
        return self


class Uncertainty(BaseModel):
    method: str = "not_calibrated"
    lower: float | None = None
    upper: float | None = None
    message: str = "No validated interval or probability calibration is available."


class ModelResult(BaseModel):
    model_name: str
    model_version: str = "stub-v1"
    value: float | None = None
    is_stub: bool = True
    readiness: Readiness = Readiness.STUB
    warning: str = "Deterministic software fixture, not a trained model."


class ExplorationPrediction(Metadata):
    prediction_id: str
    site_id: str | None
    coordinates: Coordinates
    prospectivity_score: float | None = Field(default=None, ge=0, le=1)
    score_type: Literal["demo_ranking_score"] = "demo_ranking_score"
    status: Literal["stub", "insufficient_real_data"] = "stub"
    model_version: str
    data_timestamp: datetime | None = None
    feature_version: str = "placeholder-v1"
    prediction_timestamp: datetime = Field(default_factory=utc_now)
    as_of: datetime
    requested_resolution_m: float | None = None
    effective_resolution_m: float | None = None
    uncertainty: Uncertainty = Field(default_factory=Uncertainty)
    models: list[ModelResult]
