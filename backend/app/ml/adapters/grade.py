from app.ml.base import ModelInput
from app.schemas.common import Readiness
from app.schemas.prediction import ModelResult


class GradeAdapter:
    name = "grade"

    def predict(self, inputs: ModelInput) -> ModelResult:
        return ModelResult(model_name=self.name, value=None,
                           readiness=Readiness.NOT_CONFIGURED,
                           warning="No assay data or validated grade model; grade withheld.")
