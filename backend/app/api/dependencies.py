from functools import lru_cache

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db, get_engine
from app.ml.registry import ModelRegistry
from app.providers.gee import GEEProvider
from app.providers.weather import WeatherProvider
from app.repositories.exploration import ExplorationRepository
from app.repositories.features import FeatureRepository
from app.repositories.jobs import JobRepository
from app.repositories.predictions import PredictionRepository
from app.repositories.production import ProductionRepository
from app.services.decision_service import DecisionService
from app.services.exploration_service import ExplorationService
from app.services.feature_service import FeatureService
from app.services.health_service import HealthService
from app.services.job_service import JobService
from app.services.prediction_orchestrator import PredictionOrchestrator
from app.services.production_service import ProductionService


@lru_cache
def get_registry():
    return ModelRegistry()


@lru_cache
def get_gee():
    return GEEProvider(get_settings())


def get_weather():
    return WeatherProvider()


def get_exploration_repository(db: Session = Depends(get_db, scope="function")):
    return ExplorationRepository(db)


def get_feature_repository(db: Session = Depends(get_db, scope="function")):
    return FeatureRepository(db)


def get_prediction_repository(db: Session = Depends(get_db, scope="function")):
    return PredictionRepository(db)


def get_job_repository(db: Session = Depends(get_db, scope="function")):
    return JobRepository(db)


def get_exploration(repository=Depends(get_exploration_repository),
                    registry=Depends(get_registry), gee=Depends(get_gee), weather=Depends(get_weather)):
    return ExplorationService(repository, registry, gee, weather)


def get_features(repository=Depends(get_feature_repository), exploration=Depends(get_exploration),
                 gee=Depends(get_gee), settings=Depends(get_settings)):
    return FeatureService(repository, exploration, gee, settings)


def get_orchestrator(exploration=Depends(get_exploration), registry=Depends(get_registry),
                     repository=Depends(get_prediction_repository), features=Depends(get_features)):
    return PredictionOrchestrator(exploration, registry, repository, features)


def get_production_repository():
    return ProductionRepository()


def get_production(repository=Depends(get_production_repository), orchestrator=Depends(get_orchestrator)):
    return ProductionService(repository, orchestrator)


def get_decision(production=Depends(get_production), exploration=Depends(get_exploration)):
    return DecisionService(production, exploration)


def get_jobs(repository=Depends(get_job_repository), orchestrator=Depends(get_orchestrator)):
    return JobService(repository, orchestrator)


def get_health(gee=Depends(get_gee), registry=Depends(get_registry), settings=Depends(get_settings)):
    # Guarded connection: unavailable DB cannot abort health dependency resolution.
    return HealthService(get_engine, gee, registry, settings)
