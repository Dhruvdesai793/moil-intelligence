from fastapi import APIRouter, Depends

from app.api.dependencies import get_exploration
from app.schemas.exploration import Site, SiteSummary, SiteCreate
from app.services.exploration_service import ExplorationService

router = APIRouter(prefix="/exploration", tags=["Exploration"])


@router.post("/sites", response_model=Site, status_code=201)
def create_site(
    request: SiteCreate, service: ExplorationService = Depends(get_exploration)
):
    return service.create(request)


@router.get("/sites", response_model=list[Site])
def get_sites(service: ExplorationService = Depends(get_exploration)) -> list[Site]:
    return service.get_sites()


@router.get("/sites/{site_id}", response_model=Site)
def get_site(
    site_id: str, service: ExplorationService = Depends(get_exploration)
) -> Site:
    return service.get_site(site_id)


@router.get("/sites/{site_id}/summary", response_model=SiteSummary)
def get_summary(
    site_id: str, service: ExplorationService = Depends(get_exploration)
) -> SiteSummary:
    return service.summary(site_id)
