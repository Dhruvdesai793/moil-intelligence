import importlib
import logging
import httplib2
from threading import Lock
from time import monotonic

from app.core.config import Settings
from app.schemas.common import Metadata, ProviderAvailability, Readiness
from app.schemas.features import FeatureBundle

logger = logging.getLogger("moil.gee")


class GEEProvider:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._ee = None
        self._lock = Lock()
        self._checked_at = 0.0
        self._availability = None

    def availability(self) -> ProviderAvailability:
        if not self.settings.gee_enabled:
            return self._status(Readiness.NOT_CONFIGURED, "GEE_ENABLED=false; no Earth Engine calls made.")
        with self._lock:
            if self._availability is not None and monotonic() - self._checked_at < 30:
                return self._availability.model_copy(deep=True)
            try:
                ee = importlib.import_module("ee")
                if self.settings.gee_auth_method != "oauth":
                    return self._status(Readiness.NOT_CONFIGURED, "Only development OAuth is supported.")
                ee.Initialize(project=self.settings.gee_project_id,
                              http_transport=httplib2.Http(timeout=5))
                ee.data.setDeadline(5000)
                ee.data.getAlgorithms()
                self._ee = ee
                result = self._status(Readiness.OK, "Earth Engine initialized; lightweight algorithm smoke check passed.")
            except ImportError:
                result = self._status(Readiness.UNAVAILABLE, "Install earthengine-api in the backend virtual environment.")
            except Exception as exc:
                text = str(exc).lower()
                auth = any(word in text for word in ("authenticate", "credential", "invalid_grant", "refresherror"))
                status = Readiness.AUTH_REQUIRED if auth else Readiness.UNAVAILABLE
                message = ("Run earthengine authenticate in the backend virtual environment and accept browser OAuth."
                           if auth else "Earth Engine initialization failed. Check project access, API enablement and network.")
                logger.warning("Earth Engine initialization failed (%s)", type(exc).__name__)
                result = self._status(status, message)
            self._availability = result
            self._checked_at = monotonic()
            return result.model_copy(deep=True)

    def _status(self, readiness, warning):
        return ProviderAvailability(
            provider="gee", readiness=readiness,
            features=["ndvi", "land_surface_temperature", "soil_moisture", "rainfall_history", "terrain"],
            metadata=Metadata(source="earth_engine", is_stub=False,
                              message=(warning if readiness == Readiness.OK else
                                       "Integration status only; not feature or model validation."),
                              warning=None if readiness == Readiness.OK else warning))

    def _extract(self) -> FeatureBundle:
        availability = self.availability()
        status = Readiness.NOT_IMPLEMENTED if availability.readiness == Readiness.OK else availability.readiness
        return FeatureBundle(readiness=status, source="none", warning=(
            "Real batch extraction is not implemented. No satellite measurements returned."
            if status == Readiness.NOT_IMPLEMENTED else availability.metadata.warning))

    def extract_features_for_point(self, latitude, longitude, start_date, end_date) -> FeatureBundle:
        return self._extract()

    def extract_features_for_aoi(self, geojson, start_date, end_date) -> FeatureBundle:
        return self._extract()
