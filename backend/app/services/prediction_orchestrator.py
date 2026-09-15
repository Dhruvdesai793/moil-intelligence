from uuid import uuid4

from app.ml.base import ModelInput
from app.ml.registry import ModelRegistry
from app.repositories.predictions import PredictionRepository
from app.schemas.common import Readiness, utc_now
from app.schemas.prediction import (
    Coordinates, ExplorationPrediction, ExplorationPredictionRequest, ModelResult,
)
from app.services.exploration_service import ExplorationService


class PredictionOrchestrator:
    def __init__(self, exploration: ExplorationService, registry: ModelRegistry,
                 repository: PredictionRepository):
        self.exploration = exploration
        self.registry = registry
        self.repository = repository

    def exploration_prediction(self, request: ExplorationPredictionRequest) -> ExplorationPrediction:
        coordinates = request.coordinates
        if request.site_id:
            site = self.exploration.get_site(request.site_id)
            coordinates = Coordinates(latitude=site.latitude, longitude=site.longitude)
        inputs = ModelInput(coordinates=coordinates)
        prospectivity = self.registry.run("prospectivity", inputs)
        grade = self.registry.run("grade", inputs)
        result = ExplorationPrediction(
            prediction_id=str(uuid4()), site_id=request.site_id, coordinates=coordinates,
            prospectivity_score=prospectivity.value, model_version=prospectivity.model_version,
            status="stub" if prospectivity.readiness == Readiness.STUB else "insufficient_real_data",
            as_of=request.as_of or utc_now(),
            requested_resolution_m=request.requested_resolution_m,
            models=[prospectivity, grade],
            warning="No real features, calibrated probability, grade or spatial resolution. "
                    "Requested resolution is recorded only, not executed.",
        )
        return self.repository.save(result)

    def production_prediction(self, target: float) -> ModelResult:
        return self.registry.run("production", ModelInput(target=target))
