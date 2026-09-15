import ast
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import (
    get_exploration_repository,
    get_feature_repository,
    get_prediction_repository,
    get_job_repository,
    get_registry,
    get_gee,
    get_health,
)
from app.core.config import Settings
from app.providers.gee import GEEProvider
from app.providers.weather import WeatherProvider
from app.services.feature_service import FeatureService
from app.schemas.features import FeatureExtractionRequest
from app.services.health_service import HealthService
from tests.fakes import FakeExplorationRepository, FakeFeatures, FakeRecords
from app.main import app
from app.ml.base import ModelInput
from app.ml.registry import ModelRegistry
from app.schemas.prediction import ExplorationPredictionRequest
from app.services.exploration_service import ExplorationService
from app.services.prediction_orchestrator import PredictionOrchestrator


@pytest.fixture
def client():
    registry = ModelRegistry()
    gee = GEEProvider(Settings(gee_enabled=False, _env_file=None))
    features, predictions, jobs = FakeFeatures(), FakeRecords(), FakeRecords()
    app.dependency_overrides.update(
        {
            get_exploration_repository: lambda: FakeExplorationRepository(),
            get_feature_repository: lambda: features,
            get_prediction_repository: lambda: predictions,
            get_job_repository: lambda: jobs,
            get_registry: lambda: registry,
            get_gee: lambda: gee,
            get_health: lambda: HealthService(
                lambda: (_ for _ in ()).throw(RuntimeError()),
                gee,
                registry,
                Settings(_env_file=None),
            ),
        }
    )
    with TestClient(app) as client:
        client.registry = registry
        client.predictions = predictions
        client.features = features
        client.feature_service = FeatureService(
            features,
            ExplorationService(
                FakeExplorationRepository(), registry, gee, WeatherProvider()
            ),
            gee,
            Settings(gee_enabled=False, _env_file=None),
        )
        yield client
    app.dependency_overrides.clear()


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
    assert all(
        item["readiness"] == "not_configured"
        for item in summary["feature_availability"]
    )


@pytest.mark.parametrize(
    "path",
    [
        "/exploration/sites/missing",
        "/exploration/sites/missing/summary",
        "/jobs/missing",
    ],
)
def test_missing_records(client, path):
    response = client.get("/api/v1" + path)
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


def test_prediction_contract_and_determinism(client):
    payload = {
        "site_id": "zone_a",
        "requested_resolution_m": 10,
        "as_of": "2026-01-01T00:00:00Z",
    }
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
    response = client.post(
        "/api/v1/predictions/exploration",
        json={
            "coordinates": {"latitude": 21, "longitude": 79},
        },
    )
    assert response.status_code == 200
    assert response.json()["site_id"] is None


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"site_id": "zone_a", "coordinates": {"latitude": 21, "longitude": 79}},
        {"coordinates": {"latitude": 91, "longitude": 79}},
        {"site_id": "zone_a", "requested_resolution_m": -1},
        {"site_id": "zone_a", "as_of": "2026-01-01T00:00:00"},
        {"site_id": "zone_a", "as_of": "2999-01-01T00:00:00Z"},
    ],
)
def test_invalid_predictions(client, payload):
    response = client.post("/api/v1/predictions/exploration", json=payload)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_prediction_missing_site(client):
    assert (
        client.post(
            "/api/v1/predictions/exploration", json={"site_id": "missing"}
        ).status_code
        == 404
    )


def test_production_and_recommendations(client):
    production = client.get("/api/v1/production/overview")
    assert production.status_code == 200
    assert production.json()["is_stub"] is True
    assert production.json()["predicted"] == 860
    recommendations = client.get("/api/v1/decision/recommendations")
    assert recommendations.status_code == 200
    assert recommendations.json()["is_stub"] is True
    assert recommendations.json()["recommendations"][0]["actions"]
    assert (
        recommendations.json()["recommendations"][0]["status"]
        == "human_review_required"
    )


