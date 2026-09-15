from enum import StrEnum

from pydantic import BaseModel, Field, field_validator

from app.schemas.common import Metadata, ProviderAvailability


class SiteStatus(StrEnum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    UNDER_REVIEW = "UNDER_REVIEW"


class Site(BaseModel):
    id: str
    name: str
    region: str | None = None
    origin: str = "demo_fixture"
    notes: str | None = None
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    status: SiteStatus
    metadata: Metadata = Field(default_factory=Metadata)


class SiteSummary(BaseModel):
    site: Site
    feature_availability: list[ProviderAvailability]
    model_readiness: dict[str, str]
    metadata: Metadata = Field(default_factory=Metadata)


class SiteCreate(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    latitude: float = Field(ge=21.1, le=22.3)
    longitude: float = Field(ge=78.5, le=80.7)
    region: str = Field(default="Sausar study area", max_length=100)
    notes: str | None = Field(default=None, max_length=2000)

    @field_validator("name")
    @classmethod
    def clean_name(cls, value):
        value = value.strip()
        if len(value) < 2:
            raise ValueError("Name must contain at least two non-space characters.")
        return value
