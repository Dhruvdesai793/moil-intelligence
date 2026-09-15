import os

import httpx
import pandas as pd
import streamlit as st

BASE_URL = os.getenv("MOIL_BACKEND_URL", "http://127.0.0.1:8000").rstrip("/")
st.set_page_config(page_title="MOIL Intelligence", layout="wide")


def api(method: str, path: str, payload=None):
    try:
        response = httpx.request(method, f"{BASE_URL}/api/v1{path}", json=payload, timeout=10)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as exc:
        try:
            message = exc.response.json().get("error", {}).get("message", "Request rejected.")
        except ValueError:
            message = "Backend returned an invalid response."
        st.error(message)
    except (httpx.RequestError, ValueError):
        st.error("Cannot reach the backend. Start FastAPI and try again.")
    return None


def warnings(data):
    if data.get("is_stub"):
        st.warning(data.get("message", "Demo only; not scientifically validated."))
    if data.get("warning"):
        st.warning(data["warning"])


def production():
    data = api("GET", "/production/overview")
    if data:
        warnings(data)
        columns = st.columns(3)
        columns[0].metric("Demo target (t)", data["target"])
        columns[1].metric("Demo predicted (t)", data["predicted"] if data["predicted"] is not None else "Unavailable")
        columns[2].metric("Demo shortfall probability", data["shortfall_probability"] if data["shortfall_probability"] is not None else "Unavailable")
        st.write("Risk:", data["risk"])
        with st.expander("Prediction provenance"):
            st.json(data)


def select_site():
    sites = api("GET", "/exploration/sites")
    if not sites:
        st.info("No active sites available.")
        return None
    names = {site["id"]: site["name"] for site in sites}
    return st.selectbox("Exploration site", list(names), format_func=names.get)


st.title("MOIL Intelligence")
st.caption("SIH 2026 | Application prototype")
health = api("GET", "/health")
if health:
    st.sidebar.success(f"Backend: {health['status']} | {health['version']}")
else:
    st.sidebar.error("Backend unavailable")
page = st.sidebar.radio("View", [
    "Executive Overview", "Exploration Sites", "Exploration Prediction Demo",
    "Production Overview", "Recommendations", "Job Status Demo",
])
st.header(page)

if page == "Executive Overview":
    production()
    sites = api("GET", "/exploration/sites")
    if sites is not None:
        st.metric("Active demo sites", len(sites))
    st.warning("Grade, recovery, equipment and weather evidence are unavailable.")
elif page == "Exploration Sites":
    sites = api("GET", "/exploration/sites")
    if sites:
        warnings(sites[0]["metadata"])
        table = pd.DataFrame([{key: value for key, value in site.items() if key != "metadata"}
                              for site in sites])
        st.dataframe(table, hide_index=True, width="stretch")
        st.map(table.rename(columns={"latitude": "lat", "longitude": "lon"}))
        site_id = st.selectbox("Site summary", [site["id"] for site in sites])
        summary = api("GET", f"/exploration/sites/{site_id}/summary")
        if summary:
            warnings(summary["metadata"])
            with st.expander("Feature and model readiness", expanded=True):
                st.json(summary)
elif page == "Exploration Prediction Demo":
    mode = st.radio("Input", ["Site", "Coordinates"], horizontal=True)
    payload = {}
    if mode == "Site":
        site_id = select_site()
        if site_id:
            payload["site_id"] = site_id
    else:
        latitude = st.number_input("Latitude", min_value=-90.0, max_value=90.0, value=21.123)
        longitude = st.number_input("Longitude", min_value=-180.0, max_value=180.0, value=79.123)
        payload["coordinates"] = {"latitude": latitude, "longitude": longitude}
    if st.checkbox("Record requested resolution"):
        payload["requested_resolution_m"] = st.number_input("Requested resolution (m)", min_value=1.0, value=30.0)
    as_of = st.text_input("As-of timestamp (optional, ISO 8601 with timezone)")
    if as_of:
        payload["as_of"] = as_of
    if st.button("Run demo prediction", disabled=not payload):
        result = api("POST", "/predictions/exploration", payload)
        if result:
            st.session_state["prediction"] = result
        else:
            st.session_state.pop("prediction", None)
    if result := st.session_state.get("prediction"):
        warnings(result)
        st.metric("Demo ranking score", result["prospectivity_score"] if result["prospectivity_score"] is not None else "Unavailable")
        st.write("Uncertainty:", result["uncertainty"]["message"])
        with st.expander("Prediction provenance"):
            st.json(result)
elif page == "Production Overview":
    production()
elif page == "Recommendations":
    data = api("GET", "/decision/recommendations")
    if data:
        warnings(data)
        for item in data["recommendations"]:
            st.subheader(item["priority"])
            st.write("Actions:", item["actions"])
            st.write("Drivers:", item["drivers"])
            st.caption(f"{item['evidence_status']} | {item['status']}")
elif page == "Job Status Demo":
    site_id = select_site()
    immediate = st.checkbox("Complete immediately", value=True)
    if st.button("Create demo job", disabled=site_id is None):
        job = api("POST", "/jobs", {"site_id": site_id, "complete_immediately": immediate})
        if job:
            st.session_state["job_id"] = job["job_id"]
    job_id = st.text_input("Job ID", value=st.session_state.get("job_id", ""))
    if st.button("Refresh status", disabled=not job_id):
        st.session_state["job_id"] = job_id
    if job_id:
        job = api("GET", f"/jobs/{job_id}")
        if job:
            warnings(job)
            st.write("Status:", job["status"])
            st.json(job)
