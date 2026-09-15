# API Endpoint Flow Report

This report explains how the current MOIL Intelligence backend works endpoint by endpoint, and how to study it so you can rebuild the same style of application later. It is written for someone who knows FastAPI, Pydantic and SQL syntax, but is still learning how a backend codebase is organized.

The current prototype is intentionally local-first. It runs without real ML models, Google Earth Engine, PostGIS or production datasets. Every prediction-like output is marked as stub/demo/placeholder so the application can prove the software flow without pretending to prove scientific results.

## What Is Left

The project is runnable now, but these pieces are still future work:

| Area | Current state | What remains |
| --- | --- | --- |
| Real exploration data | In-memory demo sites | Replace repository fixtures with validated site/AOI data from PostGIS or curated files. |
| GEE features | Provider stubs return `not_configured` | Add batch extraction/materialization pipeline, feature timestamps and provenance. |
| PostGIS | No database required | Add database models, migrations, spatial indexes and repository implementations. |
| ML models | Deterministic stub adapters | Register trained adapters only after validation, calibration and provenance checks. |
| Production forecasting | Software fixture | Connect real production history, chronological validation and uncertainty calibration. |
| Decision engine | Simple demo rules | Add validated decision policies, human approval workflow and evidence tracking. |
| Jobs | In-memory records only | Add durable job storage and a real worker later, only when long-running extraction/training exists. |
| Authentication | Not implemented | Add only after prototype contracts stabilize. |
| Deployment | Local dev only | Add deployment packaging after backend/frontend contracts are stable. |

The most important unfinished scientific work is validation. Real model outputs should not enter the user interface until they have data lineage, training/evaluation dates, uncertainty, known limits and clear evidence status.

## How To Learn This Codebase

Study the backend in this order:

1. Start with [main.py](/home/blixture/PROGRAMMING/HACKATHONS/sih1/moil-intelligence/backend/app/main.py). This is where the FastAPI app is created, middleware is attached, exception handlers are registered and the `/api/v1` router is included.
2. Open [router.py](/home/blixture/PROGRAMMING/HACKATHONS/sih1/moil-intelligence/backend/app/api/router.py). This is the API table of contents. It includes health, exploration, predictions, production, decision and jobs routes.
3. Pick one route file, for example [exploration.py](/home/blixture/PROGRAMMING/HACKATHONS/sih1/moil-intelligence/backend/app/api/routes/exploration.py). Notice that the route does not contain business logic. It accepts input, asks FastAPI for a service dependency and returns a Pydantic response model.
4. Follow the service dependency into [dependencies.py](/home/blixture/PROGRAMMING/HACKATHONS/sih1/moil-intelligence/backend/app/api/dependencies.py). This file wires repositories, services, the model registry and the prediction orchestrator together.
5. Follow the route into the service, such as [exploration_service.py](/home/blixture/PROGRAMMING/HACKATHONS/sih1/moil-intelligence/backend/app/services/exploration_service.py). Services hold business rules such as filtering active sites or raising a domain-level `NotFoundError`.
6. Follow the service into repositories, such as [exploration.py](/home/blixture/PROGRAMMING/HACKATHONS/sih1/moil-intelligence/backend/app/repositories/exploration.py). Repositories own data access. Today they return in-memory demo objects; later they can query PostGIS without changing route code.
7. For prediction endpoints, follow the service into [prediction_orchestrator.py](/home/blixture/PROGRAMMING/HACKATHONS/sih1/moil-intelligence/backend/app/services/prediction_orchestrator.py), then into [registry.py](/home/blixture/PROGRAMMING/HACKATHONS/sih1/moil-intelligence/backend/app/ml/registry.py). The orchestrator coordinates models; the frontend never calls models directly.
8. Read the schema files under [schemas](/home/blixture/PROGRAMMING/HACKATHONS/sih1/moil-intelligence/backend/app/schemas). These files define the public contract. If a frontend page receives a response, its shape should be explainable by one of these schemas.
9. Finally, read [test_prototype.py](/home/blixture/PROGRAMMING/HACKATHONS/sih1/moil-intelligence/backend/tests/test_prototype.py). Tests show the behavior the project promises to keep stable.