@pytest.mark.parametrize("immediate, status", [(True, "completed"), (False, "queued")])
def test_job_creation_and_polling(client, immediate, status):
    response = client.post(
        "/api/v1/jobs",
        json={
            "site_id": "zone_a",
            "complete_immediately": immediate,
        },
    )
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
    settings = Settings(_env_file=None)
    gee = GEEProvider(settings)
    exploration = ExplorationService(
        FakeExplorationRepository(), registry, gee, WeatherProvider()
    )
    features = FeatureService(FakeFeatures(), exploration, gee, settings)
    orchestrator = PredictionOrchestrator(
        exploration, registry, FakeRecords(), features
    )
    result = orchestrator.exploration_prediction(
        ExplorationPredictionRequest(site_id="zone_a")
    )
    assert result.status == "insufficient_real_data"
    assert result.prospectivity_score is None
    assert result.is_stub is True
    assert result.models[0].readiness == "unavailable"


def test_api_graceful_optional_model_failure(client):
    client.registry.adapters.clear()
    prediction = client.post(
        "/api/v1/predictions/exploration", json={"site_id": "zone_a"}
    )
    assert prediction.status_code == 200
    assert prediction.json()["prospectivity_score"] is None
    production = client.get("/api/v1/production/overview").json()
    assert production["predicted"] is None
    assert production["shortfall_probability"] is None
    assert production["risk"] == "UNKNOWN"
    assert client.get("/api/v1/decision/recommendations").status_code == 200


def test_local_cors(client):
    response = client.options(
        "/api/v1/predictions/exploration",
        headers={
            "Origin": "http://localhost:8501",
            "Access-Control-Request-Method": "POST",
        },
    )
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
                imports = (
                    [node.module or ""]
                    if isinstance(node, ast.ImportFrom)
                    else [item.name for item in node.names]
                    if isinstance(node, ast.Import)
                    else []
                )
                assert not any(
                    name == prefix or name.startswith(prefix + ".")
                    for name in imports
                    for prefix in forbidden
                ), str(path)


def test_feature_availability(client):
    response = client.get("/api/v1/features/sites/zone_a/availability")
    assert response.status_code == 200
    assert response.json()["provider"]["readiness"] == "not_configured"


def test_features_require_explicit_demo_fallback(client):
    payload = {
        "site_id": "zone_a",
        "start_date": "2025-01-01",
        "end_date": "2025-02-01",
    }
    result = client.feature_service.extract(
        FeatureExtractionRequest(**payload)
    ).model_dump(mode="json")
    assert result["readiness"] == "not_configured"
    assert result["feature_payload"] == {}
    assert result["is_stub"] is False
    assert client.features.records == []
    payload["allow_demo_fallback"] = True
    result = client.feature_service.extract(
        FeatureExtractionRequest(**payload)
    ).model_dump(mode="json")
    assert result["is_stub"] is True
    assert result["source"] == "demo_fixture"
    assert len(client.features.records) == 1
    prediction = client.post(
        "/api/v1/predictions/exploration", json={"site_id": "zone_a"}
    ).json()
    assert prediction["feature_version"] == result["feature_version"]
    assert prediction["data_timestamp"] == result["extracted_at"]
    assert prediction["prediction_id"] in client.predictions.records
    from datetime import datetime

    assert datetime.fromisoformat(
        prediction["data_timestamp"]
    ) <= datetime.fromisoformat(prediction["as_of"])


@pytest.mark.parametrize(
    "payload",
    [
        {"start_date": "2025-01-01", "end_date": "2025-02-01"},
        {"site_id": "zone_a", "start_date": "2025-02-01", "end_date": "2025-01-01"},
        {
            "aoi": {"type": "Polygon", "coordinates": [[[79, 21], [80, 21], [80, 22]]]},
            "start_date": "2025-01-01",
            "end_date": "2025-02-01",
        },
    ],
)
def test_invalid_feature_requests(client, payload):
    assert client.post("/api/v1/features/extract", json=payload).status_code == 422


def test_feature_aoi_demo(client):
    result = client.feature_service.extract(
        FeatureExtractionRequest(
            **{
                "aoi": {
                    "type": "Polygon",
                    "coordinates": [
                        [[79, 21.4], [79.01, 21.4], [79.01, 21.41], [79, 21.4]]
                    ],
                },
                "start_date": "2025-01-01",
                "end_date": "2025-02-01",
                "allow_demo_fallback": True,
            }
        )
    ).model_dump(mode="json")
    assert result["is_stub"] is True
    assert result["aoi"]["type"] == "Polygon"


