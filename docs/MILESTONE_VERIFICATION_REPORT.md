# Infrastructure Milestone Verification

Verified locally on 2026-09-15. The requested commit message is: Integrate native PostGIS GEE provider and revamp UI. The final commit hash and push confirmation are supplied in the completion message; after cloning use git log -1 --oneline.

## What changed

Native PostgreSQL/PostGIS persistence replaces in-memory exploration, feature, prediction and job storage. Alembic creates extension/tables/indexes. Explicit FastAPI dependencies share one request session. GEE uses real development OAuth and a lightweight connectivity smoke check. Features have an honest extraction/materialization boundary and explicit demo fallback. Streamlit has the Mineral Intelligence theme and API-only workflows.

## Verification evidence

- Ordinary pytest: **34 passed, 1 integration test deselected**.
- pytest -m integration: **1 passed, 34 ordinary tests deselected**.
- Two upstream TestClient deprecation warnings; no failing tests.
- Alembic upgrade head succeeded at revision 0001.
- Alembic check: No new upgrade operations detected.
- PostGIS reports 3.6; geometry SRID roundtrip verified as 4326.
- Seeding rerun succeeded; exactly four demo sites remain.
- Application role rolsuper is false after first migration.
- Live health: database=ok, postgis=ok, gee=ok, model_registry=stub, status=ok.
- ACTIVE list contains exp_001 and exp_002 only.
- Missing site returns 404.
- Real extraction returns not_implemented and no measurements.
- Explicit demo feature bundle persists and links to a stored stub prediction.
- GET prediction returns the exact saved contract.
- Immediate and queued jobs create/get successfully and persist.
- Production/recommendations retain is_stub=true.
- Every Streamlit page passes its AppTest render check against the API.
- Browser screenshots verify dashboard/feature view/exploration table and map.
- Mobile DOM check: viewport and scroll width both 390px, no metric/pill/button overflow.
- git diff --check passed; pip check reports no broken requirements.
- .env, .venv, credential JSON and example service-account JSON are ignored.
- No formatter was configured.

## Dependencies added

SQLAlchemy 2.x, psycopg with binary extra, Alembic, GeoAlchemy2, official earthengine-api, httplib2 (bounded OAuth HTTP transport). FastAPI minimum is 0.121 for function-scoped transaction teardown. Existing Streamlit/httpx/pandas remain the frontend extra. No trained-ML dependencies or Docker/queue infrastructure added.

## PostgreSQL / PostGIS commands

Only initialize a new cluster; never overwrite an existing one:

```bash
sudo -iu postgres initdb --locale=C.UTF-8 --encoding=UTF8 -D /var/lib/postgres/data
sudo systemctl enable --now postgresql
sudo -iu postgres psql
```

Create only if absent:

```sql
CREATE USER moil WITH PASSWORD 'moil_dev_password';
CREATE DATABASE moil_intelligence OWNER moil;
ALTER USER moil WITH SUPERUSER;
```

Run migrations below, then remove temporary privilege from an administrator session:

```sql
ALTER USER moil WITH NOSUPERUSER;
SELECT rolname, rolsuper FROM pg_roles WHERE rolname='moil';
```

This has already been completed locally. The application role has no superuser privilege. PostGIS extension creation is in migration 0001, not a manual separate extension command.

