from fastapi.testclient import TestClient
import pytest
from app.main import app
from app.api.dependencies import (
    get_exploration_repository,
    get_feature_repository,
    get_job_repository,
    get_gee,
    get_registry,
)
from app.ml.registry import ModelRegistry
from app.providers.gee import GEEProvider
from app.core.config import Settings
from app.schemas.features import FeatureBundle, FeatureExtractionRequest
from app.schemas.common import utc_now
from app.schemas.ml import ModelInput
from tests.fakes import FakeExplorationRepository, FakeFeatures, FakeRecords
from scripts.fetch_spectral_reference import parse_spectrum


@pytest.fixture
def context():
    exploration = FakeExplorationRepository()
    features, jobs = FakeFeatures(), FakeRecords()
    provider = GEEProvider(Settings(gee_enabled=False, _env_file=None))
    registry = ModelRegistry()
    app.dependency_overrides.update(
        {
            get_exploration_repository: lambda: exploration,
            get_feature_repository: lambda: features,
            get_job_repository: lambda: jobs,
            get_gee: lambda: provider,
            get_registry: lambda: registry,
        }
    )
    with TestClient(app) as client:
        yield client, features, jobs
    app.dependency_overrides.clear()


def test_extraction_queues_without_provider_computation(context, monkeypatch):
    client, features, jobs = context
    response = client.post(
        "/api/v1/features/extract",
        json={
            "site_id": "zone_a",
            "start_date": "2025-01-01",
            "end_date": "2025-02-01",
        },
    )
    assert response.status_code == 202
    record = response.json()
    assert record["status"] == "queued" and record["result"] is None
    assert record["is_stub"] is False
    assert features.records == []
    assert (
        client.get("/api/v1/jobs/" + record["job_id"]).json()["request"]["task"]
        == "feature_extraction"
    )


def test_model_handoff_includes_measured_features(context):
    client, features, _ = context
    bundle = FeatureBundle(
        feature_id="measured1",
        site_id="zone_a",
        source="earth_engine",
        is_stub=False,
        readiness="ok",
        extracted_at=utc_now(),
        feature_version="gee-environment-v1",
        feature_payload={"ndvi": 0.31, "s2_B12": 0.12},
    )
    features.save_feature_bundle(bundle)
    assert (
        client.get("/api/v1/features/bundles/measured1").json()["feature_payload"][
            "ndvi"
        ]
        == 0.31
    )
    assert client.get("/api/v1/features/bundles/missing").status_code == 404
    result = client.get("/api/v1/features/sites/zone_a/model-input")
    assert result.status_code == 200
    inputs = ModelInput.model_validate(result.json())
    assert inputs.features.feature_payload["s2_B12"] == 0.12
    assert not inputs.features.is_stub
    assert "trained_model" in inputs.missing_inputs


def test_rankings_honest_and_sorted(context):
    client, _, _ = context
    response = client.get("/api/v1/exploration/rankings").json()
    assert response["is_stub"] is True
    rows = response["locations"]
    assert [row["rank"] for row in rows] == [1, 2]
    assert rows[0]["demo_ranking_score"] >= rows[1]["demo_ranking_score"]
    assert all(row["feature_source"] == "none" for row in rows)
    assert "not manganese" in response["warning"]


def test_study_area_has_sourced_reference_points(context):
    client, _, _ = context
    area = client.get("/api/v1/exploration/study-area").json()
    assert area["boundary_type"] == "approximate_study_envelope"
    assert len(area["mines"]) == 4
    assert all(
        m["source_url"].startswith("https://environmentclearance.nic.in")
        for m in area["mines"]
    )


def test_export_and_missing_site(context):
    client, _, _ = context
    response = client.get("/api/v1/exploration/sites/zone_a/export?format=csv")
    assert response.status_code == 200 and response.headers["content-type"].startswith(
        "text/csv"
    )
    assert "trained_model" in response.text
    text = client.get("/api/v1/exploration/sites/zone_a/export?format=text")
    assert text.json()["site"]["id"] == "zone_a"
    assert client.get("/api/v1/features/sites/missing/model-input").status_code == 404
    assert (
        client.get("/api/v1/exploration/sites/zone_a/export?format=bad").status_code
        == 422
    )


def test_saved_candidate_and_csv_formula_safety(context):
    client, _, _ = context
    response = client.post(
        "/api/v1/exploration/sites",
        json={
            "name": "=unsafe spreadsheet formula",
            "latitude": 21.6,
            "longitude": 79.4,
            "notes": "Survey candidate only",
        },
    )
    assert response.status_code == 201
    site = response.json()
    assert site["origin"] == "user_location" and site["status"] == "ACTIVE"
    assert client.get("/api/v1/exploration/sites/" + site["id"]).status_code == 200
    export = client.get(
        "/api/v1/exploration/sites/" + site["id"] + "/export?format=csv"
    )
    assert "'=unsafe" in export.text
    assert (
        client.post(
            "/api/v1/exploration/sites",
            json={"name": "outside", "latitude": 0, "longitude": 0},
        ).status_code
        == 422
    )


@pytest.mark.parametrize(
    "changes",
    [
        {"coordinates": {"latitude": 0, "longitude": 0}, "site_id": None},
        {"end_date": "2026-03-01"},
        {
            "aoi": {"coordinates": [[[79, 21.4], [80, 21.4], [80, 22], [79, 21.4]]]},
            "site_id": None,
        },
    ],
)
def test_bounded_extraction_requests(changes):
    payload = {
        "site_id": "zone_a",
        "start_date": "2025-01-01",
        "end_date": "2025-02-01",
        **changes,
    }
    with pytest.raises(ValueError):
        FeatureExtractionRequest(**payload)


def test_reference_parser_no_fabricated_deleted_values():
    text = "\n" * 16 + "0.5 0.02 0\n0.6 *************** 0"
    with pytest.raises(ValueError):
        parse_spectrum(text)


def test_spectral_reference_measured(context):
    client, _, _ = context
    reference = client.get("/api/v1/spectral/reference").json()
    assert reference["is_stub"] is False
    assert reference["status"] == "measured_reference"
    assert len(reference["wavelengths_nm"]) == len(reference["reflectance"]) > 100
    assert reference["sha256_original"]


def test_orchestrator_passes_feature_contract_to_adapter(context):
    from app.api.dependencies import get_prediction_repository

    client, features, _ = context
    captured = []

    class Adapter:
        name = "prospectivity"

        def predict(self, inputs):
            captured.append(inputs)
            from app.schemas.prediction import ModelResult

            return ModelResult(model_name=self.name, value=0.2)

    registry = ModelRegistry()
    registry.adapters["prospectivity"] = Adapter()
    app.dependency_overrides[get_registry] = lambda: registry
    app.dependency_overrides[get_prediction_repository] = lambda: FakeRecords()
    features.save_feature_bundle(
        FeatureBundle(
            feature_id="test",
            site_id="zone_a",
            readiness="ok",
            source="earth_engine",
            is_stub=False,
            extracted_at=utc_now(),
            feature_payload={"ndvi": 0.3},
        )
    )
    prediction = client.post(
        "/api/v1/predictions/exploration", json={"site_id": "zone_a"}
    ).json()
    assert prediction["is_stub"] is True
    assert captured[0].features.feature_payload == {"ndvi": 0.3}
