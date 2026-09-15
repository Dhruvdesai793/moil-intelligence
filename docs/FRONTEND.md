# Frontend

Streamlit renders a local operational dashboard and calls FastAPI only. It imports no backend services, DB drivers, GEE or ML. API availability and scientific evidence are separate concepts.

The custom Mineral Intelligence theme uses charcoal (#050607/#101418), teal (#0AB6BC), mineral gold (#C7A96B), white text, grey labels, green/red/amber status colors and compact Arial/system typography. Thin borders and restrained translucent metric surfaces keep the dashboard readable.

Sections: Executive Summary with System Health; Exploration Sites and Site Intelligence; Features & GEE; Prediction Demo; Production; Recommendations; Jobs. Pages group these sections to keep repeated workflows manageable.

app.py contains api_get/api_post HTTP helpers, render_status_pill, render_metric_card, render_warning and render_section_header. HTTP errors become friendly messages. Backend unavailable stops dependent views. Empty active-site results explain migration/seeding. Site selection comes from backend ACTIVE sites. Feature fallback and prediction feature materialization default off. Warnings remain visible. Dynamic HTML values are escaped.

## Run

Install the frontend extra into the backend virtual environment:

```bash
cd backend
pip install -e '.[frontend]'
cd ..
MOIL_API_BASE_URL=http://127.0.0.1:8000 backend/.venv/bin/streamlit run frontend/streamlit/app.py
```

Or run from frontend/streamlit with the virtual environment active: streamlit run app.py. .streamlit/config.toml in that directory supplies native dark widget styling; app.py supplies custom CSS from either working directory. MOIL_API_BASE_URL is a process environment variable; Streamlit does not automatically load backend/.env.

Use st.map for demo site locations; the basemap may need internet. Location fixtures are not reserve evidence. GEE unavailable does not crash the page: provider status and warning are shown; extraction produces no real payload unless a future provider implements it. Demo fallback is always visibly marked.

Contribute here by improving layout, tables/forms and error states while retaining the API-only boundary. Extend Pydantic backend contracts before adding UI fields. Test every page with backend available/unavailable, empty sites, GEE disabled and demo mode. Do not hide is_stub or uncertainty warnings to make output look more convincing.
