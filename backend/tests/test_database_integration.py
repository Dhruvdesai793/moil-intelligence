"""Run explicitly with pytest -m integration against a migrated local DB."""

from datetime import timedelta
from uuid import uuid4

import pytest
from geoalchemy2.elements import WKTElement
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.session import get_engine
from app.models.exploration import ExplorationSite
from app.repositories.exploration import ExplorationRepository
from app.repositories.features import FeatureRepository
from app.repositories.jobs import JobRepository
from app.repositories.predictions import PredictionRepository
from app.schemas.common import utc_now
from app.schemas.features import FeatureBundle
from app.schemas.exploration import SiteCreate
from app.schemas.jobs import JobRecord, JobRequest
from app.schemas.prediction import Coordinates, ExplorationPrediction


@pytest.mark.integration
def test_postgis_repository_roundtrip():
    # Test writes are rolled back; seeded/project records are not changed.
    with get_engine().connect() as connection:
        transaction = connection.begin()
        with Session(
            bind=connection, join_transaction_mode="create_savepoint"
        ) as session:
            candidate = ExplorationRepository(session).create(
                "test_" + uuid4().hex[:12],
                SiteCreate(
                    name="Rollback-only Sausar candidate", latitude=21.6, longitude=79.4
                ),
            )
            assert (
                candidate.origin == "user_location" and not candidate.metadata.is_stub
            )
            site_id = "test_" + uuid4().hex[:12]
            session.add(
                ExplorationSite(
                    id=site_id,
                    name="Integration test fixture",
                    status="ACTIVE",
                    region="Test",
                    latitude=21,
                    longitude=79,
                    geometry=WKTElement("POINT(79 21)", srid=4326),
                )
            )
            session.flush()
            site = ExplorationRepository(session).get(site_id)
            assert site.latitude == 21 and site.status == "ACTIVE"
            srid = session.scalar(
                text("SELECT ST_SRID(geometry) FROM exploration_sites WHERE id=:id"),
                {"id": site_id},
            )
            assert srid == 4326
            bundle = FeatureBundle(
                feature_id=str(uuid4()),
                site_id=site_id,
                coordinates=Coordinates(latitude=21, longitude=79),
                feature_version="test-v1",
                source="demo_fixture",
                is_stub=True,
                readiness="stub",
                extracted_at=utc_now(),
                feature_payload={"integration_fixture_value": 0.5},
            )
            features = FeatureRepository(session)
            features.save_feature_bundle(bundle)
            assert features.get_latest_for_site(site_id).feature_id == bundle.feature_id
            assert (
                features.get(bundle.feature_id).feature_payload
                == bundle.feature_payload
            )
            assert (
                features.get_latest_for_site(
                    site_id, bundle.extracted_at - timedelta(days=1)
                )
                is None
            )
            assert len(features.list_for_site(site_id)) == 1
            prediction = ExplorationPrediction(
                prediction_id=str(uuid4()),
                site_id=site_id,
                coordinates=bundle.coordinates,
                model_version="stub-v1",
                feature_version=bundle.feature_version,
                as_of=utc_now(),
                models=[],
                is_stub=True,
            )
            predictions = PredictionRepository(session)
            predictions.save(prediction)
            assert predictions.get(prediction.prediction_id).is_stub
            assert any(
                r.prediction_id == prediction.prediction_id
                for r in predictions.list_recent()
            )
            job = JobRecord(
                job_id=str(uuid4()),
                status="queued",
                request=JobRequest(site_id=site_id),
            )
            jobs = JobRepository(session)
            jobs.create(job)
            job.result = prediction
            from app.schemas.jobs import JobStatus

            job.status = JobStatus.COMPLETED
            jobs.update_status(job)
            assert jobs.get(job.job_id).result.prediction_id == prediction.prediction_id
            session.commit()
        transaction.rollback()
