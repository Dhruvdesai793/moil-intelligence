from pydantic import BaseModel, Field
from app.schemas.common import Metadata


class ReferenceMine(BaseModel):
    name: str
    latitude: float
    longitude: float
    coordinate_method: str
    source_url: str
    warning: str = "Historical representative reference point; not a verified current lease boundary."


class StudyArea(BaseModel):
    name: str = "Sausar belt study area"
    bounds: list[float] = [78.5, 21.1, 80.7, 22.3]
    boundary_type: str = "approximate_study_envelope"
    warning: str = "Planning envelope only, not an official geological belt or mineral occurrence boundary."
    mines: list[ReferenceMine]
    source_url: str = "https://doi.org/10.2478/ntpe-2019-0007"


class RankedLocation(BaseModel):
    site_id: str
    name: str
    latitude: float
    longitude: float
    rank: int
    demo_ranking_score: float | None
    feature_id: str | None
    feature_source: str
    feature_readiness: str
    model_version: str
    is_stub: bool = True


class Rankings(Metadata):
    source: str = "stub_model"
    is_stub: bool = True
    score_type: str = "demo_ranking_score"
    warning: str = "Deterministic demo ordering; not manganese likelihood, geological prospectivity or reserves."
    locations: list[RankedLocation] = Field(default_factory=list)


class SpectralReference(Metadata):
    sha256_original: str | None = None
    name: str = "Pyrolusite HS138"
    source: str = "USGS spectral library"
    is_stub: bool = False
    status: str = "reference_not_loaded"
    wavelengths_nm: list[float] = Field(default_factory=list)
    reflectance: list[float] = Field(default_factory=list)
    source_url: str = (
        "https://pubs.usgs.gov/of/2003/ofr-03-395/DESCRIPT/M/pyrolusite_hs138.html"
    )
    warning: str = "Laboratory sample from Colorado, not Sausar ore. Broadband satellite pixels cannot directly identify manganese. No similarity-to-probability conversion."
