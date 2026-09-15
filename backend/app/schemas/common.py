from datetime import datetime, timezone
from enum import StrEnum

from pydantic import BaseModel, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Readiness(StrEnum):
    STUB = "stub"
    NOT_CONFIGURED = "not_configured"
    UNAVAILABLE = "unavailable"


class Metadata(BaseModel):
    source: str = "demo_in_memory"
    is_stub: bool = True
    generated_at: datetime = Field(default_factory=utc_now)
    message: str = "Demo only; not scientifically validated."
    warning: str | None = "Real data, GEE and model integration pending."


class HealthResponse(BaseModel):
    status: str = "ok"
    service: str = "MOIL Intelligence API"
    version: str = "0.1.0"


class ErrorDetail(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    error: ErrorDetail


class ProviderAvailability(BaseModel):
    provider: str
    readiness: Readiness = Readiness.NOT_CONFIGURED
    features: list[str]
    metadata: Metadata = Field(default_factory=Metadata)
