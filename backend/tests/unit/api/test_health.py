from fastapi.testclient import TestClient

from app.api.dependencies import get_health
from app.core.config import Settings
from app.main import app
from app.ml.registry import ModelRegistry
from app.providers.gee import GEEProvider
from app.services.health_service import HealthService


def test_health_returns_200_when_infrastructure_unavailable():
    settings = Settings(gee_enabled=False, _env_file=None)

    def unavailable_engine():
        raise RuntimeError("offline")

    app.dependency_overrides[get_health] = lambda: HealthService(
        unavailable_engine, GEEProvider(settings), ModelRegistry(), settings)
    try:
        with TestClient(app) as client:
            response = client.get("/api/v1/health")
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "degraded"
        assert body["database"] == body["postgis"] == "unavailable"
        assert body["gee"] == "not_configured"
    finally:
        app.dependency_overrides.clear()
