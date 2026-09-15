# Frontend Directory

## Files and behavior

frontend/streamlit/app.py is the complete prototype UI; it imports httpx, pandas and Streamlit only.
Its HTTP helper applies a timeout and displays friendly connection/validation errors.
No backend module, DB, GEE or individual model is called from this file.

Executive Overview displays health, production fixtures and active demo site count.
Exploration Sites displays a coordinate table/map and selected-site readiness summary.
Exploration Prediction Demo submits a selected site or WGS84 coordinates, optional requested resolution and as-of timestamp, then shows score, uncertainty and provenance.
Production Overview displays the same backend forecast contract.
Recommendations displays actions, drivers, evidence status and human-review status.
Job Status Demo creates immediate/queued records and polls via GET; queued records never advance without a future worker.

All data/model warnings are visible. Maps display invented demo coordinates, not MOIL lease boundaries.
Map basemaps may need internet, but the coordinate table and application/API workflows remain available locally.
The UI must never present a score as calibrated probability or let recommendations execute mining actions.

## Contributing

Add views by consuming agreed FastAPI contracts. Keep business rules, adapter selection and provider calls on the backend.
Test backend-offline behavior and clear stub warnings. Coordinate contract changes through OpenAPI before changing field names.
Replace Streamlit later through the HTTP boundary without moving orchestration into the frontend.
The optional frontend dependency group in backend/pyproject.toml avoids a second dependency list.

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
