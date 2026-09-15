from fastapi import APIRouter, Depends

from app.api.dependencies import get_production
from app.schemas.production import ProductionOverview
from app.services.production_service import ProductionService

router = APIRouter(prefix="/production", tags=["Production"])


@router.get("/overview", response_model=ProductionOverview)
def overview(service: ProductionService = Depends(get_production)) -> ProductionOverview:
    return service.overview()
