from typing import Literal
from fastapi import APIRouter, Depends
from fastapi.responses import Response
from app.api.dependencies import get_intelligence
from app.schemas.ml import ModelInput
from app.schemas.intelligence import StudyArea, Rankings, SpectralReference
from app.services.intelligence_service import IntelligenceService

router = APIRouter(tags=["Exploration intelligence"])


@router.get("/exploration/study-area", response_model=StudyArea)
def study_area(service: IntelligenceService = Depends(get_intelligence)):
    return service.study_area()


@router.get("/exploration/rankings", response_model=Rankings)
def rankings(service: IntelligenceService = Depends(get_intelligence)):
    return service.rankings()


@router.get("/features/sites/{site_id}/model-input", response_model=ModelInput)
def model_input(site_id: str, service: IntelligenceService = Depends(get_intelligence)):
    return service.model_input(site_id)


@router.get("/exploration/sites/{site_id}/export")
def export(
    site_id: str,
    format: Literal["csv", "text"] = "csv",
    service: IntelligenceService = Depends(get_intelligence),
):
    return Response(
        content=service.export(site_id, format),
        media_type="text/csv" if format == "csv" else "text/plain",
        headers={
            "Content-Disposition": f'attachment; filename="location.{format if format == "csv" else "txt"}"'
        },
    )


@router.get("/spectral/reference", response_model=SpectralReference)
def reference(service: IntelligenceService = Depends(get_intelligence)):
    return service.spectral_reference()
