from typing import Protocol

from pydantic import BaseModel

from app.schemas.prediction import Coordinates, ModelResult


class ModelInput(BaseModel):
    coordinates: Coordinates | None = None
    target: float | None = None


class ModelAdapter(Protocol):
    name: str

    def predict(self, inputs: ModelInput) -> ModelResult: ...
