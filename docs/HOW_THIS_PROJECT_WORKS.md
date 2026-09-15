# How MOIL Intelligence Works

This is an exploration and mine-planning software prototype, not a validated reserve estimator.

## What you can do

Use the Sausar study map to view four sourced historical MOIL mine reference points, save exploration candidates, queue satellite extraction, inspect source quality and spectra, run a prediction demo, and export candidate details or rankings. The study rectangle is an approximate planning envelope, not an official geological boundary. Ranking halos are discrete demo scores, not a scientifically validated continuous prospectivity raster.

## The pipeline

Streamlit -> FastAPI -> services -> repositories / providers / orchestrator -> PostgreSQL/PostGIS / Earth Engine / model adapters.

For extraction:
1. Streamlit POSTs a location and date interval to /api/v1/features/extract.
2. ExtractionService validates the saved location and persists a queued job; the API returns 202.
3. The separate local extraction worker claims the queued job using a row lock.
4. FeatureService resolves coordinates and asks GEEProvider for environmental measurements.
5. FeatureRepository stores the typed bundle, source quality and spectral samples in PostGIS.
6. Streamlit polls /jobs/{id}, then reads the stored feature bundle.

For prediction:
1. Streamlit POSTs a site_id to /predictions/exploration.
2. PredictionOrchestrator resolves the candidate and reads already-materialized features.
3. ModelInput carries coordinates, features, quality, versions and missing-input warnings to the registered adapters.
4. Stub adapters return deterministic integration outputs. They do not interpret mineral spectra.
5. PredictionRepository saves the normalized, explicitly stub result.

Regular predictions never start a live GEE computation. The frontend never calls a model, database or GEE directly. Real ML preprocessing belongs between the feature bundle and the validated specialist adapter, not in routers.

## Real versus placeholder

Real: HTTP application, native PostgreSQL/PostGIS, Alembic, persistence, development GEE OAuth, bounded satellite extraction, public-domain measured USGS reference spectrum, CSV/text exports.

Unvalidated: saved candidates, seeded software fixtures, geological interpretation of remote-sensing features, ML models, grade, production forecasts, recommendations and ranking scores. A real satellite measurement is not a real manganese prediction. No ground-truth training pipeline, reserve classification or calibrated uncertainty exists.

## How to learn and contribute

Start with one request, not the whole repository. Trace GET /exploration/sites through api/router.py, api/routes/exploration.py, api/dependencies.py, services/exploration_service.py and repositories/exploration.py into models/exploration.py. Compare schemas/exploration.py with Swagger's response. ACTIVE filtering lives in the service so the business rule remains visible.

Then follow POST /features/extract through ExtractionService, scripts/extraction_worker.py, FeatureService, GEEProvider and FeatureRepository. Finally follow PredictionOrchestrator and the typed model input contract.

To replicate this project, build in that same order: schema -> repository -> service -> injected dependency -> route -> test -> HTTP frontend. Start with fakes, then replace persistence, then add a provider behind an explicit boundary.

## Directory ownership

- backend/app/api: thin HTTP routes and the explicit dependency graph.
- backend/app/core: configuration, safe errors and request logging.
- backend/app/db and models: session lifecycle and spatial/JSONB tables.
- backend/app/repositories: persistence only; no external integration or HTTP exceptions.
- backend/app/providers: Earth Engine and weather integration boundaries.
- backend/app/services: application rules, extraction coordination, ranking, exports and prediction orchestration.
- backend/app/ml: lightweight specialist adapters and registry; trained artifacts are still absent.
- backend/app/schemas: stable Pydantic contracts, including the model handoff.
- backend/scripts and alembic: seed, extraction worker, reference downloader and versioned schema changes.
- backend/tests: isolated contract/architecture tests and rollback-only database integration tests.
- frontend/streamlit: API-only map, candidate workspace, spectra, exports and operational demo views.
- data and notebooks: future raw/processed datasets and reproducible scientific investigation; not a production feature source yet.
- docs: these four focused guides. Read ML_CONTRACT before integrating models.

## Remaining milestones

Obtain licensed geology, structural evidence, boreholes/assays and historical operational labels. Define preprocessing and feature versioning with the ML team. Add spatially blocked exploration validation, chronological production validation, uncertainty calibration and human-reviewed recommendations. Only then replace demo rankings with scientifically supported outputs and build a validated prospectivity raster.

Before deployment: production identity/access controls, service-account GEE authentication, quotas, retry/recovery policy and operational monitoring. Development OAuth and this local single-process worker are not a production deployment design.
