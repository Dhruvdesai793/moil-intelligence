# Architecture Decisions

| Decision | Reason and boundary |
| --- | --- |
| FastAPI is the stable backend boundary | Frontend uses HTTP contracts; integrations stay private to backend. |
| Streamlit for SIH prototype | Fast functional dashboard, replaceable later without changing services. |
| Native PostgreSQL/PostGIS locally | Matches Arch/CachyOS install, no Docker requirement. |
| PostGIS spatial persistence | WGS84 Points/Polygons, GIST indexes; metric calculations require projection/geography. |
| Alembic owns schema changes | Repeatable migrations including PostGIS extension creation. |
| Explicit dependency injection | One request session, visible constructors, no hidden infrastructure in business methods. |
| GEEProvider abstraction | Lazy OAuth initialization, honest status and replaceable batch extraction boundary. |
| earthengine-api in backend | Official API; geemap is notebook-only later. |
| ML stays stubbed | No trained/validated artifacts, scientific datasets or performance claims exist. |
| Frontend stays API-only | No direct PostgreSQL/GEE/model access. |
| Features are materialized | Audit requires batch extraction; inference reads persisted features, not live satellite computations. |
| Demo fallback needs explicit consent | Global permission plus per-request toggle; no fake NDVI output. |
| Lightweight persisted jobs | Polling contract now; no Redis/Celery/worker or asynchronous claims. |
| ACTIVE rule in service | Business rule remains obvious; repository query optimization can follow with tests. |

This integration milestone validates software boundaries, not the audit's first-model scientific gate. Baselines, spatial holdout, chronological backtests, calibrated uncertainty and actual-outcome evaluation must be completed before scientific claims.
