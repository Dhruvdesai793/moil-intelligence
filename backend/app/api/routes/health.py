from fastapi import APIRouter, Depends

from app.api.dependencies import get_health
from app.schemas.common import HealthResponse
from app.services.health_service import HealthService

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
def health_check(service: HealthService = Depends(get_health)) -> HealthResponse:
    return service.check()