A good rule while learning: when you see an endpoint, ask four questions:

| Question | Where to look |
| --- | --- |
| What URL and HTTP method does it expose? | `backend/app/api/routes/*.py` |
| What request/response shape does it promise? | `backend/app/schemas/*.py` |
| What business decision does it make? | `backend/app/services/*.py` |
| Where does data/model output come from? | `backend/app/repositories`, `backend/app/ml`, `backend/app/providers` |

## Backend Layer Pattern

Every endpoint should keep this flow:

```text
HTTP request
-> FastAPI route
-> Pydantic request validation
-> dependency-injected service
-> repository/provider/orchestrator
-> Pydantic response model
-> JSON response
```

Do not put business logic in route files. Route files should be boring in the best possible way. They are the door, not the brain.

Do not put FastAPI imports in repositories. Repositories should be replaceable by database-backed versions later.

Do not let the frontend call ML adapters. The frontend talks only to FastAPI, and FastAPI talks to services.

## App Startup And Cross-Cutting Behavior

### `backend/app/main.py`

This file creates the app:

```python
app = FastAPI(title="MOIL Intelligence API", version="0.1.0", lifespan=lifespan)
```

It also:

- loads settings from `backend/app/core/config.py`
- configures logging during startup
- creates cached services once through `get_services()`
- includes the root API router under `/api/v1`
- adds CORS so local Streamlit can call the backend
- adds request logging middleware
- registers structured exception handlers

The startup path deliberately does not require DB credentials, GEE authentication or ML artifacts. That makes the prototype usable before the scientific/data stack is ready.

### Error Handling

Domain-level missing records raise `NotFoundError`. The handler in [exceptions.py](/home/blixture/PROGRAMMING/HACKATHONS/sih1/moil-intelligence/backend/app/core/exceptions.py) converts that into:

```json
{
  "error": {
    "code": "not_found",
    "message": "..."
  }
}
```

Pydantic validation errors become `422 validation_error`. Unexpected errors become `500 internal_error` without leaking internals to the client.

## Current Endpoint Map

| Method | Path | Main route file | Main service | Purpose |
| --- | --- | --- | --- | --- |
| GET | `/api/v1/health` | `routes/health.py` | none | Confirm API is alive. |
| GET | `/api/v1/exploration/sites` | `routes/exploration.py` | `ExplorationService` | Return active exploration sites. |
| GET | `/api/v1/exploration/sites/{site_id}` | `routes/exploration.py` | `ExplorationService` | Return one site or 404. |
| GET | `/api/v1/exploration/sites/{site_id}/summary` | `routes/exploration.py` | `ExplorationService` | Return site, feature availability and model readiness. |
| POST | `/api/v1/predictions/exploration` | `routes/predictions.py` | `PredictionOrchestrator` | Create a stub exploration prediction. |
| GET | `/api/v1/production/overview` | `routes/production.py` | `ProductionService` | Return stub production forecast overview. |
| GET | `/api/v1/decision/recommendations` | `routes/decision.py` | `DecisionService` | Return stub recommendations. |
| POST | `/api/v1/jobs` | `routes/jobs.py` | `JobService` | Create an in-memory demo job. |
| GET | `/api/v1/jobs/{job_id}` | `routes/jobs.py` | `JobService` | Poll a demo job status. |

## Endpoint Walkthroughs

### GET `/api/v1/health`

Purpose: confirm the backend is running.

Route: [health.py](/home/blixture/PROGRAMMING/HACKATHONS/sih1/moil-intelligence/backend/app/api/routes/health.py)

Response schema: `HealthResponse` in [common.py](/home/blixture/PROGRAMMING/HACKATHONS/sih1/moil-intelligence/backend/app/schemas/common.py)

Flow:

```text
Client
-> GET /api/v1/health
-> health_check()
-> HealthResponse()
-> JSON
```

Example response:

```json
{
  "status": "ok",
  "service": "MOIL Intelligence API",
  "version": "0.1.0"
}
```

Why it matters: frontend and deployment checks can use this before attempting richer API calls.

