from enum import StrEnum

from pydantic import BaseModel

from app.schemas.common import Metadata


class Priority(StrEnum):
    HIGH = "HIGH"
    NORMAL = "NORMAL"


class Recommendation(BaseModel):
    priority: Priority
    actions: list[str]
    drivers: list[str]
    evidence_status: str = "stub_rule_supported_only"
    status: str = "human_review_required"


class Recommendations(Metadata):
    recommendations: list[Recommendation]
