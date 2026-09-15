from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.prediction import Prediction
from app.schemas.prediction import ExplorationPrediction


class PredictionRepository:
    def __init__(self, session: Session):
        self.session = session

    def save(self, prediction: ExplorationPrediction) -> ExplorationPrediction:
        self.session.add(Prediction(
            id=prediction.prediction_id, site_id=prediction.site_id,
            coordinates=prediction.coordinates.model_dump(), prediction_type="exploration",
            result_payload=prediction.model_dump(mode="json"), model_version=prediction.model_version,
            feature_version=prediction.feature_version, is_stub=prediction.is_stub,
            warning=prediction.warning, created_at=prediction.prediction_timestamp))
        self.session.flush()
        return prediction

    def get(self, prediction_id: str) -> ExplorationPrediction | None:
        row = self.session.get(Prediction, prediction_id)
        return ExplorationPrediction.model_validate(row.result_payload) if row else None

    def list_recent(self, limit: int = 20) -> list[ExplorationPrediction]:
        return [ExplorationPrediction.model_validate(row.result_payload) for row in self.session.scalars(
            select(Prediction).order_by(Prediction.created_at.desc()).limit(limit))]
