from hashlib import sha256

from app.ml.base import ModelInput
from app.schemas.prediction import ModelResult


class ProspectivityAdapter:
    name = "prospectivity"

    def predict(self, inputs: ModelInput) -> ModelResult:
        key = inputs.coordinates.model_dump_json() if inputs.coordinates else "demo"
        number = int.from_bytes(sha256(key.encode()).digest()[:4], "big")
        return ModelResult(model_name=self.name, value=round((number % 1001) / 1000, 3))
