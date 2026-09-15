from app.repositories.production import ProductionRepository
from app.schemas.production import ProductionOverview, Risk
from app.services.prediction_orchestrator import PredictionOrchestrator


class ProductionService:
    def __init__(self, repository: ProductionRepository, orchestrator: PredictionOrchestrator):
        self.repository = repository
        self.orchestrator = orchestrator

    def overview(self) -> ProductionOverview:
        state = self.repository.get_overview()
        model = self.orchestrator.production_prediction(state.target)
        predicted = model.value
        risk = Risk.UNKNOWN if predicted is None else (
            Risk.HIGH if predicted < state.target else Risk.LOW)
        return ProductionOverview(
            target=state.target, predicted=predicted,
            shortfall_probability=0.81 if predicted is not None else None,
            risk=risk, model_version=model.model_version, model=model,
            status="stub" if predicted is not None else "insufficient_real_data",
            warning="Target, forecast and shortfall probability are software fixtures. "
                    "No real operational history or chronological backtesting.",
        )
