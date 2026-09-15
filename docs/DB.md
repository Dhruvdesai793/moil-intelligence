# PostgreSQL and PostGIS

PostgreSQL persists exploration sites, feature bundles, predictions and jobs across restarts. PostGIS stores spatial geometry and supports future spatial queries. SQLAlchemy translates repository queries; Alembic owns schema changes. Production targets remain software fixtures because no operational dataset exists.

## Native Arch / CachyOS setup

Packages are already installed locally. Teammates can install with:

```bash
sudo pacman -S postgresql postgis
```

Only if the cluster has **not** been initialized (check for /var/lib/postgres/data/PG_VERSION), initialize it once. Never run initdb over an existing cluster:

```bash
sudo -iu postgres initdb --locale=C.UTF-8 --encoding=UTF8 -D /var/lib/postgres/data
sudo systemctl enable --now postgresql
sudo -iu postgres psql
```

Inside psql, create these only if absent:

```sql
CREATE USER moil WITH PASSWORD 'moil_dev_password';
CREATE DATABASE moil_intelligence OWNER moil;
```

The password is a local example, not a shared deployment credential. Use your own password in .env. If the role exists, use psql's `\password moil` interactively rather than placing a real password in shell history.

PostGIS is not a trusted extension: its first installation normally needs a superuser. The migration contains CREATE EXTENSION; do not install it separately. For local setup, the database administrator can grant **temporary** migration privilege:

```sql
ALTER USER moil WITH SUPERUSER;
```

Run the first migration, then immediately remove that privilege from a postgres administrator terminal:

```sql
ALTER USER moil WITH NOSUPERUSER;
```

The application does not need superuser privileges. Alternatively run Alembic under a dedicated privileged migration account and grant moil table/sequence permissions afterward. Do not use that account for the API.

## Configure and migrate

From repository root:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
# fish: source .venv/bin/activate.fish
pip install -e '.[frontend]'
cp .env.example .env
```

Example DATABASE_URL:

```dotenv
DATABASE_URL=postgresql+psycopg://moil:moil_dev_password@localhost:5432/moil_intelligence
```

Edit .env locally. URL-encode special characters in passwords. Configuration is read from backend/.env when running commands from backend. No .env or credentials belong in git.

```bash
alembic upgrade head
python scripts/seed_db.py
alembic current
```

Seeding is idempotent: existing IDs are preserved, not overwritten. Four fixtures are exp_001 and exp_002 ACTIVE, exp_003 UNDER_REVIEW, and exp_004 INACTIVE. Their names/coordinates are software examples, not validated geological or MOIL records.

## Inspect

```bash
psql -h localhost -U moil -d moil_intelligence
```

```sql
SELECT PostGIS_Version();
SELECT id, name, status, ST_AsText(geometry), ST_SRID(geometry) FROM exploration_sites;
SELECT id, source, feature_version, is_stub FROM site_features;
SELECT id, is_stub, created_at FROM predictions ORDER BY created_at DESC;
SELECT id, status FROM jobs;
SELECT tablename FROM pg_tables WHERE schemaname='public';
```

Tables:
- exploration_sites: identity, lifecycle status, region, latitude/longitude, Point and optional Polygon.
- site_features: origin, version, JSONB serialized feature contract, observation dates, extraction timestamp, source/status/warning, spatial origin.
- predictions: normalized JSONB response plus queryable origin/version/stub columns.
- jobs: persisted request/result/status with timestamps. Queued records have no worker.

Geometry is stored/displayed in WGS84 / EPSG:4326. Coordinates are longitude then latitude in PostGIS/GeoJSON, latitude then longitude in the UI fields. Degrees are not metres. Future buffers/distances must use a suitable projected metric CRS (usually local UTM) or PostGIS geography where appropriate, then transform to 4326 for storage/display. No distance/buffer endpoint is implemented here.

## Session lifecycle and contributions

get_db creates one SQLAlchemy Session per request. FastAPI shares that dependency across repositories. Repositories flush writes; get_db commits only after the service returns successfully, before the HTTP response is sent. On errors it rolls back. Health opens a separate guarded connection and reports database/PostGIS status even if unavailable.

ACTIVE filtering stays in ExplorationService to make the user-visible business rule explicit. At large scale move the predicate into a repository query and retain tests for identical behavior.

Add a model, generate/review a new Alembic revision, migrate a disposable database, and add a repository integration test. Do not edit migration 0001 after teammates have applied it. Do not call SQL from routers.

## Troubleshooting

- Service fails: inspect `systemctl status postgresql` and `journalctl -u postgresql`; check initialized cluster and version compatibility after Arch upgrades.
- Password authentication fails: verify role, password, host, port and DATABASE_URL; inspect pg_hba.conf. Do not weaken authentication to trust for convenience.
- postgis.control missing: verify native postgis package matches PostgreSQL version.
- Permission denied creating extension: use a privileged first migration role as above; remove temporary privilege afterward.
- relation does not exist: run alembic upgrade head against the same URL used by API.
- Port 5432 unavailable: check service status and PostgreSQL listen configuration.
- /health checks connection/extension, not schema completeness; DB-backed endpoints report a structured 503 for missing tables.

Future real ingestion needs versioned schemas, rejected-row reports, provenance, timestamp checks and spatial validation. The current feature table is a materialization boundary, not a completed training dataset pipeline.

Setup reference: [Arch PostgreSQL](https://wiki.archlinux.org/title/PostgreSQL), [Arch PostGIS](https://wiki.archlinux.org/title/PostGIS).
