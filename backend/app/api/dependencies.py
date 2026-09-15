from functools import lru_cache

from app.ml.registry import ModelRegistry
from app.repositories.exploration import ExplorationRepository
from app.repositories.jobs import JobRepository
from app.repositories.predictions import PredictionRepository
from app.repositories.production import ProductionRepository
from app.services.decision_service import DecisionService
from app.services.exploration_service import ExplorationService
from app.services.job_service import JobService
from app.services.prediction_orchestrator import PredictionOrchestrator
from app.services.production_service import ProductionService


class ApplicationServices:
    def __init__(self):
        registry = ModelRegistry()
        self.exploration = ExplorationService(ExplorationRepository(), registry)
        self.orchestrator = PredictionOrchestrator(
            self.exploration, registry, PredictionRepository())
        self.production = ProductionService(ProductionRepository(), self.orchestrator)
        self.decision = DecisionService(self.production, self.exploration)
        self.jobs = JobService(JobRepository(), self.orchestrator)


@lru_cache
def get_services() -> ApplicationServices:
    return ApplicationServices()


def get_exploration() -> ExplorationService:
    return get_services().exploration


def get_orchestrator() -> PredictionOrchestrator:
    return get_services().orchestrator


def get_production() -> ProductionService:
    return get_services().production


def get_decision() -> DecisionService:
    return get_services().decision


def get_jobs() -> JobService:
    return get_services().jobs
