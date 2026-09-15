from fastapi import APIRouter, Depends

from app.api.dependencies import get_decision
from app.schemas.decision import Recommendations
from app.services.decision_service import DecisionService

router = APIRouter(prefix="/decision", tags=["Decision"])


@router.get("/recommendations", response_model=Recommendations)
def recommendations(service: DecisionService = Depends(get_decision)) -> Recommendations:
    return service.recommendations()
