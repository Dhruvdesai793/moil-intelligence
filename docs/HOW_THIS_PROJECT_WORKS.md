# How MOIL Intelligence Works

This milestone integrates the application infrastructure. It does not complete the audit's scientifically meaningful first-model milestone. Real mining datasets, baseline comparisons, spatial/temporal validation and trained artifacts remain gates owned by the data/ML work.

## Full flow

```text
Data -> validation/ingestion -> temporal/spatial alignment -> feature engineering
  -> PostgreSQL/PostGIS materialized features -> specialist models
  -> PredictionOrchestrator -> decision/recommendation -> FastAPI
  -> Streamlit -> human decision -> actual outcomes -> evaluation/retraining
```

Today the database, API, dashboard and persistence are real. Sites/production/features used in demos are explicit software fixtures. GEE has real lazy authentication and connectivity checks, but no satellite feature extraction yet. Models are deterministic stubs. Outcomes, ingestion QA and scientific retraining are not implemented.

## Follow one request

When you select a site, Streamlit sends GET /api/v1/exploration/sites. FastAPI creates the dependencies, ExplorationService applies the ACTIVE rule, and ExplorationRepository reads PostgreSQL. Pydantic serializes the response. Streamlit never sees a database session.

Feature extraction is separate. The service resolves a site, asks GEEProvider for an extraction result, and stores an explicitly allowed demo bundle or reports unavailable/no features. A future batch provider will return real, validated provenance through the same boundary.

Prediction resolves the origin and reads materialized features before calling adapters internally. It saves a normalized prediction with versions/timestamps and stub warnings. The frontend gets one response and does not coordinate models. Grade/optional adapter failures withhold outputs. Decisions are human-review suggestions based on demo state.

Jobs demonstrate persistent polling contracts. Immediate jobs execute synchronously; queued jobs have no worker and never advance. Adding a worker later is an implementation milestone, not merely an environment switch.

## Learn and replicate

1. Read schemas/exploration.py and api/routes/exploration.py: identify HTTP input/output.
2. Read ExplorationService: identify the ACTIVE rule and missing-site error.
3. Read ExplorationRepository and models/exploration.py: trace SELECT to schema.
4. Read api/dependencies.py and db/session.py: trace session sharing and transaction boundaries.
5. Follow FeatureService/provider/repository: distinguish external integration from persistence.
6. Follow PredictionOrchestrator and ML registry: understand stable outputs and partial failure.
7. Read tests/fakes.py and test_prototype.py: reproduce behavior without infrastructure.
8. Rebuild a small independent catalog endpoint using schema -> repository -> service -> DI -> route -> tests -> Streamlit HTTP form.

FastAPI/Pydantic/SQL syntax is enough to begin. The next concepts are responsibility boundaries, dependency injection, transactions, migrations, provenance and failure contracts. Learn them by following an existing request rather than memorizing every file.

## Contributor boundaries

Backend contributors own API schemas, routes, explicit DI, services, persistence and provider coordination. Frontend contributors own HTTP-backed views and truthful warnings. Data contributors must provide versioned ingestion contracts, rejected rows, observation timestamps and feature definitions. ML contributors must provide target/as-of definitions, reproducible preprocessing/artifacts, baseline and held-out validation before changing adapters to real models.

Read BACKEND.md for files, DB.md for native setup, GEE.md for OAuth, FRONTEND.md for UI and API_ENDPOINT_FLOW_REPORT.md for each endpoint. Do not put business/SQL/GEE logic in routes or bypass the orchestrator from frontend.

## Local workflow

Install backend plus frontend extra, configure ignored backend/.env, prepare native PostgreSQL, run Alembic and seed fixtures. Authenticate GEE manually only if enabled. Start FastAPI from backend and Streamlit from root. Run pytest, then explicit integration tests, review git diff and commit only intended files.

Never present fixture ranking scores as geological probabilities, confidence, reserves or validated mining recommendations. Store/display WGS84; metre-based operations require metric projection. Materialize satellite features ahead of real inference.
