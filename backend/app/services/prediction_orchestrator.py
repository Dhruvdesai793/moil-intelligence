from uuid import uuid4

from app.ml.base import ModelInput
from app.core.exceptions import NotFoundError
from app.ml.registry import ModelRegistry
from app.repositories.predictions import PredictionRepository
from app.schemas.common import Readiness, utc_now
from app.schemas.prediction import (
    Coordinates, ExplorationPrediction, ExplorationPredictionRequest, ModelResult,
)
from app.services.exploration_service import ExplorationService
from app.services.feature_service import FeatureService
from app.schemas.features import FeatureExtractionRequest
from datetime import timedelta


class PredictionOrchestrator:
    def __init__(self, exploration: ExplorationService, registry: ModelRegistry,
                 repository: PredictionRepository, features: FeatureService):
        self.exploration = exploration
        self.registry = registry
        self.repository = repository
        self.features = features

    def exploration_prediction(self, request: ExplorationPredictionRequest) -> ExplorationPrediction:
        coordinates = request.coordinates
        if request.site_id:
            site = self.exploration.get_site(request.site_id)
            coordinates = Coordinates(latitude=site.latitude, longitude=site.longitude)
        as_of = request.as_of or utc_now()
        bundle = self.features.latest(request.site_id, as_of)
        if bundle is None and request.allow_demo_features and request.as_of is None:
            bundle = self.features.extract(FeatureExtractionRequest(
                site_id=request.site_id,
                coordinates=coordinates if request.site_id is None else None,
                start_date=(as_of - timedelta(days=30)).date(), end_date=as_of.date(),
                allow_demo_fallback=True))
        if bundle is not None and bundle.readiness not in (Readiness.OK, Readiness.STUB):
            bundle = None
        if request.as_of is None:
            as_of = utc_now()
        # Stub adapters do not interpret unvalidated environmental features.
        inputs = ModelInput(coordinates=coordinates)
        prospectivity = self.registry.run("prospectivity", inputs)
        grade = self.registry.run("grade", inputs)
        result = ExplorationPrediction(
            prediction_id=str(uuid4()), site_id=request.site_id, coordinates=coordinates,
            prospectivity_score=prospectivity.value, model_version=prospectivity.model_version,
            status="insufficient_real_data",
            as_of=as_of,
            source="stub_models",
            feature_version=bundle.feature_version if bundle else "unavailable",
            data_timestamp=bundle.extracted_at if bundle else None,
            requested_resolution_m=request.requested_resolution_m,
            models=[prospectivity, grade],
            warning="Stub models only; stored features are provenance, not validated model inputs. "
                    "No calibrated probability, geological validity or executed spatial resolution.",
        )
        return self.repository.save(result)

    def production_prediction(self, target: float) -> ModelResult:
        return self.registry.run("production", ModelInput(target=target))

    def get_prediction(self, prediction_id: str) -> ExplorationPrediction:
        result = self.repository.get(prediction_id)
        if result is None:
            raise NotFoundError(f"Prediction '{prediction_id}' was not found.")
        return result
