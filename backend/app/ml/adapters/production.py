from app.ml.base import ModelInput
from app.schemas.prediction import ModelResult


class ProductionAdapter:
    name = "production"

    def predict(self, inputs: ModelInput) -> ModelResult:
        value = round(inputs.target * 0.86, 2) if inputs.target is not None else None
        return ModelResult(model_name=self.name, value=value)