Future improvement: include optional dependency readiness such as database, feature store and model registry status, but keep those as readiness fields rather than startup blockers.

### GET `/api/v1/exploration/sites`

Purpose: return active exploration sites only.

Route: [exploration.py](/home/blixture/PROGRAMMING/HACKATHONS/sih1/moil-intelligence/backend/app/api/routes/exploration.py)

Service: [exploration_service.py](/home/blixture/PROGRAMMING/HACKATHONS/sih1/moil-intelligence/backend/app/services/exploration_service.py)

Repository: [exploration.py](/home/blixture/PROGRAMMING/HACKATHONS/sih1/moil-intelligence/backend/app/repositories/exploration.py)

Response schema: `list[Site]` in [exploration.py](/home/blixture/PROGRAMMING/HACKATHONS/sih1/moil-intelligence/backend/app/schemas/exploration.py)

Flow:

```text
Client
-> route get_sites()
-> Depends(get_exploration)
-> ExplorationService.get_sites()
-> ExplorationRepository.get_sites()
-> service filters status == ACTIVE
-> list[Site]
```

Important detail: the repository currently returns both active and inactive demo sites. The service applies the business rule that the endpoint should expose active sites only.

Current frontend use: the Streamlit app fetches this list for exploration tables, map-friendly coordinates and site selectors.

Future improvement: let the repository query active sites from PostGIS with filters such as concession, AOI, district, mineral target and data freshness. Keep the response schema stable unless the frontend truly needs new fields.

### GET `/api/v1/exploration/sites/{site_id}`

Purpose: return one exploration site by ID.

Flow:

```text
Client
-> route get_site(site_id)
-> ExplorationService.get_site(site_id)
-> ExplorationRepository.get(site_id)
-> Site or NotFoundError
-> JSON 200 or structured 404
```

If the site is missing, the service raises:

```python
NotFoundError(f"Exploration site '{site_id}' was not found.")
```

The route does not build a 404 itself. This keeps HTTP formatting in the exception layer and business meaning in the service layer.

Future improvement: support stable external IDs from MOIL systems or PostGIS primary keys. Avoid changing the URL shape unless the identity model changes.

### GET `/api/v1/exploration/sites/{site_id}/summary`

Purpose: show whether a site has enough data/model support for prediction.

Flow:

```text
Client
-> route get_summary(site_id)
-> ExplorationService.summary(site_id)
-> get_site(site_id)
-> GEEProvider().availability()
-> WeatherProvider().availability()
-> ModelRegistry readiness check
-> SiteSummary
```

Response includes:

- `site`: the selected site
- `feature_availability`: provider stubs such as GEE and weather, currently `not_configured`
- `model_readiness`: readiness of `prospectivity`, `grade` and `production`
- `metadata`: `source`, `is_stub`, `generated_at`, `message`, `warning`

Why it matters: this endpoint helps the frontend be honest. Before showing a prediction demo, the UI can show that real GEE/data/model integration is pending.

Future improvement: replace provider stubs with real feature availability checks based on materialized features, not live expensive network calls in the route.

### POST `/api/v1/predictions/exploration`

Purpose: create a normalized exploration prediction contract while real ML is unavailable.

Route: [predictions.py](/home/blixture/PROGRAMMING/HACKATHONS/sih1/moil-intelligence/backend/app/api/routes/predictions.py)

Orchestrator: [prediction_orchestrator.py](/home/blixture/PROGRAMMING/HACKATHONS/sih1/moil-intelligence/backend/app/services/prediction_orchestrator.py)

ML registry: [registry.py](/home/blixture/PROGRAMMING/HACKATHONS/sih1/moil-intelligence/backend/app/ml/registry.py)

Request schema: `ExplorationPredictionRequest`

Response schema: `ExplorationPrediction`

Accepted input:

```json
{
  "site_id": "zone_a",
  "requested_resolution_m": 10,
  "as_of": "2026-01-01T00:00:00Z"
}
```

or:

```json
{
  "coordinates": {
    "latitude": 21.0,
    "longitude": 79.0
  }
}
```

Validation rules:

