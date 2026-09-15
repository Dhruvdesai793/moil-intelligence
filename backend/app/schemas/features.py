from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from app.schemas.common import Metadata, ProviderAvailability, Readiness, utc_now
from app.schemas.prediction import Coordinates


class AOI(BaseModel):
    type: Literal["Polygon"] = "Polygon"
    coordinates: list[list[list[float]]]

    @model_validator(mode="after")
    def validate_polygon(self):
        if not self.coordinates:
            raise ValueError("Polygon needs at least one ring.")
        for ring in self.coordinates:
            if len(ring) < 4 or ring[0] != ring[-1]:
                raise ValueError("Polygon rings must be closed and contain at least four positions.")
            for point in ring:
                if len(point) != 2 or not -180 <= point[0] <= 180 or not -90 <= point[1] <= 90:
                    raise ValueError("AOI positions must be WGS84 [longitude, latitude].")
        return self


class FeatureExtractionRequest(BaseModel):
    site_id: str | None = Field(default=None, min_length=1)
    coordinates: Coordinates | None = None
    aoi: AOI | None = None
    start_date: date
    end_date: date
    allow_demo_fallback: bool = False

    @model_validator(mode="after")
    def validate_request(self):
        if sum(item is not None for item in (self.site_id, self.coordinates, self.aoi)) != 1:
            raise ValueError("Provide exactly one of site_id, coordinates or aoi.")
        if self.start_date >= self.end_date or self.end_date > utc_now().date():
            raise ValueError("Dates require start_date < end_date <= today (end exclusive).")
        return self


class FeatureBundle(Metadata):
    feature_id: str | None = None
    site_id: str | None = None
    coordinates: Coordinates | None = None
    aoi: AOI | None = None
    feature_version: str = "unavailable"
    feature_payload: dict[str, float | str | None] = Field(default_factory=dict)
    start_date: date | None = None
    end_date: date | None = None
    extracted_at: datetime | None = None
    readiness: Readiness = Readiness.NOT_CONFIGURED
    source: str = "none"
    is_stub: bool = False
    message: str = "No features extracted."


class FeatureAvailability(BaseModel):
    site_id: str
    provider: ProviderAvailability
    latest_feature: FeatureBundle | None = None
