# API Endpoint Flow Report

This report explains the current infrastructure milestone. Read it with schemas, routes and services open. API paths share /api/v1. Backend startup does not connect to PostgreSQL or initialize GEE; request dependencies create sessions lazily. Infrastructure status does not imply scientific validation.

## What remains

Real trained adapters, reproducible ML preprocessing/training, validated geological/operational datasets, baselines, spatial holdout, chronological backtesting, calibrated intervals and actual-outcome evaluation remain absent. Real satellite batch extraction is also deliberately not implemented yet: the provider signature, authentication and persistence boundary are ready. Queued jobs need a future worker. Auth/access control remains a later deployment requirement.

## Pattern you can replicate

1. Schema describes legal input and normalized output.
2. Router receives a schema and dependency-injected service.
3. Service applies business rules and coordinates repositories/providers.
4. Repository executes SQL and returns Pydantic contracts.
5. Provider talks to an external system and reports availability honestly.
6. Orchestrator coordinates model adapters and saves one normalized prediction.
7. Request session commits after successful service completion; exceptions roll back.
8. Frontend calls HTTP and renders status, output and provenance separately.

Start by rebuilding a catalog list/detail endpoint. Then add persistence and a migration. Then add a provider boundary returning unavailable. Finally connect an HTTP form. These steps teach backend design beyond FastAPI syntax.

## Endpoint map

| Endpoint | Service | Storage / integration |
| --- | --- | --- |
| GET /health | HealthService | guarded DB/PostGIS checks, GEE availability, registry |
| GET /exploration/sites | ExplorationService | ExplorationRepository |
| GET /exploration/sites/{site_id} | ExplorationService | ExplorationRepository |
| GET /exploration/sites/{site_id}/summary | ExplorationService | repository + GEE/weather/registry |
| GET /features/sites/{site_id}/availability | FeatureService | GEEProvider + FeatureRepository |
| GET /features/sites/{site_id} | FeatureService | FeatureRepository |
| POST /features/extract | FeatureService | GEE boundary + FeatureRepository |
| POST /predictions/exploration | PredictionOrchestrator | features + stub adapters + PredictionRepository |
| GET /predictions/{prediction_id} | PredictionOrchestrator | PredictionRepository |
| GET /production/overview | ProductionService | demo target + stub production adapter |
| GET /decision/recommendations | DecisionService | production/exploration demo state |
| POST /jobs | JobService | JobRepository + optional synchronous prediction |
| GET /jobs/{job_id} | JobService | JobRepository |

## GET /api/v1/health

Route -> get_health -> HealthService.check.

The service calls SELECT 1 and SELECT PostGIS_Version() inside a guarded connection, then asks GEEProvider for availability and inspects registered adapters. Returns HTTP 200 even if DB/GEE unavailable, with status, service, version, environment, database, postgis, gee and model_registry.

Overall status is degraded if DB/PostGIS fail or enabled GEE is unavailable. Disabled GEE is an intentional local configuration. The registry status is stub, not a training/validation success. Health does not verify every table or scientific dataset.

Example:

```json
{"status":"degraded","service":"MOIL Intelligence API","version":"0.1.0",
 "environment":"development","database":"unavailable","postgis":"unavailable",
 "gee":"not_configured","model_registry":"stub"}
```

Contribute by adding bounded diagnostic checks to this service. Keep checks free of expensive extraction and avoid credentials in returned messages.

## GET /api/v1/exploration/sites

Route -> get_exploration -> ExplorationService.get_sites -> ExplorationRepository.list_sites -> SQL SELECT -> Site schemas -> service ACTIVE filter.

Only ACTIVE records are returned. exp_001 and exp_002 are seeded ACTIVE; exp_003 UNDER_REVIEW and exp_004 INACTIVE do not appear. Filtering remains in the service so the business rule is visible. It can move into SQL for scale while keeping the same contract and tests.

Each Site includes id/name/region/status/latitude/longitude and demo metadata. Native PostGIS holds a Point in SRID 4326. Listing does not infer ore potential or reserves.

Contribute by adding tested query parameters/pagination once needed. Do not silently relax the ACTIVE rule.

## GET /api/v1/exploration/sites/{site_id}

Route -> service.get_site -> repository.get -> session primary-key lookup.

The service raises NotFoundError for a missing ID, translated centrally to HTTP 404. Detail lookup can return non-ACTIVE sites if explicitly requested; only the list enforces ACTIVE. Database failure produces 503, not an empty successful list.

Contribute by extending Site/ORM contracts and migrations together. Keep lat/lon and geometry consistent during future write endpoints.

## GET /api/v1/exploration/sites/{site_id}/summary

Service resolves the site, asks injected GEE/weather providers for availability and reports registry readiness. Returns SiteSummary with site, feature_availability, model_readiness and metadata.

No provider is constructed inside this method. Weather is not configured. Grade is unavailable/not configured. Prospectivity and production are stubs. Provider readiness is not proof of a feature dataset or model.

Contribute by adding compact availability summaries, not heavyweight extraction inside a GET route.

## GET /api/v1/features/sites/{site_id}/availability

FeatureService validates the site, obtains provider status and reads latest persisted bundle. Returns site_id/provider/latest_feature. No extraction occurs.

GEE disabled returns not_configured. OAuth missing returns auth_required. Project/network failures return unavailable. A stored demo bundle can exist even when GEE is disabled, so read both provider and bundle metadata.

Contribute by adding source-specific support/timestamp metadata after feature definitions are frozen.

## GET /api/v1/features/sites/{site_id}

Service validates the site, then repository lists its bundles newest first. JSONB is deserialized into FeatureBundle models. Unknown site is 404; no bundles is an empty list.

