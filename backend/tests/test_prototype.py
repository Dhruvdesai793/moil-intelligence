import ast
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_services
from app.main import app
from app.ml.base import ModelInput
from app.ml.registry import ModelRegistry
from app.repositories.exploration import ExplorationRepository
from app.repositories.predictions import PredictionRepository
from app.schemas.prediction import ExplorationPredictionRequest
from app.services.exploration_service import ExplorationService
from app.services.prediction_orchestrator import PredictionOrchestrator


@pytest.fixture
def client():
    get_services.cache_clear()
    with TestClient(app) as client:
        yield client
    get_services.cache_clear()


def test_active_sites_and_summary(client):
    response = client.get("/api/v1/exploration/sites")
    assert response.status_code == 200
    sites = response.json()
    assert len(sites) == 2
    assert all(site["status"] == "ACTIVE" for site in sites)
    assert all(site["metadata"]["is_stub"] for site in sites)
    summary = client.get("/api/v1/exploration/sites/zone_a/summary").json()
    assert summary["site"]["id"] == "zone_a"
    assert summary["model_readiness"]["grade"] == "not_configured"
    assert all(item["readiness"] == "not_configured"
               for item in summary["feature_availability"])


@pytest.mark.parametrize("path", [
    "/exploration/sites/missing", "/exploration/sites/missing/summary", "/jobs/missing",
])
def test_missing_records(client, path):
    response = client.get("/api/v1" + path)
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


def test_prediction_contract_and_determinism(client):
    payload = {"site_id": "zone_a", "requested_resolution_m": 10,
               "as_of": "2026-01-01T00:00:00Z"}
    first_response = client.post("/api/v1/predictions/exploration", json=payload)
    assert first_response.status_code == 200
    first = first_response.json()
    second = client.post("/api/v1/predictions/exploration", json=payload).json()
    assert first["is_stub"] is True
    assert first["prospectivity_score"] == second["prospectivity_score"]
    assert first["score_type"] == "demo_ranking_score"
    assert first["prediction_id"] != second["prediction_id"]
    assert first["uncertainty"]["method"] == "not_calibrated"
    assert first["uncertainty"]["lower"] is None
    assert first["data_timestamp"] is None
    assert first["effective_resolution_m"] is None
    assert "not scientifically validated" in first["message"]
    assert first["models"][1]["value"] is None
    for key in ("source", "feature_version", "prediction_timestamp", "model_version"):
        assert first[key]


def test_coordinate_input(client):
    response = client.post("/api/v1/predictions/exploration", json={
        "coordinates": {"latitude": 21, "longitude": 79},
    })
    assert response.status_code == 200
    assert response.json()["site_id"] is None


@pytest.mark.parametrize("payload", [
    {}, {"site_id": "zone_a", "coordinates": {"latitude": 21, "longitude": 79}},
    {"coordinates": {"latitude": 91, "longitude": 79}},
    {"site_id": "zone_a", "requested_resolution_m": -1},
    {"site_id": "zone_a", "as_of": "2026-01-01T00:00:00"},
    {"site_id": "zone_a", "as_of": "2999-01-01T00:00:00Z"},
])
def test_invalid_predictions(client, payload):
    response = client.post("/api/v1/predictions/exploration", json=payload)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_prediction_missing_site(client):
    assert client.post("/api/v1/predictions/exploration",
                       json={"site_id": "missing"}).status_code == 404


def test_production_and_recommendations(client):
    production = client.get("/api/v1/production/overview")
    assert production.status_code == 200
    assert production.json()["is_stub"] is True
    assert production.json()["predicted"] == 860
    recommendations = client.get("/api/v1/decision/recommendations")
    assert recommendations.status_code == 200
    assert recommendations.json()["is_stub"] is True
    assert recommendations.json()["recommendations"][0]["actions"]
    assert recommendations.json()["recommendations"][0]["status"] == "human_review_required"


@pytest.mark.parametrize("immediate, status", [(True, "completed"), (False, "queued")])
def test_job_creation_and_polling(client, immediate, status):
    response = client.post("/api/v1/jobs", json={
        "site_id": "zone_a", "complete_immediately": immediate,
    })
    assert response.status_code == 201
    job = response.json()
    assert job["status"] == status
    assert job["is_stub"] is True
    polled = client.get("/api/v1/jobs/" + job["job_id"])
    assert polled.status_code == 200
    assert polled.json() == job
    assert (job["result"] is not None) == immediate


class BrokenAdapter:
    name = "prospectivity"

    def predict(self, inputs: ModelInput):
        raise RuntimeError("Missing artifact")


@pytest.mark.parametrize("adapters", [{}, {"prospectivity": BrokenAdapter()}])
def test_missing_or_broken_models(adapters):
    registry = ModelRegistry(adapters)
    exploration = ExplorationService(ExplorationRepository(), registry)
    orchestrator = PredictionOrchestrator(exploration, registry, PredictionRepository())
    result = orchestrator.exploration_prediction(
        ExplorationPredictionRequest(site_id="zone_a"))
    assert result.status == "insufficient_real_data"
    assert result.prospectivity_score is None
    assert result.is_stub is True
    assert result.models[0].readiness == "unavailable"


def test_api_graceful_optional_model_failure(client):
    get_services().orchestrator.registry.adapters.clear()
    prediction = client.post("/api/v1/predictions/exploration", json={"site_id": "zone_a"})
    assert prediction.status_code == 200
    assert prediction.json()["prospectivity_score"] is None
    production = client.get("/api/v1/production/overview").json()
    assert production["predicted"] is None
    assert production["shortfall_probability"] is None
    assert production["risk"] == "UNKNOWN"
    assert client.get("/api/v1/decision/recommendations").status_code == 200


def test_local_cors(client):
    response = client.options("/api/v1/predictions/exploration", headers={
        "Origin": "http://localhost:8501",
        "Access-Control-Request-Method": "POST",
    })
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:8501"


def test_layer_import_boundaries():
    app_dir = Path(__file__).resolve().parents[1] / "app"
    for directory, forbidden in [
        (app_dir / "api" / "routes", ("app.ml", "app.providers", "app.repositories")),
        (app_dir / "repositories", ("fastapi", "starlette", "app.services", "app.ml")),
        (app_dir / "services", ("fastapi", "starlette")),
        (app_dir.parents[1] / "frontend", ("app",)),
    ]:
        for path in directory.rglob("*.py"):
            tree = ast.parse(path.read_text())
            for node in ast.walk(tree):
                imports = ([node.module or ""] if isinstance(node, ast.ImportFrom)
                           else [item.name for item in node.names]
                           if isinstance(node, ast.Import) else [])
                assert not any(name == prefix or name.startswith(prefix + ".")
                               for name in imports for prefix in forbidden), str(path)
