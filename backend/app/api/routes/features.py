from fastapi import APIRouter, Depends

from app.api.dependencies import get_features
from app.schemas.features import FeatureAvailability, FeatureBundle, FeatureExtractionRequest
from app.services.feature_service import FeatureService

router = APIRouter(prefix="/features", tags=["Features"])


@router.get("/sites/{site_id}/availability", response_model=FeatureAvailability)
def availability(site_id: str, service: FeatureService = Depends(get_features)):
    return service.availability(site_id)


@router.post("/extract", response_model=FeatureBundle)
def extract(request: FeatureExtractionRequest, service: FeatureService = Depends(get_features)):
    return service.extract(request)


@router.get("/sites/{site_id}", response_model=list[FeatureBundle])
def list_features(site_id: str, service: FeatureService = Depends(get_features)):
    return service.list_for_site(site_id)
