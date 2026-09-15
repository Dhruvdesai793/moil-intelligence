from uuid import uuid4

from app.core.config import Settings
from app.providers.gee import GEEProvider
from app.repositories.features import FeatureRepository
from app.schemas.common import Readiness, utc_now
from app.schemas.features import FeatureAvailability, FeatureBundle, FeatureExtractionRequest
from app.schemas.prediction import Coordinates
from app.services.exploration_service import ExplorationService


class FeatureService:
    def __init__(self, repository: FeatureRepository, exploration: ExplorationService,
                 provider: GEEProvider, settings: Settings):
        self.repository = repository
        self.exploration = exploration
        self.provider = provider
        self.settings = settings

    def availability(self, site_id: str) -> FeatureAvailability:
        self.exploration.get_site(site_id)
        return FeatureAvailability(site_id=site_id, provider=self.provider.availability(),
                                   latest_feature=self.repository.get_latest_for_site(site_id))

    def latest(self, site_id, as_of=None):
        return self.repository.get_latest_for_site(site_id, as_of) if site_id else None

    def list_for_site(self, site_id):
        self.exploration.get_site(site_id)
        return self.repository.list_for_site(site_id)

    def extract(self, request: FeatureExtractionRequest) -> FeatureBundle:
        coordinates = request.coordinates
        if request.site_id:
            site = self.exploration.get_site(request.site_id)
            coordinates = Coordinates(latitude=site.latitude, longitude=site.longitude)
        if coordinates:
            result = self.provider.extract_features_for_point(
                coordinates.latitude, coordinates.longitude, request.start_date, request.end_date)
        else:
            result = self.provider.extract_features_for_aoi(
                request.aoi.model_dump(), request.start_date, request.end_date)
        result.site_id = request.site_id
        result.coordinates = coordinates
        result.aoi = request.aoi
        result.start_date = request.start_date
        result.end_date = request.end_date
        if result.readiness != Readiness.OK and request.allow_demo_fallback and self.settings.gee_allow_demo_features:
            result = result.model_copy(update={
                "is_stub": True, "source": "demo_fixture", "readiness": Readiness.STUB,
                "feature_version": "demo-integration-v1",
                "feature_payload": {"integration_fixture_value": 0.5, "purpose": "software_contract_test"},
                "message": "Demo integration payload only; not scientifically validated.",
                "warning": "Demo feature payload, not extracted from Earth Engine.",
                "extracted_at": utc_now(), "feature_id": str(uuid4()),
            })
        if result.readiness in (Readiness.OK, Readiness.STUB):
            if result.feature_id is None:
                result.feature_id = str(uuid4())
                result.extracted_at = utc_now()
            return self.repository.save_feature_bundle(result)
        return result
