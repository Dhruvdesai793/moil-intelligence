# Architecture Decisions

1. Preserve audit v3.4's integrated pipeline and backend-only orchestration. FastAPI is the sole frontend boundary; services coordinate rules and repositories/providers isolate infrastructure.
2. Implement software contracts now because ML/data are pending. This is not completion of the audit's scientific milestones. Baselines, leakage controls and validation still gate real serving.
3. Use typed, process-local demo repositories; no PostGIS requirement today. Jobs/predictions retain 1000 records, reset on reload/restart and work in one process only.
4. Use deterministic adapters without artifacts or heavy ML imports. Ranking/production fixtures are explicitly stubbed; grade and uncalibrated uncertainty are withheld.
5. Missing/failed adapters return unavailable outputs. The application and recommendations still operate; failure does not create a fake numeric substitute.
6. GEE/weather expose not_configured availability only. Real GEE remains batch/materialization-first, weather must respect forecast-at-origin parity and soil moisture retains its coarse spatial support.
7. Prediction metadata separates requested cutoff, generation timestamp and actual data timestamp. No data means a null data timestamp; requested resolution is not achieved resolution.
8. Recommendations are demonstration review rules with explicit evidence status and human approval, not causal improvement estimates or automatic mining actions.
9. Jobs define polling without pretending there is a worker. Immediate jobs run synchronously; queued jobs remain queued. Worker infrastructure is a later build task.
10. Streamlit consumes HTTP contracts and is replaceable later. Do not add Docker, Redis, Celery, MLflow, DVC, Kubernetes, auth, WebSocket endpoints, raster serving or React now.
11. One Python environment installs backend/test dependencies plus an optional frontend extra. Streamlit's own transport dependencies are library requirements, not a custom WebSocket API.
12. Actual outcomes, monitoring/retraining and full ingestion/features are deferred contracts. Define them with the data/ML team after real evidence gates rather than exposing nonfunctional endpoints.

## Integration checklist for contributors

Agree on input feature schema, target, as-of availability and true lineage.
Validate inputs, freeze splits, compare baseline and model, check uncertainty/calibration, then register the adapter.
Replace repository access centrally in api/dependencies.py and keep route/response contracts stable.
Version scientific semantics if ranking becomes probability; do not just set is_stub=false on a fixture.
