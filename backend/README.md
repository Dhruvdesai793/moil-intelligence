# Backend Local Development

From backend:

```bash
python -m venv .venv
source .venv/bin/activate
# fish: source .venv/bin/activate.fish
pip install -e '.[frontend]'
cp .env.example .env
# Configure native DB according to ../docs/DB.md.
alembic upgrade head
python scripts/seed_db.py
uvicorn app.main:app --reload
pytest
pytest -m integration
```

Optional OAuth: earthengine authenticate; accept external browser. Configure GEE_ENABLED=true only after setup. Missing GEE never blocks startup. DB-backed endpoints require a migrated database and otherwise return a structured 503.

See ../docs/BACKEND.md for responsibilities/dependencies, ../docs/DB.md for PostGIS privilege/geometry rules, ../docs/GEE.md for provider behavior and ../docs/API_ENDPOINT_FLOW_REPORT.md for endpoint walkthroughs.
