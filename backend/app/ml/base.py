from typing import Protocol
from app.schemas.ml import ModelInput as ModelInput
from app.schemas.prediction import ModelResult


class ModelAdapter(Protocol):
    name: str

    def predict(self, inputs: ModelInput) -> ModelResult: ...
