# MOIL Intelligence

FastAPI + Streamlit exploration workspace with native PostgreSQL/PostGIS, Alembic, real bounded Earth Engine extraction and an API-only frontend.

Explore the approximate Sausar study area, inspect four sourced historical MOIL reference points, save candidates, extract environmental features, compare Sentinel-2 bands with a measured USGS pyrolusite spectrum, and export location details.

**ML and prospectivity rankings remain deterministic demos. Satellite measurements do not establish manganese reserves.**

## Run locally

Follow [local setup](docs/LOCAL_SETUP.md) for native PostgreSQL, OAuth and configuration.

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
# fish: source .venv/bin/activate.fish
pip install -e '.[frontend]'
cp .env.example .env
# Configure DATABASE_URL and GEE_ENABLED locally; never commit credentials.
earthengine authenticate
alembic upgrade head
python scripts/seed_db.py
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Second terminal from backend: `python scripts/extraction_worker.py`.

Third terminal from root: `backend/.venv/bin/streamlit run frontend/streamlit/app.py --server.address 127.0.0.1`.

Dashboard: http://127.0.0.1:8501. API docs: http://127.0.0.1:8000/docs.

Tests from backend: `pytest`. Live rollback-only DB tests: `pytest -m integration`.

## Understand and contribute

Read [how it works](docs/HOW_THIS_PROJECT_WORKS.md), [ML/API contracts](docs/ML_CONTRACT.md), [local setup](docs/LOCAL_SETUP.md), and [research and data limits](docs/RESEARCH_AND_DATA.md).

Frontend -> FastAPI -> services -> repositories/providers/orchestrator -> PostGIS/GEE/adapters. Predictions read stored features and never launch live GEE work. Trained models, labelled geology/operations datasets and scientific validation are still missing.