- provide exactly one of `site_id` or `coordinates`
- latitude must be between `-90` and `90`
- longitude must be between `-180` and `180`
- `requested_resolution_m`, if supplied, must be positive
- `as_of`, if supplied, must include a timezone
- `as_of` cannot be in the future

Flow:

```text
Client
-> route predict(request)
-> Pydantic validates request
-> PredictionOrchestrator.exploration_prediction(request)
-> if site_id exists, ExplorationService.get_site(site_id)
-> build ModelInput(coordinates)
-> ModelRegistry.run("prospectivity", inputs)
-> ModelRegistry.run("grade", inputs)
-> normalize result into ExplorationPrediction
-> PredictionRepository.save(result)
-> JSON response
```

Current model behavior:

- `prospectivity` returns a deterministic stub score from coordinates
- `grade` returns `None` with `not_configured`
- missing/broken adapters return `unavailable` instead of crashing

Important response fields:

| Field | Meaning |
| --- | --- |
| `prediction_id` | Unique ID for this generated response. |
| `prospectivity_score` | Demo ranking score, not a scientific probability. |
| `score_type` | Currently `demo_ranking_score`. |
| `status` | `stub` or `insufficient_real_data`. |
| `model_version` | Stub adapter version or `unavailable`. |
| `data_timestamp` | `null` until real data exists. |
| `feature_version` | Placeholder feature version. |
| `prediction_timestamp` | When the API generated the response. |
| `uncertainty` | Explicitly `not_calibrated`. |
| `models` | Per-adapter status and warnings. |
| `is_stub` | Always true in this prototype. |

Future improvement: the orchestrator should pull validated features by site/AOI, call registered trained adapters, attach model/data/feature provenance, and refuse to return scientific-looking scores when evidence is insufficient.

### GET `/api/v1/production/overview`

Purpose: return a demo production forecast overview for the frontend.

Route: [production.py](/home/blixture/PROGRAMMING/HACKATHONS/sih1/moil-intelligence/backend/app/api/routes/production.py)

Service: [production_service.py](/home/blixture/PROGRAMMING/HACKATHONS/sih1/moil-intelligence/backend/app/services/production_service.py)

Repository: [production.py](/home/blixture/PROGRAMMING/HACKATHONS/sih1/moil-intelligence/backend/app/repositories/production.py)

Flow:

```text
Client
-> route overview()
-> ProductionService.overview()
-> ProductionRepository.get_overview()
-> PredictionOrchestrator.production_prediction(target)
-> ModelRegistry.run("production", ModelInput(target))
-> ProductionOverview
```

Current behavior:

- target is a demo fixture
- predicted value is generated by the production stub adapter
- shortfall probability is a fixture
- risk is derived in the service:
  - `HIGH` when predicted is below target
  - `LOW` when predicted reaches/exceeds target
  - `UNKNOWN` when adapter output is unavailable

Future improvement: connect real production history and use chronological validation. Do not keep the hard-coded shortfall probability once real forecasting begins.

### GET `/api/v1/decision/recommendations`

Purpose: return simple recommendation objects based on current stub production/exploration state.

Route: [decision.py](/home/blixture/PROGRAMMING/HACKATHONS/sih1/moil-intelligence/backend/app/api/routes/decision.py)

Service: [decision_service.py](/home/blixture/PROGRAMMING/HACKATHONS/sih1/moil-intelligence/backend/app/services/decision_service.py)

Flow:

```text
Client
-> route recommendations()
-> DecisionService.recommendations()
-> ProductionService.overview()
-> ExplorationService.get_sites()
-> build Recommendations response
```

Current behavior:

- recommendations are rule-based demo text
- evidence status is `stub_rule_supported_only`
- status is `human_review_required`
- warning says no causal improvement or mining safety claim is made

Why it matters: the decision endpoint proves where recommendations will live without letting frontend pages invent their own business rules.

Future improvement: add a transparent decision policy that consumes validated predictions, operational constraints and human review outcomes. Keep evidence status visible.

### POST `/api/v1/jobs`

Purpose: establish the future contract for long-running work without adding Redis, Celery or a worker yet.

