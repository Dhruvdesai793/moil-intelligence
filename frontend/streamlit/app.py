"""API-only exploration workspace. Scientific outputs remain explicitly unvalidated."""

import html
import os
from datetime import date, timedelta
import folium
import httpx
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from streamlit_folium import st_folium

BASE_URL = os.getenv("MOIL_API_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
st.set_page_config(
    page_title="MOIL Intelligence", page_icon=":material/terrain:", layout="wide"
)
st.markdown(
    """
<style>
.stApp{background:#080a0c;color:#f6f6f6}
.block-container{padding-top:3.5rem;max-width:1600px}
h1,h2,h3{letter-spacing:0!important} h1{font-size:2.3rem!important}
[data-testid="stSidebar"]{background:#101418;border-right:1px solid #ffffff18}
[data-testid="stMetric"]{border-bottom:1px solid #ffffff20;padding:12px 0}
[data-testid="stMetricValue"]{font-size:1.65rem}
.pill{display:inline-block;padding:3px 9px;border:1px solid #ffffff25;border-radius:4px;font-size:12px;color:#0ab6bc}
.brandline{color:#9ca3af;font-size:13px;margin-bottom:12px}
.section-title{border-top:1px solid #ffffff20;padding-top:18px;margin-top:18px}
[data-testid="stHorizontalBlock"]{gap:1.2rem}
button{border-radius:5px!important}
iframe{border:1px solid #ffffff18!important;border-radius:4px}
.st-key-explore_layout [data-testid="stHorizontalBlock"]{flex-wrap:wrap!important}
.st-key-explore_layout [data-testid="stColumn"]:first-child{min-width:min(100%,360px)!important}
.st-key-explore_layout [data-testid="stColumn"]:last-child{min-width:min(100%,240px)!important}
@media(max-width:650px){.block-container{padding:1rem}h1{font-size:1.8rem!important}}
</style>""",
    unsafe_allow_html=True,
)


def api_get(path, raw=False):
    try:
        response = httpx.get(BASE_URL + "/api/v1" + path, timeout=20)
        response.raise_for_status()
        return response.text if raw else response.json()
    except (httpx.HTTPError, ValueError):
        st.error(
            "Backend request unavailable. Check the API connection or system health."
        )
        return None


def api_post(path, payload):
    try:
        response = httpx.post(BASE_URL + "/api/v1" + path, json=payload, timeout=20)
        if response.status_code == 422:
            st.error("Please check the location and date inputs.")
            return None
        response.raise_for_status()
        return response.json()
    except (httpx.HTTPError, ValueError):
        st.error("Could not complete the request. Check system health and try again.")
        return None


def render_status_pill(status):
    st.markdown(
        '<span class="pill">' + html.escape(str(status)) + "</span>",
        unsafe_allow_html=True,
    )


def render_metric_card(label, value, delta=None):
    st.metric(label, value, delta)


def render_warning(value):
    if value:
        if isinstance(value, dict):
            message = value.get("warning") or value.get("metadata", {}).get("warning")
            if value.get("is_stub"):
                message = message or "Demo output, not a validated scientific result."
        else:
            message = str(value)
        if message:
            st.warning(message)


def render_section_header(title):
    st.markdown(
        '<h3 class="section-title">' + html.escape(title) + "</h3>",
        unsafe_allow_html=True,
    )


def queue_extraction(site_id, start, end, allow_demo):
    job = api_post(
        "/features/extract",
        {
            "site_id": site_id,
            "start_date": str(start),
            "end_date": str(end),
            "allow_demo_fallback": allow_demo,
        },
    )
    if job:
        st.session_state["extraction_job"] = job["job_id"]
        st.success("Extraction queued. Open Pipeline to follow its progress.")


def show_job(job_id):
    record = api_get("/jobs/" + job_id)
    if not record:
        return
    render_status_pill(record["status"])
    st.caption("Job " + record["job_id"])
    if record.get("error"):
        st.error(record["error"])
    result = record.get("result")
    if result:
        render_warning(result)
        st.json(result, expanded=False)
    if record["status"] in ("queued", "running"):
        st.info("Extraction runs in the local worker. Refresh to check progress.")


health = api_get("/health")
with st.sidebar:
    st.title("MOIL")
    st.caption("MINERAL INTELLIGENCE")
    page = st.radio(
        "Workspace",
        ["Explore", "Locations", "Production", "Pipeline", "System"],
        label_visibility="collapsed",
    )
    st.divider()
    render_status_pill(health["status"] if health else "API unavailable")
    st.caption("Sausar belt study area")
    st.caption("ML: demo adapters only")
    st.link_button("API reference", BASE_URL + "/docs", icon=":material/open_in_new:")
if not health:
    st.title("MOIL Intelligence")
    st.info("Start FastAPI on " + BASE_URL + " to connect this workspace.")
    st.stop()

sites = api_get("/exploration/sites") or []
area = api_get("/exploration/study-area")
rankings = api_get("/exploration/rankings") or {"locations": []}
rank_by_id = {r["site_id"]: r for r in rankings["locations"]}
site_by_id = {s["id"]: s for s in sites}

if page == "Explore":
    st.markdown(
        '<div class="brandline">EXPLORATION WORKSPACE / SAUSAR BELT</div>',
        unsafe_allow_html=True,
    )
    st.title("MOIL Intelligence")
    st.caption("Surface evidence, exploration candidates and traceable model inputs.")
    top = st.columns(4)
    with top[0]:
        render_metric_card("Saved candidates", len(sites))
    with top[1]:
        render_metric_card("Reference mines", len(area["mines"]) if area else 0)
    with top[2]:
        render_metric_card(
            "Measured sites",
            sum(r["feature_source"] == "earth_engine" for r in rankings["locations"]),
        )
    with top[3]:
        render_metric_card("Model validation", "Pending")
    with st.container(key="explore_layout"):
        left, right = st.columns([2.2, 1])
    with left:
        st.subheader("Sausar study map")
        baseline = st.segmented_control(
            "Basemap",
            ["Streets", "Satellite"],
            default="Streets",
            label_visibility="collapsed",
        )
        map_ = folium.Map(
            location=[21.65, 79.6], zoom_start=8, tiles=None, control_scale=True
        )
        if baseline == "Satellite":
            folium.TileLayer(
                "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
                attr="Esri, Maxar, Earthstar Geographics",
                name="Satellite",
            ).add_to(map_)
        else:
            folium.TileLayer("OpenStreetMap", name="Streets").add_to(map_)
        if area:
            west, south, east, north = area["bounds"]
            folium.Rectangle(
                [[south, west], [north, east]],
                color="#0ab6bc",
                weight=1,
                fill=False,
                tooltip="Approximate Sausar study envelope; not an official geological boundary",
            ).add_to(map_)
            mines = folium.FeatureGroup(name="MOIL reference mines")
            for mine in area["mines"]:
                popup = (
                    "<b>"
                    + html.escape(mine["name"])
                    + "</b><br>"
                    + html.escape(mine["coordinate_method"])
                    + '<br><a href="'
                    + html.escape(mine["source_url"], quote=True)
                    + '" target="_blank">Published source</a><br>Historical reference point, not a lease boundary.'
                )
                folium.Marker(
                    [mine["latitude"], mine["longitude"]],
                    tooltip=mine["name"],
                    popup=folium.Popup(popup, max_width=280),
                    icon=folium.Icon(color="orange", icon="industry", prefix="fa"),
                ).add_to(mines)
            mines.add_to(map_)
        candidates = folium.FeatureGroup(name="Saved exploration candidates")
        demo = folium.FeatureGroup(name="Prospectivity DEMO / unvalidated")
        for site in sites:
            row = rank_by_id.get(site["id"], {})
            score = row.get("demo_ranking_score")
            folium.CircleMarker(
                [site["latitude"], site["longitude"]],
                radius=6,
                color="#0ab6bc",
                fill=True,
                tooltip=site["name"],
                popup=html.escape(site["name"]) + " / " + html.escape(site["origin"]),
            ).add_to(candidates)
            if score is not None:
                color = (
                    "#10b981"
                    if score >= 0.67
                    else "#f59e0b"
                    if score >= 0.34
                    else "#ef4444"
                )
                folium.CircleMarker(
                    [site["latitude"], site["longitude"]],
                    radius=17,
                    color=color,
                    weight=1,
                    fill=True,
                    fill_opacity=0.18,
                    tooltip=f"{site['name']}: demo score {score:.2f}; not geological likelihood",
                ).add_to(demo)
        demo.add_to(map_)
        candidates.add_to(map_)
        folium.LayerControl(collapsed=True).add_to(map_)
        event = st_folium(
            map_,
            height=480,
            width=None,
            use_container_width=True,
            key="sausar_map",
            returned_objects=["last_clicked"],
        )
        if event and event.get("last_clicked"):
            st.session_state["map_point"] = event["last_clicked"]
        st.caption(
            "Gold: sourced MOIL reference points. Cyan: candidates. Coloured halos: deterministic demo ordering, not a validated mineral raster."
        )
        if area:
            st.caption(area["warning"])
    with right:
        st.subheader("Location intelligence")
        selected = (
            st.selectbox(
                "Saved location",
                list(site_by_id),
                format_func=lambda x: site_by_id[x]["name"],
            )
            if sites
            else None
        )
        if selected:
            site = site_by_id[selected]
            st.caption(f"{site['latitude']:.5f} N · {site['longitude']:.5f} E")
            row = rank_by_id.get(selected, {})
            render_status_pill(row.get("feature_readiness", "not_extracted"))
            st.write("Candidate only. No confirmed deposit or reserve classification.")
            availability = api_get("/features/sites/" + selected + "/availability")
            if availability:
                render_status_pill("GEE: " + availability["provider"]["readiness"])
            if st.button("Check GEE", icon=":material/cloud_sync:"):
                checked = api_post("/features/provider/check", {})
                if checked:
                    render_status_pill(checked["readiness"])
                    render_warning(checked["metadata"])
        point = st.session_state.get("map_point", {"lat": 21.65, "lng": 79.6})
        render_section_header("Save a candidate")
        with st.form("new_location", clear_on_submit=False):
            name = st.text_input("Location name", placeholder="Survey candidate name")
            latitude = st.number_input(
                "Latitude",
                min_value=21.1,
                max_value=22.3,
                value=min(22.3, max(21.1, float(point["lat"]))),
                format="%.6f",
                key="new_lat_" + str(point["lat"]),
            )
            longitude = st.number_input(
                "Longitude",
                min_value=78.5,
                max_value=80.7,
                value=min(80.7, max(78.5, float(point["lng"]))),
                format="%.6f",
                key="new_lon_" + str(point["lng"]),
            )
            notes = st.text_area("Field notes", height=80)
            save = st.form_submit_button(
                "Save location", icon=":material/add_location_alt:"
            )
        if save:
            result = api_post(
                "/exploration/sites",
                {
                    "name": name,
                    "latitude": latitude,
                    "longitude": longitude,
                    "notes": notes,
                },
            )
            if result:
                st.success("Candidate saved.")
                st.rerun()
    if selected:
        tabs = st.tabs(
            ["Satellite features", "Spectral comparison", "Model handoff", "Export"]
        )
        bundle = (availability or {}).get("latest_feature")
        with tabs[0]:
            controls = st.columns([1, 1, 1.4])
            with controls[0]:
                start = st.date_input(
                    "Start date",
                    date(2025, 1, 1),
                    max_value=date.today() - timedelta(days=1),
                )
            with controls[1]:
                end = st.date_input(
                    "End date (exclusive)", date(2025, 4, 1), max_value=date.today()
                )
            with controls[2]:
                allow = st.toggle("Allow demo fallback", value=False)
            if st.button(
                "Extract satellite features",
                icon=":material/satellite_alt:",
                type="primary",
            ):
                queue_extraction(selected, start, end, allow)
            if bundle:
                render_warning(bundle)
                st.caption(
                    "Source: "
                    + bundle["source"]
                    + " · "
                    + bundle["feature_version"]
                    + " · "
                    + str(bundle.get("extracted_at"))
                )
                st.dataframe(
                    pd.DataFrame(
                        [
                            {
                                "feature": k,
                                "value": str(v) if v is not None else "Missing",
                            }
                            for k, v in bundle["feature_payload"].items()
                        ]
                    ),
                    hide_index=True,
                    width="stretch",
                )
                st.dataframe(
                    pd.DataFrame(
                        [
                            {"product": k, **v}
                            for k, v in bundle.get("quality", {}).items()
                        ]
                    ),
                    hide_index=True,
                    width="stretch",
                )
            else:
                st.info(
                    "No stored feature bundle yet. Extract a date window to materialize measurements."
                )
        with tabs[1]:
            reference = api_get("/spectral/reference")
            figure = go.Figure()
            if reference and reference.get("wavelengths_nm"):
                figure.add_trace(
                    go.Scatter(
                        x=reference["wavelengths_nm"],
                        y=reference["reflectance"],
                        name="USGS pyrolusite HS138 / laboratory",
                        line=dict(color="#c7a96b", width=1.5),
                    )
                )
            bands = (bundle or {}).get("spectral_bands", [])
            if bands:
                figure.add_trace(
                    go.Scatter(
                        x=[b["wavelength_nm"] for b in bands],
                        y=[b["reflectance"] for b in bands],
                        text=[b["band"] for b in bands],
                        name="Location / Sentinel-2 broadband",
                        mode="markers+lines",
                        connectgaps=False,
                        line=dict(color="#0ab6bc", width=2),
                        marker=dict(size=8),
                    )
                )
            figure.update_layout(
                template="plotly_dark",
                paper_bgcolor="#080a0c",
                plot_bgcolor="#080a0c",
                height=360,
                margin=dict(l=20, r=20, t=25, b=20),
                xaxis_title="Wavelength (nm)",
                yaxis_title="Reflectance (unitless)",
                legend=dict(orientation="h", y=1.15),
                font=dict(color="#f6f6f6"),
            )
            st.plotly_chart(figure, width="stretch")
            if not bands:
                st.info(
                    "Extract real Sentinel-2 data for the location band profile. Demo features contain no fabricated spectrum."
                )
            render_warning(reference)
            st.caption(
                "Broadband centers, not a hyperspectral measurement. Curves are not bandpass-convolved; no mineral match score is computed."
            )
            st.link_button(
                "Manganese remote-sensing research",
                "https://doi.org/10.1016/j.asr.2023.03.044",
                icon=":material/article:",
            )
        with tabs[2]:
            inputs = api_get("/features/sites/" + selected + "/model-input")
            st.caption(
                "This is the exact typed input passed to backend adapters. Trained models are not installed."
            )
            if inputs:
                st.json(inputs, expanded=False)
            if st.button("Run prediction demo", icon=":material/science:"):
                result = api_post("/predictions/exploration", {"site_id": selected})
                if result:
                    st.session_state["prediction_" + selected] = result
            result = st.session_state.get("prediction_" + selected)
            if result:
                render_warning(result)
                st.json(result, expanded=False)
        with tabs[3]:
            if st.button("Prepare location exports", icon=":material/download:"):
                st.session_state["csv_" + selected] = api_get(
                    "/exploration/sites/" + selected + "/export?format=csv", raw=True
                )
                st.session_state["txt_" + selected] = api_get(
                    "/exploration/sites/" + selected + "/export?format=text", raw=True
                )
            for format in ("csv", "txt"):
                content = st.session_state.get(format + "_" + selected)
                if content:
                    st.download_button(
                        "Download " + format.upper(),
                        content,
                        file_name=selected + "." + format,
                        mime="text/csv" if format == "csv" else "text/plain",
                        icon=":material/download:",
                    )

elif page == "Locations":
    st.title("Exploration candidates")
    render_warning(rankings)
    rows = rankings["locations"]
    if rows:
        table = pd.DataFrame(rows).rename(
            columns={
                "demo_ranking_score": "Demo score",
                "name": "Location",
                "rank": "Demo rank",
            }
        )
        st.dataframe(table, hide_index=True, width="stretch")
        export_table = table.assign(warning=rankings["warning"]).map(
            lambda value: (
                "'" + value
                if isinstance(value, str)
                and value.lstrip().startswith(("=", "+", "-", "@"))
                else value
            )
        )
        st.download_button(
            "Export ranked candidates",
            export_table.to_csv(index=False),
            "demo_candidate_ranking.csv",
            "text/csv",
            icon=":material/download:",
        )
    else:
        st.info("Save your first exploration candidate in Explore.")
elif page == "Production":
    st.title("Production planning")
    overview = api_get("/production/overview")
    if overview:
        render_warning(overview)
        metrics = st.columns(3)
        with metrics[0]:
            render_metric_card("Demo target", overview["target"])
        with metrics[1]:
            render_metric_card("Demo production", overview["predicted"])
        with metrics[2]:
            render_metric_card("Demo risk", overview["risk"])
        with st.expander("Operational response details"):
            st.json(overview, expanded=False)
    render_section_header("Recommended actions")
    recommendations = api_get("/decision/recommendations")
    if recommendations:
        render_warning(recommendations)
        for recommendation in recommendations["recommendations"]:
            render_status_pill(recommendation["priority"])
            for action in recommendation["actions"]:
                st.write(action)
            st.caption(" · ".join(recommendation["drivers"]))
            st.caption("Evidence: " + recommendation["evidence_status"])
            st.divider()
elif page == "Pipeline":
    st.title("Extraction pipeline")
    st.caption(
        "Queued → running → completed / failed. Real extraction executes outside the API process."
    )
    job_id = st.text_input("Job ID", value=st.session_state.get("extraction_job", ""))
    if st.button("Refresh job status", icon=":material/refresh:") or job_id:
        if job_id:
            show_job(job_id)
    with st.expander("Prediction job demo"):
        selected = (
            st.selectbox(
                "Location",
                list(site_by_id),
                format_func=lambda x: site_by_id[x]["name"],
            )
            if sites
            else None
        )
        if selected and st.button(
            "Create prediction job", icon=":material/play_arrow:"
        ):
            job = api_post("/jobs", {"site_id": selected, "complete_immediately": True})
            if job:
                st.session_state["extraction_job"] = job["job_id"]
                st.rerun()
else:
    st.title("System health")
    st.json(health, expanded=True)
    st.caption(
        "Database and PostGIS are real infrastructure. GEE availability does not imply model validation."
    )
