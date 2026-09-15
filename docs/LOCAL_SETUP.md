# Local Setup

Native Linux PostgreSQL/PostGIS is first-class. No Docker, Redis or Celery.

## PostgreSQL on Arch/CachyOS

```bash
sudo pacman -S postgresql postgis
# Only if /var/lib/postgres/data has NOT already been initialized:
sudo -iu postgres initdb --locale=C.UTF-8 --encoding=UTF8 -D /var/lib/postgres/data
sudo systemctl enable --now postgresql
sudo -iu postgres psql
```

In psql, create the role/database only if absent:

```sql
CREATE USER moil WITH PASSWORD 'moil_dev_password';
CREATE DATABASE moil_intelligence OWNER moil;
```

That password is a development example, not a production secret. Keep your real connection URL in ignored backend/.env.

PostGIS is enabled by migration 0001. That migration may require a privileged role. Prefer running only the initial migration with an administrator DATABASE_URL, then later migrations with the ordinary owner role. Alternatively an administrator can temporarily grant the local role SUPERUSER, run the first migration, then immediately revoke it. Do not leave an application role privileged. Never initialize an existing cluster again.

Verify:

```bash
psql -h localhost -U moil -d moil_intelligence
```

```sql
SELECT PostGIS_Version();
SELECT id, name, origin, ST_SRID(geometry) FROM exploration_sites;
SELECT id, source, feature_version, readiness FROM site_features;
SELECT id, status FROM jobs;
```

Geometry storage/display is WGS84, SRID 4326: coordinates are degrees. For metric distances use geography or an appropriate projected CRS; do not buffer degrees as metres.

## Python and configuration

From the repository root:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
# fish: source .venv/bin/activate.fish
pip install -e '.[frontend]'
cp .env.example .env
```

Configure backend/.env:

```dotenv
DATABASE_URL=postgresql+psycopg://moil:moil_dev_password@localhost:5432/moil_intelligence
GEE_ENABLED=true
GEE_PROJECT_ID=secure-guru-473417-q2
GEE_AUTH_METHOD=oauth
GEE_ALLOW_DEMO_FEATURES=true
GEE_TIMEOUT_SECONDS=60
GEE_MIN_VALID_FRACTION=0.6
```

Authenticate in your external browser, then migrate and seed:

```bash
earthengine authenticate
# Alternative: python -c "import ee; ee.Authenticate()"
alembic upgrade head
python scripts/seed_db.py
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

The provider lazily initializes ee.Initialize(project=settings.gee_project_id). No GEE initialization occurs at module import. Disabled/unavailable/auth_required GEE reports status without breaking API startup. Use the official earthengine-api; geemap is not a backend dependency.

From backend in a second terminal, activate the same virtual environment:

```bash
python scripts/extraction_worker.py
# Process at most one queued extraction, then exit:
python scripts/extraction_worker.py --once
```

From root in a third terminal:

```bash
MOIL_API_BASE_URL=http://127.0.0.1:8000 backend/.venv/bin/streamlit run frontend/streamlit/app.py --server.address 127.0.0.1
```

Dashboard: http://127.0.0.1:8501. API: http://127.0.0.1:8000/docs.

Development OAuth is intentional for local use; deployment requires service-account authentication and access review. No credentials, OAuth tokens, .env or .venv belong in git.

## Verification and troubleshooting

```bash
cd backend
pytest
pytest -m integration
curl http://127.0.0.1:8000/api/v1/health
python scripts/fetch_spectral_reference.py
```

Ordinary tests use fakes and need no live PostgreSQL/GEE. Integration tests require migrated PostgreSQL/PostGIS and roll back writes. The spectrum downloader reproduces the committed public-domain USGS reference; it is not necessary for normal startup.

DB unavailable: verify service, host authentication and DATABASE_URL. Migration permission denied: run the initial extension migration using an administrator connection; keep the app role ordinary. GEE auth_required: rerun browser authentication in the same OS account/virtual environment. GEE unavailable: verify project approval/API enablement and network. A queued extraction not advancing means the local worker is not running. A failed optional product is reported separately, not filled with invented data. Basemap tiles require network and carry attribution.

Real extraction has been smoke-tested locally for exp_001, 2025-01-01 to 2025-04-01; all five product groups returned measured values. Re-run your own smoke check rather than assuming every location/date has coverage.