Contribute pagination and feature-version filtering when volume needs it. The current latest query is site-based, not a spatial nearest-feature lookup.

## POST /api/v1/features/extract

Example:

```json
{"site_id":"exp_001","start_date":"2025-01-01","end_date":"2025-02-01",
 "allow_demo_fallback":false}
```

Exactly one origin is required: site_id, coordinates, or aoi. Coordinates validate geographic ranges. Polygon AOIs validate closed rings and WGS84 positions; full topology validation is deferred. Dates require start < end <= today, end exclusive.

FeatureService resolves a site into coordinates, calls point/AOI provider method, attaches request provenance, and persists a successful bundle. GEEProvider lazily authenticates/checks connectivity but currently returns not_implemented or unavailable with **no measurements**.

Demo fallback only runs when allow_demo_fallback=true and GEE_ALLOW_DEMO_FEATURES=true. A generic integration_fixture_value payload is marked is_stub=true, source=demo_fixture, readiness=stub, and warning that it was not extracted from Earth Engine. The repository stores origin geometry and serialized contract in PostgreSQL.

Unavailable/no-extraction responses have no feature_id or extracted_at and an empty payload. HTTP 200 is a successfully reported capability result, not extraction success. Clients must inspect readiness.

Contribute real batch extraction through GEEProvider after feature definitions/QA are agreed. Do not generate fake NDVI values or issue long raster computations from serving requests.

## POST /api/v1/predictions/exploration

Examples:

```json
{"site_id":"exp_001","allow_demo_features":false}
```

```json
{"coordinates":{"latitude":21.1458,"longitude":79.0882}}
```

Schema requires exactly one site or coordinates. Optional as_of must include timezone and cannot be future. requested_resolution_m must be positive; it is recorded, not executed.

Orchestrator:
1. Resolve site through ExplorationService.
2. Select latest materialized site bundle with extracted_at <= as_of.
3. If no bundle, optionally request explicit demo materialization for a current request. Historical requests never create fresh features.
4. Pass coordinates to deterministic prospectivity/grade adapters through ModelRegistry.
5. Normalize output with prediction ID, feature/model versions, timestamps, uncertainty, source and warnings.
6. Save through PredictionRepository; request transaction commits.
7. Return the same stable contract to Streamlit.

Coordinate requests do not retrieve prior coordinate bundles yet. Stub adapters ignore unvalidated scientific payloads. Linking demonstrates software provenance, not real feature preprocessing.

Response is always is_stub=true, source=stub_models, score_type=demo_ranking_score, status=insufficient_real_data. Score is not calibrated probability. Grade may be null. Missing/broken adapters return unavailable results without crashing the core API. Uncertainty method is not_calibrated and intervals are null.

Contribute real adapters only with reproducible validated artifacts and an agreed feature contract. Preserve adapter failure handling, provenance and historical time rules.

## GET /api/v1/predictions/{prediction_id}

Orchestrator delegates read to PredictionRepository and raises NotFoundError if absent. Returns the exact stored normalized prediction from JSONB, preserving timestamps and warnings.

Contribute a history endpoint/pagination if needed; add access control before any sensitive operational deployment.

## GET /api/v1/production/overview

ProductionService reads a demo target from ProductionRepository, asks orchestrator for the stub production adapter, computes HIGH/LOW/UNKNOWN risk and returns ProductionOverview.

The current target 1000, forecast 860 and shortfall probability are software fixtures. No real operational database table or forecast performance exists. Missing model returns null predicted/probability and UNKNOWN risk.

Contribute operational ingestion only after schema/as-of semantics are agreed. Train/validate with chronological backtests; do not treat synthetic output as mine performance.

## GET /api/v1/decision/recommendations

DecisionService combines production overview and active-site count into rule-based demo suggestions. Returns priority/actions/drivers/evidence_status/status and warnings.

Recommendations require human review. No quantified causal improvement or autonomous mining action is claimed.

Contribute explicit rule/evidence definitions and tests. Feature importance alone cannot prove an intervention effect.

## POST /api/v1/jobs

```json
{"site_id":"exp_001","complete_immediately":true}
```

JobService validates the origin, creates an ID, runs a prediction synchronously if requested, then persists the JobRecord. Returns HTTP 201. Immediate completion is not asynchronous processing.

complete_immediately=false stores queued; no worker advances it. Records persist across backend restarts. Requests/results are JSONB; relational status supports future polling queries.

Contribute a worker only as a separate staged task with claimed/running/failed/retry semantics and transaction tests. Current job task supports exploration_prediction only; real GEE batch jobs remain future work.

## GET /api/v1/jobs/{job_id}

JobService -> JobRepository.get -> stored JobRecord. Unknown ID returns 404. Frontend refresh polls via HTTP. No WebSockets or background infrastructure are needed for this contract.

## Verification and setup

```bash
cd backend
.venv/bin/pytest
.venv/bin/pytest -m integration
.venv/bin/alembic upgrade head
.venv/bin/python scripts/seed_db.py
```

Ordinary tests override repositories/providers and do not require DB/OAuth. Integration tests exercise real PostGIS geometry, JSONB feature/prediction/job roundtrips and roll back unique test fixtures. Setup details: DB.md and GEE.md.

## How to add an endpoint

Write a concise Pydantic contract, a persistence query if needed, a service method, a DI provider and a thin route. Add tests for legal input, missing data and failure states. Add frontend HTTP use only after the backend contract works. Document source/stub/version/timestamp behavior.

Never import SQLAlchemy/GEE/ML into route modules. Never construct repositories/providers in routers or business methods. Never make frontend call models directly.