Route: [jobs.py](/home/blixture/PROGRAMMING/HACKATHONS/sih1/moil-intelligence/backend/app/api/routes/jobs.py)

Service: [job_service.py](/home/blixture/PROGRAMMING/HACKATHONS/sih1/moil-intelligence/backend/app/services/job_service.py)

Repository: [jobs.py](/home/blixture/PROGRAMMING/HACKATHONS/sih1/moil-intelligence/backend/app/repositories/jobs.py)

Request schema: `JobRequest`

Response schema: `JobRecord`

Example immediate request:

```json
{
  "site_id": "zone_a",
  "task": "exploration_prediction",
  "complete_immediately": true
}
```

Flow when `complete_immediately` is true:

```text
Client
-> route create_job(request)
-> JobService.create(request)
-> create queued JobRecord
-> convert JobRequest into ExplorationPredictionRequest
-> PredictionOrchestrator.exploration_prediction(...)
-> set result
-> status = completed
-> JobRepository.save(job)
```

Flow when `complete_immediately` is false:

```text
Client
-> route create_job(request)
-> JobService.create(request)
-> create queued JobRecord
-> save job
-> queued status remains queued
```

Current limitation: queued jobs do not advance because there is no worker. Records are in memory and reset when the backend restarts.

Future improvement: add durable job storage and a worker only when real long-running tasks exist, such as GEE extraction, model training or batch scoring.

### GET `/api/v1/jobs/{job_id}`

Purpose: poll the status of a previously created demo job.

Flow:

```text
Client
-> route get_job(job_id)
-> JobService.get(job_id)
-> JobRepository.get(job_id)
-> JobRecord or NotFoundError
```

Future improvement: return durable status, timestamps, progress percentage, retry/error metadata and links to result resources.

## How To Add A New Endpoint Later

Use this checklist:

1. Define request and response schemas in `backend/app/schemas`.
2. Add or extend a repository/provider/adapter if new data is needed.
3. Add service logic in `backend/app/services`.
4. Wire the service in `backend/app/api/dependencies.py` if it is new.
5. Add a thin route in `backend/app/api/routes`.
6. Include the route module in `backend/app/api/router.py` if it is new.
7. Add tests in `backend/tests`.
8. Update docs and frontend only after the API contract is clear.

Example shape:

```python
@router.get("/example", response_model=ExampleResponse)
def example(service: ExampleService = Depends(get_example)) -> ExampleResponse:
    return service.example()
```

If the route starts doing filtering, calculations, model selection or database decisions, move that work into a service.

## How To Replace Stubs With Real Pieces

### Replace In-Memory Sites With PostGIS

Keep this call stable:

```python
ExplorationService.get_sites()
```

Replace the repository implementation behind it:

```text
ExplorationRepository.get_sites()
-> currently returns demo list
-> later queries PostGIS
```

The route and frontend should not need to know whether the source is a list or database query.

### Replace Provider Stubs With GEE/Weather Feature Availability

Current provider methods return `ProviderAvailability`. Keep that typed response, but make the provider inspect materialized feature tables or files later.

Avoid doing live GEE extraction inside a normal HTTP request. The audit expects extraction to be staged and controlled, not hidden inside a user click.

### Replace ML Stubs With Real Adapters

Add a real adapter that follows the same interface as the stub adapters:

```text
ModelInput
-> adapter.predict(...)
-> ModelResult
```

Then register it in `ModelRegistry`. The orchestrator should still normalize output into `ExplorationPrediction` or `ProductionOverview`.

Before exposing real predictions, require:

- known model version
- feature version
- data timestamp
- training/evaluation window
- uncertainty or calibration status
- validation summary
- clear warning when evidence is limited

## What To Remember

The backend is built around one simple idea: stable contracts first, real science later.

The frontend should not know how many models exist. It should not know whether data came from memory, PostGIS or GEE. It should call FastAPI and display the response honestly.

The backend should not pretend a stub is a model. It should preserve the shape of the future system while making the current limitations visible.

That discipline is what lets the team build the application layer now and plug in real data/ML later without rewriting every page.
