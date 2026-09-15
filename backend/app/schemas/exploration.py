from enum import StrEnum

from pydantic import BaseModel, Field

from app.schemas.common import Metadata, ProviderAvailability


class SiteStatus(StrEnum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    UNDER_REVIEW = "UNDER_REVIEW"


class Site(BaseModel):
    id: str
    name: str
    region: str | None = None
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    status: SiteStatus
    metadata: Metadata = Field(default_factory=Metadata)


class SiteSummary(BaseModel):
    site: Site
    feature_availability: list[ProviderAvailability]
    model_readiness: dict[str, str]
    metadata: Metadata = Field(default_factory=Metadata)
