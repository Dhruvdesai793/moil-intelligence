from uuid import uuid4

from app.ml.base import ModelInput
from app.core.exceptions import NotFoundError
from app.ml.registry import ModelRegistry
from app.repositories.predictions import PredictionRepository
from app.schemas.common import Readiness, utc_now
from app.schemas.intelligence import RankedLocation, Rankings
from app.schemas.prediction import (
    Coordinates,
    ExplorationPrediction,
    ExplorationPredictionRequest,
    ModelResult,
)
from app.services.exploration_service import ExplorationService
from app.services.feature_service import FeatureService


class PredictionOrchestrator:
    def __init__(
        self,
        exploration: ExplorationService,
        registry: ModelRegistry,
        repository: PredictionRepository,
        features: FeatureService,
    ):
        self.exploration = exploration
        self.registry = registry
        self.repository = repository
        self.features = features

    def model_input_for_site(self, site_id, as_of=None) -> ModelInput:
        site = self.exploration.get_site(site_id)
        bundle = self.features.latest(site_id, as_of or utc_now())
        if bundle is not None and bundle.readiness not in (
            Readiness.OK,
            Readiness.STUB,
        ):
            bundle = None
        return ModelInput(
            site_id=site_id,
            coordinates=Coordinates(latitude=site.latitude, longitude=site.longitude),
            features=bundle,
        )

    def rankings(self) -> Rankings:
        values = []
        for site in self.exploration.get_sites():
            inputs = self.model_input_for_site(site.id)
            model = self.registry.run("prospectivity", inputs)
            bundle = inputs.features
            values.append(
                RankedLocation(
                    site_id=site.id,
                    name=site.name,
                    latitude=site.latitude,
                    longitude=site.longitude,
                    rank=0,
                    demo_ranking_score=model.value,
                    model_version=model.model_version,
                    feature_id=bundle.feature_id if bundle else None,
                    feature_source=bundle.source if bundle else "none",
                    feature_readiness=bundle.readiness.value
                    if bundle
                    else "not_extracted",
                )
            )
        values.sort(
            key=lambda v: (
                v.demo_ranking_score is None,
                -(v.demo_ranking_score or 0),
                v.site_id,
            )
        )
        for i, value in enumerate(values, 1):
            value.rank = i
        return Rankings(locations=values)

    def exploration_prediction(
        self, request: ExplorationPredictionRequest
    ) -> ExplorationPrediction:
        as_of = request.as_of or utc_now()
        inputs = (
            self.model_input_for_site(request.site_id, as_of)
            if request.site_id
            else ModelInput(coordinates=request.coordinates)
        )
        coordinates, bundle = inputs.coordinates, inputs.features
        if request.as_of is None:
            as_of = utc_now()
        # Handoff includes measured data, but stub adapters make no geological interpretation.
        prospectivity = self.registry.run("prospectivity", inputs)
        grade = self.registry.run("grade", inputs)
        result = ExplorationPrediction(
            prediction_id=str(uuid4()),
            site_id=request.site_id,
            coordinates=coordinates,
            prospectivity_score=prospectivity.value,
            model_version=prospectivity.model_version,
            status="insufficient_real_data",
            as_of=as_of,
            source="stub_models",
            feature_version=bundle.feature_version if bundle else "unavailable",
            feature_id=bundle.feature_id if bundle else None,
            data_timestamp=bundle.extracted_at if bundle else None,
            requested_resolution_m=request.requested_resolution_m,
            models=[prospectivity, grade],
            warning="Stub models only; measured features are supplied through the model input contract, not validated scientifically. "
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