def test_historical_prediction_does_not_read_future_features(client):
    client.feature_service.extract(
        FeatureExtractionRequest(
            **{
                "site_id": "zone_a",
                "start_date": "2025-01-01",
                "end_date": "2025-02-01",
                "allow_demo_fallback": True,
            }
        )
    )
    result = client.post(
        "/api/v1/predictions/exploration",
        json={
            "site_id": "zone_a",
            "as_of": "2025-03-01T00:00:00Z",
        },
    ).json()
    assert result["data_timestamp"] is None


def test_demo_disabled_by_configuration(client):
    from app.api.dependencies import get_settings

    app.dependency_overrides[get_settings] = lambda: Settings(
        gee_allow_demo_features=False, _env_file=None
    )
    client.feature_service.settings = Settings(
        gee_allow_demo_features=False, _env_file=None
    )
    result = client.feature_service.extract(
        FeatureExtractionRequest(
            **{
                "site_id": "zone_a",
                "start_date": "2025-01-01",
                "end_date": "2025-02-01",
                "allow_demo_fallback": True,
            }
        )
    ).model_dump(mode="json")
    assert result["feature_payload"] == {}
    assert client.features.records == []


def test_gee_auth_failure_is_honest(monkeypatch):
    from types import SimpleNamespace
    import app.providers.gee as module

    def fail(**kwargs):
        raise RuntimeError("Please authenticate with credentials")

    monkeypatch.setattr(
        module.importlib,
        "import_module",
        lambda name: SimpleNamespace(
            Initialize=fail, data=SimpleNamespace(setDeadline=lambda value: None)
        ),
    )
    provider = GEEProvider(Settings(gee_enabled=True, _env_file=None))
    result = provider.availability()
    assert result.readiness == "auth_required"
    assert "earthengine authenticate" in result.metadata.warning


def test_gee_initialization_order_and_cache(monkeypatch):
    from types import SimpleNamespace
    import app.providers.gee as module

    calls = []
    ee = SimpleNamespace(
        Initialize=lambda **kwargs: calls.append(("initialize", kwargs["project"])),
        data=SimpleNamespace(
            setDeadline=lambda value: calls.append(("deadline", value)),
            getAlgorithms=lambda: calls.append(("smoke", None)),
        ),
    )
    monkeypatch.setattr(module.importlib, "import_module", lambda name: ee)
    provider = GEEProvider(Settings(gee_enabled=True, _env_file=None))
    assert provider.availability().readiness == "ok"
    assert provider.availability().readiness == "ok"
    assert calls == [
        ("initialize", "secure-guru-473417-q2"),
        ("deadline", 60000),
        ("smoke", None),
    ]


def test_prediction_read_and_feature_history(client):
    client.feature_service.extract(
        FeatureExtractionRequest(
            site_id="zone_a",
            start_date="2025-01-01",
            end_date="2025-02-01",
            allow_demo_fallback=True,
        )
    )
    payload = {"site_id": "zone_a", "allow_demo_features": True}
    prediction = client.post("/api/v1/predictions/exploration", json=payload).json()
    assert (
        client.get("/api/v1/predictions/" + prediction["prediction_id"]).json()
        == prediction
    )
    bundles = client.get("/api/v1/features/sites/zone_a").json()
    assert len(bundles) == 1 and bundles[0]["is_stub"]
    assert client.get("/api/v1/predictions/missing").status_code == 404


def test_routes_do_not_construct_infrastructure():
    directory = Path(__file__).resolve().parents[1] / "app" / "api" / "routes"
    for path in directory.glob("*.py"):
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node, ast.Call):
                name = (
                    node.func.id
                    if isinstance(node.func, ast.Name)
                    else node.func.attr
                    if isinstance(node.func, ast.Attribute)
                    else ""
                )
                assert not name.endswith(("Repository", "Provider", "Orchestrator")), (
                    str(path)
                )
                assert name not in ("create_engine", "Session", "SessionLocal"), str(
                    path
                )
