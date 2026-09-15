"""Local single-process database-backed extraction worker. No queue infrastructure."""

import argparse
import logging
import time
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.config import get_settings
from app.db.session import get_engine
from app.models.job import Job
from app.ml.registry import ModelRegistry
from app.providers.gee import GEEProvider
from app.providers.weather import WeatherProvider
from app.repositories.exploration import ExplorationRepository
from app.repositories.features import FeatureRepository
from app.repositories.jobs import JobRepository
from app.schemas.jobs import JobRecord, JobStatus
from app.schemas.features import FeatureExtractionRequest
from app.schemas.common import Readiness
from app.services.exploration_service import ExplorationService
from app.services.feature_service import FeatureService


def run_one(engine, provider, settings):
    with Session(engine) as session:
        row = session.scalars(
            select(Job)
            .where(Job.job_type == "feature_extraction", Job.status == "queued")
            .order_by(Job.created_at)
            .with_for_update(skip_locked=True)
            .limit(1)
        ).first()
        if row is None:
            return False
        job = JobRecord.model_validate(row.payload)
        job.status = JobStatus.RUNNING
        JobRepository(session).save(job)
        session.commit()
    try:
        with Session(engine) as session:
            exploration = ExplorationService(
                ExplorationRepository(session),
                ModelRegistry(),
                provider,
                WeatherProvider(),
            )
            features = FeatureService(
                FeatureRepository(session), exploration, provider, settings
            )
            result = features.extract(
                FeatureExtractionRequest.model_validate(
                    job.request.model_dump(exclude={"task"})
                )
            )
            job.result = result
            job.is_stub = result.is_stub
            job.status = (
                JobStatus.COMPLETED
                if result.readiness in (Readiness.OK, Readiness.STUB)
                else JobStatus.FAILED
            )
            job.error = None if job.status == JobStatus.COMPLETED else result.warning
            job.message = "Feature extraction finished."
            JobRepository(session).save(job)
            session.commit()
    except Exception as exc:
        logging.error("Extraction job failed (%s)", type(exc).__name__)
        with Session(engine) as session:
            job.status = JobStatus.FAILED
            job.error = "Extraction failed. Check local worker logs; retry with a smaller date range."
            JobRepository(session).save(job)
            session.commit()
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    settings = get_settings()
    provider = GEEProvider(settings)
    while True:
        worked = run_one(get_engine(), provider, settings)
        if args.once:
            break
        if not worked:
            time.sleep(2)
