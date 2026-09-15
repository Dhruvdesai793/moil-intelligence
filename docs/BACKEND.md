# Backend Directory

This single guide covers backend/ and its nested packages. None of the runtime modules requires a database, external credentials or trained artifacts.

## Files and ownership

| File/group | Purpose | Ways to contribute |
| --- | --- | --- |
| pyproject.toml | Python 3.11+ packaging, backend/test dependencies, frontend extra, pytest discovery | Add only needed dependencies; no heavy ML/geospatial runtime yet |
| .env.example | Local CORS/log settings and frontend URL example | Document optional configuration without secrets |
| README.md | Run instructions and API quick reference | Keep commands synchronized |
| app/main.py | FastAPI title/version, lifespan, CORS, middleware, errors | Improve application lifecycle without external startup requirements |
| app/api/router.py | Versioned route assembly and shared error documentation | Register agreed routes |
| app/api/dependencies.py | Cached process-local service/repository construction | Swap repositories/providers centrally; no runtime work in route imports |
| app/api/routes/health.py | Health response | Preserve simple availability check |
| app/api/routes/exploration.py | Sites, detail, summary | Delegate changes to ExplorationService |
| app/api/routes/predictions.py | Exploration prediction entry point | Keep orchestration backend-only |
| app/api/routes/production.py | Production overview | Delegate to ProductionService |
| app/api/routes/decision.py | Recommendations | Delegate to DecisionService |
| app/api/routes/jobs.py | Job creation/status polling | Preserve HTTP contract when workers arrive |
| app/core/config.py | Pydantic environment settings | Add concise configurable values |
| app/core/logging.py | Method/path/status/duration logging | Avoid logging confidential payloads |
| app/core/exceptions.py | Domain not-found and structured HTTP/error translation | Keep HTTP concepts out of lower layers |
| app/schemas/common.py | Metadata, readiness, provider, health and errors | Preserve explicit provenance |
| app/schemas/exploration.py | Sites/status and feature-readiness summary | Extend validated location contracts carefully |
| app/schemas/prediction.py | Location/request, model results, uncertainty, normalized prediction | Add genuine feature lineage when ML integrates |
| app/schemas/production.py | Demo production contract and risk | Add real forecasts only with validated history |
| app/schemas/decision.py | Priority/actions/drivers/evidence | Distinguish decision support from causal claims |
| app/schemas/jobs.py | Task, queued/completed/failed status and result | Add worker transitions later without changing polling |
| app/services/exploration_service.py | Active filtering, lookup and readiness summary | Add domain rules here |
| app/services/prediction_orchestrator.py | Model coordination, graceful results, prediction recording | Connect materialized features and specialist adapters here |
| app/services/production_service.py | Repository state + orchestrated demo production | Replace fixture probability after calibration |
| app/services/decision_service.py | Rule-supported review recommendations | Require evidence and human review |
| app/services/job_service.py | Immediate/queued lifecycle | Future worker integration; no pretend background execution |
| app/repositories/exploration.py | Sample site access | Replace with validated PostGIS queries |
| app/repositories/production.py | Typed demo production input | Replace with time-bounded operations data |
| app/repositories/predictions.py | Bounded, locked in-memory prediction records | Add persistent audit trail through the same API |
| app/repositories/jobs.py | Bounded, locked in-memory job records | Add persistent polling records later |
| app/ml/base.py | Lightweight model adapter protocol and typed input | Extend real feature input after schema agreement |
| app/ml/registry.py | Adapter lookup and exception-to-unavailable fallback | Register adapters only through backend |
| app/ml/adapters/prospectivity.py | Deterministic hash-derived ranking fixture | Replace after spatial validation; never call it calibrated probability |
| app/ml/adapters/grade.py | Withheld grade, not_configured | Connect validated assay-backed grade model |
| app/ml/adapters/production.py | Deterministic 86% target fixture | Replace after chronological backtesting |
| app/providers/gee.py | Feature provider protocol and not_configured GEE availability | Connect batch-export/materialization status, not synchronous extraction |
| app/providers/weather.py | Weather availability placeholder | Separate observed and forecast-at-origin sources |
| app/models/exploration.py, production.py, prediction.py, job.py | Empty future persistence/domain-model placeholders | Fill only when persistence requires separate models; schemas serve MVP |
| app/jobs/handlers.py, runner.py | Empty deferred worker placeholders | Do not imply queued jobs execute today |
| app/**/__init__.py | Package markers | Keep initialization free of external side effects |
| tests/unit/api/test_health.py | Health contract test | Preserve real runtime response |
| tests/test_prototype.py | Contracts, validation, fallback, jobs, CORS and import boundaries | Cover externally meaningful regressions |

## Rules

Routers contain no business logic and no DB/GEE/model calls.
Services own rules; repositories own access and never import FastAPI.
All model execution goes through PredictionOrchestrator. Optional outputs are withheld when unavailable.
Process caches make repositories shared between requests, not durable across restarts.
The test suite checks import boundaries in addition to behavior.

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
