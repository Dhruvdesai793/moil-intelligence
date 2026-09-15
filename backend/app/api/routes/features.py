from fastapi import APIRouter, Depends

from app.api.dependencies import get_features, get_extractions
from app.schemas.jobs import JobRecord
from app.services.extraction_service import ExtractionService
from app.schemas.features import (
    FeatureAvailability,
    FeatureBundle,
    FeatureExtractionRequest,
)
from app.services.feature_service import FeatureService

router = APIRouter(prefix="/features", tags=["Features"])


@router.get("/bundles/{feature_id}", response_model=FeatureBundle)
def get_bundle(feature_id: str, service: FeatureService = Depends(get_features)):
    return service.get(feature_id)


@router.get("/sites/{site_id}/availability", response_model=FeatureAvailability)
def availability(site_id: str, service: FeatureService = Depends(get_features)):
    return service.availability(site_id)


@router.post("/extract", response_model=JobRecord, status_code=202)
def extract(
    request: FeatureExtractionRequest,
    service: ExtractionService = Depends(get_extractions),
):
    return service.queue(request)


@router.get("/sites/{site_id}", response_model=list[FeatureBundle])
def list_features(site_id: str, service: FeatureService = Depends(get_features)):
    return service.list_for_site(site_id)
