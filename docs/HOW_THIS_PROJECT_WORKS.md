# How This Project Works

This application is a working integration prototype, not a validated scientific system.
The SIH26009 v3.4 audit is the architecture source: sections 2A, 28, 45, 54B/54C, 56 and 61 govern orchestration, provenance, polling, uncertainty, causality and staged delivery.
The current demo exercises software flow in parallel with the ML team's work. It does not count as passing Sprint 1a's data/baseline/signal gate or the real walking-skeleton milestone.

## Why this matters

An integrated application gives frontend/backend contributors stable contracts before data and ML are ready.
Replacing a repository or adapter later should preserve the API and frontend, provided the scientific result retains its meaning and provenance.
Explicit insufficient-evidence states help prevent demo screenshots from being mistaken for mining advice.

## Intended flow

```text
Data -> Validation/Ingestion -> Temporal/spatial alignment -> Feature Engineering
     -> Specialist Models -> Prediction Orchestrator -> Decision/Recommendation
     -> FastAPI -> Frontend -> Human approval/action -> Actual Outcomes
     -> Monitoring/backtesting -> Validation/Retraining
```

Only the application boundary and stub serving path exist today. Ingestion, features, actual outcomes and retraining remain future integrations.

## A request through the current system

1. Streamlit calls FastAPI over HTTP. It never imports backend models or providers.
2. Pydantic validates the selected site/coordinates, requested resolution and prediction cutoff.
3. Thin routers receive injected services from api/dependencies.py.
4. ExplorationService resolves the demo site through ExplorationRepository.
5. PredictionOrchestrator normalizes the input and asks ModelRegistry to invoke prospectivity and grade adapters.
6. Prospectivity returns a stable hash-derived demo ranking score; grade reports not_configured with no grade.
7. Absent or broken adapters produce unavailable output instead of crashing the API.
8. The orchestrator stores a typed normalized result in PredictionRepository and FastAPI serializes it.
9. Streamlit shows the score separately from uncalibrated uncertainty and data/model warnings.

ProductionService reads a demo target and obtains its adapter result through the same orchestrator.
DecisionService uses production risk and active exploration state to propose review actions. No action executes automatically and no expected improvement is claimed.

## Honesty and provenance

Every sample site is explicitly demo data. Prediction-like outputs carry stub labels and warnings.
No real data timestamp, achieved raster resolution, validation metrics, calibrated confidence or geological conclusions are invented.
The shortfall probability is a fixed fixture, not a statistically calibrated forecast.
Grade, recovery, equipment and weather measurements are withheld.

## Future integration

Replace in-memory repositories with PostGIS implementations behind their existing methods.
Introduce validated/materialized feature input in the orchestrator before registering a trained adapter.
GEE stays batch extraction, not a synchronous dashboard dependency.
Models must consume features available at prediction time, and return genuine data/feature/model versions, uncertainty and readiness.
Only enable real outputs after frozen targets, baseline comparisons, spatial holdout for exploration and chronological backtests for production.
Preserve positive/true_negative/background label_source distinctions, WGS84 storage and metric projected CRS for distances.
Weather forecast-at-origin and observed rainfall are distinct; SMAP soil moisture retains its coarse resolution, while NDVI/LST cannot use future satellite observations.
Outcome capture and evaluation require a separately agreed contract; no retraining runs in this prototype.

## Contribution workflow

Read the relevant top-level directory guide. Choose the layer that owns the change, implement one behavior, test both success and unavailable-data paths, and update the contract/docs.
For frontend work use only listed API endpoints. For backend work keep routers declarative, services responsible for rules and repositories responsible for access.
Coordinate new contracts with frontend/ML contributors through OpenAPI and sample requests; do not silently replace a ranking score with a probability.
Start backend/frontend, verify warnings and run pytest before submitting.

## Local workflow

From the repository root:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e ".[frontend]"
uvicorn app.main:app --reload
```

For fish replace activation with `source .venv/bin/activate.fish`.
Backend-only installation is `pip install -e .`; pytest and HTTP testing dependencies are included.
Open http://127.0.0.1:8000/docs. No database, GEE credentials or model artifacts are needed.

In another terminal, from the repository root:

```bash
source backend/.venv/bin/activate
streamlit run frontend/streamlit/app.py --server.address 127.0.0.1
```

Open http://127.0.0.1:8501. From `frontend/streamlit` instead use `streamlit run app.py` with the same environment activated.
Set `MOIL_BACKEND_URL` in the frontend process environment to change the default http://127.0.0.1:8000.
The frontend reads environment variables directly; it does not automatically load the backend .env.

Tests:

```bash
cd backend
source .venv/bin/activate
pytest
```

Backend settings load `backend/.env` when started in backend/. Copy the values from `backend/.env.example` only when needed. Keep .env and credentials untracked.

## Current API

All paths below are under `/api/v1`. Swagger/OpenAPI at `/docs` is the executable contract.

| Method | Path | Purpose |
| --- | --- | --- |
| GET | /health | Runtime status, service, version |
| GET | /exploration/sites | Active demo sites, each with metadata |
| GET | /exploration/sites/{site_id} | Site record or structured 404 |
| GET | /exploration/sites/{site_id}/summary | Site, feature availability, model readiness |
| POST | /predictions/exploration | Backend-orchestrated stub ranking result |
| GET | /production/overview | Stub target, forecast, risk, provenance |
| GET | /decision/recommendations | Rule-supported demo recommendations |
| POST | /jobs | Create immediate or queued job; HTTP 201 |
| GET | /jobs/{job_id} | Poll in-memory status or 404 |

Prediction input is exactly one of `site_id` or `coordinates: {latitude, longitude}`, with optional positive `requested_resolution_m` and timezone-aware, non-future `as_of`. Coordinates are WGS84; polygon AOIs and spatial calculations are deferred.
Requested resolution is recorded but no raster inference occurs; `effective_resolution_m` is null.

Example:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/predictions/exploration \
  -H 'Content-Type: application/json' \
  -d '{"site_id":"zone_a","requested_resolution_m":30}'
```

Prediction responses carry `is_stub`, `source`, `generated_at`, `message`, `warning`, `model_version`, `data_timestamp`, `feature_version`, `prediction_timestamp`, `as_of`, `uncertainty`, and model-level readiness.
A demo ranking score is not a mineral probability. Missing calibrated intervals and actual data timestamps are null.
Site metadata is nested; prediction, production, recommendation and job metadata is at the top level.

Errors use `{"error":{"code":"not_found|validation_error|internal_error|http_error","message":"..."}}`.
Queued jobs have no worker and never advance. Immediate jobs run the same prediction orchestrator synchronously.
Jobs/predictions are process-local, reset on restart/reload, and retain at most 1000 records each. Use one process locally.
