from pydantic import BaseModel, Field
from app.schemas.prediction import Coordinates
from app.schemas.features import FeatureBundle


class ModelInput(BaseModel):
    contract_version: str = "exploration-model-input-v1"
    site_id: str | None = None
    coordinates: Coordinates | None = None
    target: float | None = None
    features: FeatureBundle | None = None
    missing_inputs: list[str] = Field(
        default_factory=lambda: [
            "validated_geology",
            "drilling_assays",
            "trained_model",
        ]
    )
    warning: str = (
        "Environmental features alone do not establish manganese presence or reserves."
    )
