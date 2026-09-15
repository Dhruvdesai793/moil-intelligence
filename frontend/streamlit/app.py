"""MOIL dashboard. All infrastructure is accessed through FastAPI."""
import html
import os
from datetime import date, timedelta

import httpx
import pandas as pd
import streamlit as st

BASE_URL = os.getenv("MOIL_API_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
st.set_page_config(page_title="MOIL Intelligence", page_icon=":material/landscape:", layout="wide")
st.markdown("""
<style>
:root { --bg:#050607; --surface:#101418; --accent:#0AB6BC; --gold:#C7A96B; --muted:#9CA3AF; }
.stApp { background:#050607; color:#F6F6F6; font-family:Arial,sans-serif; }
[data-testid="stSidebar"] { background:#080A0C; border-right:1px solid #ffffff19; }
.block-container { max-width:1440px; padding-top:2rem; }
h1,h2,h3 { font-family:Arial,sans-serif; letter-spacing:0 !important; }
h1 { font-size:2.5rem !important; font-weight:600 !important; }
h2 { font-size:1.5rem !important; }
h3 { font-size:1.1rem !important; }
.metric { background:rgba(255,255,255,.04); border:1px solid #ffffff19; border-radius:6px;
padding:18px 20px; min-height:110px; backdrop-filter:blur(12px); }
.metric-label { font-size:12px; color:#9CA3AF; margin-bottom:10px; }
.metric-value { font-size:28px; font-weight:600; color:#F6F6F6; overflow-wrap:anywhere; }
.pill { display:inline-block; padding:4px 10px; border:1px solid currentColor; border-radius:4px;
font-size:12px; line-height:20px; white-space:normal; overflow-wrap:anywhere; }
.section { border-top:1px solid #ffffff19; margin-top:26px; padding-top:20px; margin-bottom:16px; }
.section > span { color:#C7A96B; font-size:12px; }
[data-testid="stSidebar"] h1 { font-size:24px !important; }
[data-testid="stAppDeployButton"] { display:none; }
header[data-testid="stHeader"] { background:transparent; }
.brand { color:#0AB6BC; font-size:12px; text-transform:uppercase; }
.stButton button { border-radius:4px; border-color:#0AB6BC55; }
.stButton button[kind="primary"] { background:#0AB6BC; color:#050607; }
[data-testid="stAlert"] { border-radius:4px; }
@media(max-width:640px) { .block-container { padding:1rem; } h1 { font-size:2rem !important; } }
</style>
""", unsafe_allow_html=True)


def api_request(method, path, payload=None):
    try:
        response = httpx.request(method, f"{BASE_URL}/api/v1{path}", json=payload, timeout=15)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as exc:
        try:
            message = exc.response.json().get("error", {}).get("message", "Request rejected.")
        except ValueError:
            message = "Backend returned an invalid response."
        st.error(message)
    except (httpx.RequestError, ValueError):
        st.error("Backend unavailable. Start FastAPI and refresh this view.")
    return None


def api_get(path):
    return api_request("GET", path)


def api_post(path, payload):
    return api_request("POST", path, payload)


def render_status_pill(status):
    color = {"ok": "#10B981", "completed": "#10B981", "ACTIVE": "#10B981",
             "unavailable": "#EF4444", "failed": "#EF4444", "HIGH": "#EF4444"}.get(status, "#F59E0B")
    st.markdown(f'<span class="pill" style="color:{color}">{html.escape(str(status))}</span>',
                unsafe_allow_html=True)


def render_metric_card(label, value):
    st.markdown(f'<div class="metric"><div class="metric-label">{html.escape(str(label))}</div>'
                f'<div class="metric-value">{html.escape(str(value if value is not None else "Unavailable"))}</div></div>',
                unsafe_allow_html=True)


def render_warning(data):
    messages = []
    if data.get("is_stub"):
        messages.append(data.get("message", "Demo fixture only; not scientifically validated."))
    if data.get("warning"):
        messages.append(data["warning"])
    if messages:
        st.warning(" ".join(messages))


def render_section_header(title, number):
    st.markdown(f'<div class="section"><span>{html.escape(number)}</span>'
                f'<h2>{html.escape(title)}</h2></div>', unsafe_allow_html=True)


def render_production(data):
    if not data:
        return
    render_warning(data)
    for column, label, value in zip(st.columns(3), ["Demo target / tonnes", "Demo predicted / tonnes", "Risk"],
                                    [data["target"], data["predicted"], data["risk"]]):
        with column:
            render_metric_card(label, value)
    with st.expander("Production provenance"):
        st.json(data)


st.sidebar.markdown('<p class="brand">MOIL / SIH 2026</p>', unsafe_allow_html=True)
st.sidebar.title("Intelligence")
page = st.sidebar.radio("Workspace", ["Executive Summary", "Exploration", "Features & GEE",
                                     "Prediction Demo", "Production", "Recommendations", "Jobs"])
st.sidebar.caption("Local development")
st.sidebar.caption(BASE_URL)
st.markdown('<p class="brand">Mineral Intelligence / Application Layer</p>', unsafe_allow_html=True)
st.title("MOIL Intelligence")
health = api_get("/health")
if health:
    st.sidebar.caption("API status")
    with st.sidebar:
        render_status_pill(health["status"])
else:
    st.stop()

if page == "Executive Summary":
    st.caption("Operational workspace")
    render_section_header("System Health", "01")
    columns = st.columns(5)
    for column, key in zip(columns, ["database", "postgis", "gee", "model_registry", "status"]):
        with column:
            st.caption(key.replace("_", " ").upper())
            render_status_pill(health[key])
    st.caption(f'Version {health["version"]} / {health["environment"]}')
    render_section_header("Production Overview", "02")
    render_production(api_get("/production/overview"))
    render_section_header("Exploration Sites", "03")
    sites = api_get("/exploration/sites")
    if sites is not None:
        render_metric_card("Active software demo sites", len(sites))
    st.warning("Models and geological evidence remain unvalidated. Outputs support software testing only.")

elif page in ("Exploration", "Features & GEE", "Prediction Demo", "Jobs"):
    sites = api_get("/exploration/sites")
    if not sites:
        st.info("No active sites available. Run migrations and seed the demo database.")
        st.stop()
    names = {item["id"]: item["name"] for item in sites}
    site_id = st.selectbox("Active exploration site", list(names), format_func=names.get)
    if page == "Exploration":
        render_section_header("Exploration Sites", "01")
        render_warning(sites[0]["metadata"])
        frame = pd.DataFrame([{k: v for k, v in item.items() if k != "metadata"} for item in sites])
        st.dataframe(frame, hide_index=True, width="stretch")
        st.map(frame.rename(columns={"latitude": "lat", "longitude": "lon"}))
        render_section_header("Site Intelligence", "02")
        summary = api_get(f"/exploration/sites/{site_id}/summary")
        if summary:
            render_warning(summary["metadata"])
            for column, (name, status) in zip(st.columns(3), summary["model_readiness"].items()):
                with column:
                    st.caption(name.upper())
                    render_status_pill(status)
            with st.expander("Site provenance"):
                st.json(summary)

    elif page == "Features & GEE":
        render_section_header("GEE / Feature Extraction", "01")
        availability = api_get(f"/features/sites/{site_id}/availability")
        if availability:
            provider = availability["provider"]
            render_status_pill(provider["readiness"])
            st.caption(provider["metadata"]["message"])
            render_warning(provider["metadata"])
            if availability["latest_feature"]:
                with st.expander("Latest stored bundle"):
                    st.json(availability["latest_feature"])
        with st.form("feature-extraction"):
            first, second = st.columns(2)
            start = first.date_input("Start date", date.today() - timedelta(days=30))
            end = second.date_input("End date (exclusive)", date.today(), max_value=date.today())
            fallback = st.toggle("Allow demo fixture fallback", value=False)
            submitted = st.form_submit_button("Extract features", icon=":material/layers:", type="primary")
        if submitted:
            result = api_post("/features/extract", {
                "site_id": site_id, "start_date": start.isoformat(), "end_date": end.isoformat(),
                "allow_demo_fallback": fallback})
            st.session_state["feature_result"] = (site_id, result)
        saved = st.session_state.get("feature_result")
        if saved and saved[0] == site_id and saved[1]:
            render_status_pill(saved[1]["readiness"])
            render_warning(saved[1])
            st.json(saved[1])

    elif page == "Prediction Demo":
        render_section_header("Exploration Prediction Demo", "01")
        st.warning("Deterministic model fixtures. No calibrated probability or validated geological conclusion.")
        mode = st.radio("Prediction origin", ["Site", "Coordinates"], horizontal=True)
        payload = {"site_id": site_id}
        if mode == "Coordinates":
            first, second = st.columns(2)
            latitude = first.number_input("Latitude", min_value=-90.0, max_value=90.0, value=21.1458)
            longitude = second.number_input("Longitude", min_value=-180.0, max_value=180.0, value=79.0882)
            payload = {"coordinates": {"latitude": latitude, "longitude": longitude}}
        payload["allow_demo_features"] = st.toggle("Allow demo feature materialization", value=False)
        if st.button("Run demo prediction", icon=":material/science:", type="primary"):
            st.session_state["prediction"] = api_post("/predictions/exploration", payload)
        result = st.session_state.get("prediction")
        if result:
            render_warning(result)
            render_metric_card("Demo ranking score", result["prospectivity_score"])
            st.caption(result["uncertainty"]["message"])
            with st.expander("Prediction provenance", expanded=True):
                st.json(result)

    else:
        render_section_header("Jobs / Pipeline Status", "01")
        immediate = st.toggle("Complete synchronously", value=True)
        st.caption("Queued records persist; no background worker is installed.")
        if st.button("Create demo job", icon=":material/add:", type="primary"):
            job = api_post("/jobs", {"site_id": site_id, "complete_immediately": immediate})
            if job:
                st.session_state["job_id"] = job["job_id"]
        job_id = st.text_input("Job ID", value=st.session_state.get("job_id", ""))
        st.button("Refresh status", icon=":material/refresh:")
        if job_id:
            job = api_get(f"/jobs/{job_id}")
            if job:
                render_status_pill(job["status"])
                render_warning(job)
                st.json(job)

elif page == "Production":
    render_section_header("Production Overview", "01")
    render_production(api_get("/production/overview"))

elif page == "Recommendations":
    render_section_header("Recommendations", "01")
    data = api_get("/decision/recommendations")
    if data:
        render_warning(data)
        for item in data["recommendations"]:
            render_status_pill(item["priority"])
            st.write(" / ".join(item["actions"]))
            st.caption("Drivers: " + " / ".join(item["drivers"]))
            st.caption(f'{item["evidence_status"]} / {item["status"]}')
            st.divider()
