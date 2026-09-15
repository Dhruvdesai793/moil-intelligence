# Repository Root

README.md is the clone/run entry point. .gitignore excludes local environments, generated data and credential files. .streamlit/config.toml sets native dashboard colors when launched from root.

backend owns FastAPI, explicit dependencies, ORM persistence, migrations, providers, adapters and tests; read BACKEND.md and DB.md. frontend owns Streamlit HTTP views; read FRONTEND.md. data reserves raw/processed/sample areas; read DATA.md. docs holds contributor explanations including endpoint flows, DB/GEE setup and architecture decisions. notebooks reserves data-team signal checks; read NOTEBOOKS.md.

Root contributors should keep setup commands consistent with working-directory configuration and avoid committing credentials, virtual environments or private data. No Docker/queue/enterprise deployment infrastructure is required for this milestone.
