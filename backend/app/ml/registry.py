import logging

from app.ml.adapters.grade import GradeAdapter
from app.ml.adapters.production import ProductionAdapter
from app.ml.adapters.prospectivity import ProspectivityAdapter
from app.ml.base import ModelAdapter, ModelInput
from app.schemas.common import Readiness
from app.schemas.prediction import ModelResult


class ModelRegistry:
    def __init__(self, adapters: dict[str, ModelAdapter] | None = None):
        self.adapters = adapters if adapters is not None else {
            "prospectivity": ProspectivityAdapter(),
            "grade": GradeAdapter(),
            "production": ProductionAdapter(),
        }

    def run(self, name: str, inputs: ModelInput) -> ModelResult:
        adapter = self.adapters.get(name)
        if adapter is not None:
            try:
                return adapter.predict(inputs)
            except Exception:
                logging.getLogger("moil.models").exception("Adapter unavailable: %s", name)
        return ModelResult(model_name=name, model_version="unavailable",
                           readiness=Readiness.UNAVAILABLE,
                           warning="Adapter absent or failed; output withheld.")
