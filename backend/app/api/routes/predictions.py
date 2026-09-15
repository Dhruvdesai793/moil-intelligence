from fastapi import APIRouter, Depends

from app.api.dependencies import get_orchestrator
from app.schemas.prediction import ExplorationPrediction, ExplorationPredictionRequest
from app.services.prediction_orchestrator import PredictionOrchestrator

router = APIRouter(prefix="/predictions", tags=["Predictions"])


@router.post("/exploration", response_model=ExplorationPrediction)
def predict(request: ExplorationPredictionRequest,
            service: PredictionOrchestrator = Depends(get_orchestrator)) -> ExplorationPrediction:
    return service.exploration_prediction(request)


@router.get("/{prediction_id}", response_model=ExplorationPrediction)
def get_prediction(prediction_id: str,
                   service: PredictionOrchestrator = Depends(get_orchestrator)):
    return service.get_prediction(prediction_id)
