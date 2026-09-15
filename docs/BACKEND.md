# Backend

## Request lifecycle

Frontend HTTP -> route -> dependency-injected service -> repository/provider/orchestrator -> schema -> HTTP response.

Routers validate contracts and delegate. Services own business rules. Repositories receive a SQLAlchemy Session and own persistence, with no HTTP/GEE/model imports. Providers own external access. PredictionOrchestrator coordinates adapters and normalized output. No infrastructure constructors belong inside business methods.

## Dependency graph

```text
settings -> engine factory -> get_db (one session/request)
settings -> cached GEEProvider
cached ModelRegistry + WeatherProvider
session -> exploration / feature / prediction / job repositories
exploration repo + registry + GEE + weather -> ExplorationService
feature repo + ExplorationService + GEE + settings -> FeatureService
ExplorationService + FeatureService + registry + prediction repo -> PredictionOrchestrator
demo ProductionRepository + orchestrator -> ProductionService
ProductionService + ExplorationService -> DecisionService
job repo + orchestrator -> JobService
guarded engine factory + GEE + registry + settings -> HealthService
```

See app/api/dependencies.py for every provider. Cached settings, engine, registry and GEE provider carry no request session. Request-scoped services/repositories are not cached. get_db flush/commit/rollback behavior is described in DB.md.

## Feature lifecycle

Resolve site or coordinates/AOI -> provider extraction boundary -> unavailable response OR explicit demo fallback -> persist FeatureBundle -> return provenance. No fake real measurements. A source-ready provider is not a source-ready trained model.

## Prediction lifecycle

Resolve site -> get latest materialized features whose extracted_at <= as_of -> optional explicit demo materialization for a current request -> deterministic stub adapters -> persist prediction -> normalized contract.

Historical requests never create fresh features. Coordinate requests currently do not search persisted coordinate bundles: they can explicitly materialize a new demo bundle. Stub adapters intentionally ignore scientific feature payloads; provenance demonstrates linking, not scientific preprocessing. feature_version and data_timestamp expose the selected bundle. Model failure returns missing output/insufficient_real_data gracefully. Requested resolution is metadata only.

## API list

| Method | Path |
| --- | --- |
| GET | /api/v1/health |
| GET | /api/v1/exploration/sites |
| GET | /api/v1/exploration/sites/{site_id} |
| GET | /api/v1/exploration/sites/{site_id}/summary |
| GET | /api/v1/features/sites/{site_id}/availability |
| GET | /api/v1/features/sites/{site_id} |
| POST | /api/v1/features/extract |
| POST | /api/v1/predictions/exploration |
| GET | /api/v1/predictions/{prediction_id} |
| GET | /api/v1/production/overview |
| GET | /api/v1/decision/recommendations |
| POST | /api/v1/jobs |
| GET | /api/v1/jobs/{job_id} |

DB-backed routes require migrations/connection; health always reports availability. Errors use {error: {code, message}}: 404 missing record, 422 validation, 503 database unavailable/schema missing, 500 unexpected failure. Logging records method/path/status/duration_ms without request payloads.

## Files and ownership

app/main.py wires startup, CORS, logging and exceptions. api/ owns contracts/dependencies/routes. core/ owns settings/logging/errors. db/ owns Base/session. models/ contains ORM tables (production.py remains the demo production state contract). schemas/ contains public Pydantic models. repositories/ translates persistence to schemas. providers/ owns GEE/weather. services/ owns exploration/features/prediction/production/decision/jobs/health. ml/ contains protocol/registry/lightweight adapters. jobs/ placeholder runner files are not an operational worker. alembic/ contains schema revisions. scripts/seed_db.py installs idempotent fixtures. tests/ includes isolated fakes and marked database integration tests.

## Run and test

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload
pytest
pytest -m integration
```

Ordinary pytest uses dependency overrides and no live DB/GEE. Explicit integration tests require a migrated local PostgreSQL/PostGIS database, write unique records and roll them back. Use DB.md/GEE.md for setup. See API_ENDPOINT_FLOW_REPORT.md for endpoint walkthroughs.

Real: HTTP boundary, DI, persistence, spatial schema, migration, GEE auth/smoke boundary. Stub: seeded sites, production, recommendations, ML outputs, optional weather provider, demo features. Real batch extraction, validated data ingestion/training, calibrated models and actual-outcome evaluation remain future work.
