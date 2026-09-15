# MOIL Intelligence

SIH 2026 application infrastructure: FastAPI + Streamlit + native PostgreSQL/PostGIS + Alembic + official GEE provider boundary.

**Software integration only:** seeded sites, demo feature payloads, production and predictions are not validated MOIL/geological evidence. ML artifacts and training datasets/pipelines are not ready. Real satellite extraction is not implemented.

## Setup

Follow [native database setup](docs/DB.md) first; it covers initdb, role/database creation and privileged first PostGIS migration.

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
# fish: source .venv/bin/activate.fish
pip install -e '.[frontend]'
cp .env.example .env
# Edit DATABASE_URL locally; GEE_ENABLED=false works without OAuth.
alembic upgrade head
python scripts/seed_db.py
uvicorn app.main:app --reload
```

API docs: http://127.0.0.1:8000/docs

Second terminal, from root:

```bash
MOIL_API_BASE_URL=http://127.0.0.1:8000 backend/.venv/bin/streamlit run frontend/streamlit/app.py
```

Dashboard: http://127.0.0.1:8501

Optional GEE OAuth from backend:

```bash
.venv/bin/earthengine authenticate
```

Accept the external browser yourself; enable GEE in .env and restart backend. Project secure-guru-473417-q2. No credentials belong in git.

## Tests

```bash
cd backend
.venv/bin/pytest
.venv/bin/pytest -m integration
```

Ordinary tests need no live DB/GEE. Integration tests need migrated PostgreSQL/PostGIS; writes roll back.

## Architecture and contribution

Frontend -> FastAPI -> services -> repositories/providers/orchestrator -> PostgreSQL/PostGIS/GEE/stub adapters.

Read [project guide](docs/HOW_THIS_PROJECT_WORKS.md), [backend](docs/BACKEND.md), [frontend](docs/FRONTEND.md), [DB](docs/DB.md), [GEE](docs/GEE.md), [endpoint walkthroughs](docs/API_ENDPOINT_FLOW_REPORT.md) and [decisions](docs/ARCHITECTURE_DECISIONS.md).

Routers delegate, services own rules, repositories own database queries, providers own external integration and PredictionOrchestrator owns adapter coordination. Frontend uses only HTTP. Feature demo fallback defaults off. Queued jobs have no worker.
