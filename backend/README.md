# Backend

Run commands and native PostgreSQL/GEE configuration: [local setup](../docs/LOCAL_SETUP.md).

Request flow and directory ownership: [project guide](../docs/HOW_THIS_PROJECT_WORKS.md).

Every API route and the model handoff: [ML contract](../docs/ML_CONTRACT.md).

Scientific data provenance and limitations: [research](../docs/RESEARCH_AND_DATA.md).

From this directory, install `pip install -e '.[frontend]'`, run `alembic upgrade head`, seed with `python scripts/seed_db.py`, start `uvicorn app.main:app --reload`, and run the separate `python scripts/extraction_worker.py`. Ordinary `pytest` does not require live GEE/PostgreSQL. `pytest -m integration` checks native DB persistence with rolled-back writes.
