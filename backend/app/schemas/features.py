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
        if not self.coordinates or len(self.coordinates) > 5:
            raise ValueError("Polygon requires one to five closed rings.")
        for ring in self.coordinates:
            if len(ring) < 4 or len(ring) > 100 or ring[0] != ring[-1]:
                raise ValueError("Rings must be closed, with 4 to 100 positions.")
            for point in ring:
                if (
                    len(point) != 2
                    or not 78.5 <= point[0] <= 80.7
                    or not 21.1 <= point[1] <= 22.3
                ):
                    raise ValueError(
                        "AOI must be within the approximate Sausar study envelope."
                    )
        xs = [p[0] for p in self.coordinates[0]]
        ys = [p[1] for p in self.coordinates[0]]
        if (max(xs) - min(xs)) * (max(ys) - min(ys)) > 0.01:
            raise ValueError(
                "AOI bounding box exceeds the local extraction budget (~100 km2)."
            )
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
        if (
            sum(item is not None for item in (self.site_id, self.coordinates, self.aoi))
            != 1
        ):
            raise ValueError("Provide exactly one of site_id, coordinates or aoi.")
        if self.start_date >= self.end_date or self.end_date > utc_now().date():
            raise ValueError(
                "Dates require start_date < end_date <= today (end exclusive)."
            )
        if (self.end_date - self.start_date).days > 366:
            raise ValueError("Local extraction is limited to 366 days.")
        if self.coordinates and not (
            21.1 <= self.coordinates.latitude <= 22.3
            and 78.5 <= self.coordinates.longitude <= 80.7
        ):
            raise ValueError(
                "Coordinates must be within the approximate Sausar study envelope."
            )
        return self


class SpectralBand(BaseModel):
    band: str
    wavelength_nm: float
    reflectance: float | None
    native_resolution_m: int
    wavelength_note: str = "Approximate Sentinel-2A band center; broadband observation."


class ProductQuality(BaseModel):
    collection: str
    status: str
    scene_count: int = 0
    native_resolution_m: float
    units: str
    valid_fraction: float | None = None
    latest_observation: str | None = None
    warning: str | None = None


class FeatureBundle(Metadata):
    feature_id: str | None = None
    site_id: str | None = None
    coordinates: Coordinates | None = None
    aoi: AOI | None = None
    feature_version: str = "unavailable"
    feature_payload: dict[str, float | str | None] = Field(default_factory=dict)
    spectral_bands: list[SpectralBand] = Field(default_factory=list)
    quality: dict[str, ProductQuality] = Field(default_factory=dict)
    extraction_method: str | None = None
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