## Environment / install

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
# fish: source .venv/bin/activate.fish
pip install -e '.[frontend]'
cp .env.example .env
```

Edit backend/.env:

```dotenv
DATABASE_URL=postgresql+psycopg://moil:moil_dev_password@localhost:5432/moil_intelligence
GEE_ENABLED=true
GEE_PROJECT_ID=secure-guru-473417-q2
GEE_AUTH_METHOD=oauth
GEE_ALLOW_DEMO_FEATURES=true
```

The password is a local example. Use your own for shared environments. Current local .env is ignored and GEE is enabled after successful manual authentication. Missing .env uses safe GEE-disabled defaults; database-backed endpoints still need configured PostgreSQL.

## GEE commands

```bash
cd backend
.venv/bin/earthengine authenticate
# alternative:
.venv/bin/python -c "import ee; ee.Authenticate()"
```

Accept the external browser yourself. The configured provider initializes project secure-guru-473417-q2 lazily, with bounded HTTP transport. OAuth credential files remain outside git. Live smoke authentication passed.

## Migrate / seed / run / test

From backend with its environment active:

```bash
alembic upgrade head
python scripts/seed_db.py
alembic check
uvicorn app.main:app --reload
```

From root in another terminal:

```bash
MOIL_API_BASE_URL=http://127.0.0.1:8000 backend/.venv/bin/streamlit run frontend/streamlit/app.py
```

Tests:

```bash
cd backend
.venv/bin/pytest
.venv/bin/pytest -m integration
```

Smoke checks:

```bash
curl http://127.0.0.1:8000/api/v1/health
curl http://127.0.0.1:8000/api/v1/exploration/sites
curl http://127.0.0.1:8000/api/v1/features/sites/exp_001/availability
```

Both servers are left running locally until requested to stop.

## Real versus placeholder

Real: FastAPI contracts, request DI/transactions, PostgreSQL persistence, PostGIS geometry/indexes, Alembic, development GEE authentication/smoke boundary, feature storage, Streamlit HTTP flows, tests/docs.

Placeholders: seeded sites, generic demo features, prospectivity/grade/production adapters, production overview and recommendations, optional weather. No calibrated probability, real model confidence, reserve conclusion or validated geological claim exists.

Not implemented: actual satellite batch extraction/export, validated ingestion/ML datasets, scientific preprocessing/training, actual-outcome evaluation/retraining, queued-job worker, full AOI topology/size validation. Coordinates can request new demo bundles but do not look up historical coordinate bundles. Prediction stubs deliberately ignore scientific feature values. Historical site requests exclude bundles extracted after as_of. Meter buffers/distances are not implemented; future calculations require a metric CRS/geography.

ACTIVE filtering stays in ExplorationService for business-rule clarity; repository queries only persist/query data. Optimize the predicate into SQL later with contract tests if needed.

## Files created

- .streamlit/config.toml
- backend/alembic.ini
- backend/alembic/env.py
- backend/alembic/script.py.mako
- backend/alembic/versions/0001_postgis_mvp.py
- backend/app/api/routes/features.py
- backend/app/db/__init__.py
- backend/app/db/base.py
- backend/app/db/session.py
- backend/app/models/feature.py
- backend/app/repositories/features.py
- backend/app/schemas/features.py
- backend/app/services/feature_service.py
- backend/app/services/health_service.py
- backend/scripts/seed_db.py
- backend/tests/__init__.py
- backend/tests/fakes.py
- backend/tests/test_database_integration.py
- docs/DB.md
- docs/GEE.md
- frontend/streamlit/.streamlit/config.toml
- docs/MILESTONE_VERIFICATION_REPORT.md

## Files modified

- .gitignore
- README.md
- backend/.env.example
- backend/README.md
- backend/app/api/dependencies.py
- backend/app/api/router.py
- backend/app/api/routes/health.py
- backend/app/api/routes/predictions.py
- backend/app/core/config.py
- backend/app/core/exceptions.py
- backend/app/main.py
- backend/app/models/exploration.py
- backend/app/models/job.py
- backend/app/models/prediction.py
- backend/app/providers/gee.py
- backend/app/repositories/exploration.py
- backend/app/repositories/jobs.py
- backend/app/repositories/predictions.py
- backend/app/schemas/common.py
- backend/app/schemas/exploration.py
- backend/app/schemas/prediction.py
- backend/app/services/exploration_service.py
- backend/app/services/job_service.py
- backend/app/services/prediction_orchestrator.py
- backend/pyproject.toml
- backend/tests/test_prototype.py
- backend/tests/unit/api/test_health.py
- docs/API_ENDPOINT_FLOW_REPORT.md
- docs/ARCHITECTURE_DECISIONS.md
- docs/BACKEND.md
- docs/DATA.md
- docs/DOCS.md
- docs/FRONTEND.md
- docs/HOW_THIS_PROJECT_WORKS.md
- docs/ROOT.md
- frontend/streamlit/app.py

backend/.env was created locally but is intentionally not tracked.

## Git status

Before commit: the created/modified files above were the intended changes; no .env or credentials were staged. After push the expected clean output is:

```text
## main...origin/main
```

The completion message reports the actual post-push status.

## Tree

Equivalent tree -a -L 5 output below excludes .git, .venv, caches, generated egg metadata and ignored local .env; those are runtime/internal artifacts, not teammate source files. This report was added after the snapshot.

```text
.
├── .gitignore
├── .streamlit
│   └── config.toml
├── README.md
├── backend
│   ├── .env.example
│   ├── README.md
│   ├── alembic
│   │   ├── env.py
│   │   ├── script.py.mako
│   │   └── versions
│   │       └── 0001_postgis_mvp.py
│   ├── alembic.ini
│   ├── app
│   │   ├── __init__.py
│   │   ├── api
│   │   │   ├── __init__.py
│   │   │   ├── dependencies.py
│   │   │   ├── router.py
│   │   │   └── routes
│   │   │       ├── __init__.py
│   │   │       ├── decision.py
│   │   │       ├── exploration.py
│   │   │       ├── features.py
│   │   │       ├── health.py
│   │   │       ├── jobs.py
│   │   │       ├── predictions.py
│   │   │       └── production.py
│   │   ├── core
│   │   │   ├── __init__.py
│   │   │   ├── config.py
│   │   │   ├── exceptions.py
│   │   │   └── logging.py
│   │   ├── db
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   └── session.py
│   │   ├── jobs
│   │   │   ├── __init__.py
│   │   │   ├── handlers.py
│   │   │   └── runner.py
│   │   ├── main.py
│   │   ├── ml
│   │   │   ├── __init__.py
│   │   │   ├── adapters
│   │   │   │   ├── __init__.py
│   │   │   │   ├── grade.py
│   │   │   │   ├── production.py
│   │   │   │   └── prospectivity.py
│   │   │   ├── base.py
│   │   │   └── registry.py
│   │   ├── models
│   │   │   ├── __init__.py
│   │   │   ├── exploration.py
│   │   │   ├── feature.py
│   │   │   ├── job.py
│   │   │   ├── prediction.py
│   │   │   └── production.py
│   │   ├── providers
│   │   │   ├── __init__.py
│   │   │   ├── gee.py
│   │   │   └── weather.py
│   │   ├── repositories
│   │   │   ├── __init__.py
│   │   │   ├── exploration.py
│   │   │   ├── features.py
│   │   │   ├── jobs.py
│   │   │   ├── predictions.py
│   │   │   └── production.py
│   │   ├── schemas
│   │   │   ├── __init__.py
│   │   │   ├── common.py
│   │   │   ├── decision.py
│   │   │   ├── exploration.py
│   │   │   ├── features.py
│   │   │   ├── jobs.py
│   │   │   ├── prediction.py
│   │   │   └── production.py
│   │   └── services
│   │       ├── __init__.py
│   │       ├── decision_service.py
│   │       ├── exploration_service.py
│   │       ├── feature_service.py
│   │       ├── health_service.py
│   │       ├── job_service.py
│   │       ├── prediction_orchestrator.py
│   │       └── production_service.py
│   ├── pyproject.toml
│   ├── scripts
│   │   └── seed_db.py
│   └── tests
│       ├── __init__.py
│       ├── e2e
│       ├── fakes.py
│       ├── integration
│       ├── test_database_integration.py
│       ├── test_prototype.py
│       └── unit
│           ├── api
│           │   └── test_health.py
│           ├── ml
│           ├── repositories
│           └── services
├── data
│   ├── processed
│   │   └── .gitkeep
│   ├── raw
│   │   └── .gitkeep
│   └── samples
│       └── .gitkeep
├── docs
│   ├── API_ENDPOINT_FLOW_REPORT.md
│   ├── ARCHITECTURE_DECISIONS.md
│   ├── BACKEND.md
│   ├── DATA.md
│   ├── DB.md
│   ├── DOCS.md
│   ├── FRONTEND.md
│   ├── GEE.md
│   ├── HOW_THIS_PROJECT_WORKS.md
│   ├── NOTEBOOKS.md
│   └── ROOT.md
├── frontend
│   └── streamlit
│       ├── .streamlit
│       │   └── config.toml
│       └── app.py
└── notebooks
    ├── 00_data_sanity.ipynb
    ├── 01_baseline.ipynb
    └── 02_simple_ml.ipynb

36 directories, 96 files
```
