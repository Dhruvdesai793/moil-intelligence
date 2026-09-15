from collections import OrderedDict
from threading import Lock

from app.schemas.prediction import ExplorationPrediction


class PredictionRepository:
    def __init__(self):
        self._records: OrderedDict[str, ExplorationPrediction] = OrderedDict()
        self._lock = Lock()

    def save(self, prediction: ExplorationPrediction) -> ExplorationPrediction:
        with self._lock:
            self._records[prediction.prediction_id] = prediction.model_copy(deep=True)
            if len(self._records) > 1000:
                self._records.popitem(last=False)
        return prediction

    def get(self, prediction_id: str) -> ExplorationPrediction | None:
        with self._lock:
            record = self._records.get(prediction_id)
            return record.model_copy(deep=True) if record else None
