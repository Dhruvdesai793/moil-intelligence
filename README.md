# MOIL Intelligence

SIH 2026 FastAPI + Streamlit application prototype, guided by SIH26009 Technical Audit v3.4.

The HTTP application flow is implemented and tested. Scientific models, validated feature tables and real MOIL data are not available. All prediction-like outputs are explicitly demo/stub results, never evidence for geological or operational decisions.

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

## Architecture and contributions

Frontend -> FastAPI -> services -> repositories/providers/orchestrator -> specialist adapters.
DecisionService consumes application state; all model execution is coordinated by PredictionOrchestrator.
The intended full flow is Data -> Validation/Ingestion -> temporal/spatial alignment -> Features -> Models -> Orchestrator -> Decisions -> API -> Frontend -> Human action -> Actual outcomes -> Validation/retraining.

Read `docs/HOW_THIS_PROJECT_WORKS.md` for orchestration, `docs/BACKEND.md` and `docs/FRONTEND.md` for file ownership, `docs/DATA.md` for data contracts, and `docs/ARCHITECTURE_DECISIONS.md` for staged choices.
Directory guides stay in docs and cover nested directories.

Real: request validation, HTTP routes, service separation, deterministic fixtures, error handling, logging, polling records, frontend interactions and tests.
Stubbed: sites, production, prospectivity, recommendations and provider availability. Grade is withheld.
Deferred: real ingestion/features, GEE batch exports, PostGIS, validated models, actual outcome capture, retraining, workers and deployment infrastructure.

Add one scoped change with behavioral tests. Do not put business logic or DB/GEE calls in routers. Do not bypass the orchestrator from the frontend. Do not present stub predictions as real scientific output.
