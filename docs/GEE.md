# Google Earth Engine

GEE supplies future public satellite/environmental features. The backend uses the official earthengine-api package behind GEEProvider. geemap is not a backend dependency; it can be added to notebooks later.

Project: **secure-guru-473417-q2**.

## Development OAuth

Run from backend with its virtual environment active:

```bash
earthengine authenticate
# alternative:
python -c "import ee; ee.Authenticate()"
```

Accept authentication yourself in the external browser. Credentials normally live in ~/.config/earthengine/credentials outside this repository. Never copy OAuth files, service account JSON or tokens into git.

backend/.env:

```dotenv
GEE_ENABLED=true
GEE_PROJECT_ID=secure-guru-473417-q2
GEE_AUTH_METHOD=oauth
GEE_ALLOW_DEMO_FEATURES=true
```

Restart FastAPI after changing settings. To run without GEE, set GEE_ENABLED=false. Missing GEE never blocks API startup.

The provider lazily calls:

```python
ee.Initialize(project=settings.gee_project_id)
```

For the configured project this is equivalent to ee.Initialize(project="secure-guru-473417-q2"). It performs an algorithm-list smoke check with a small API deadline, no raster download or expensive export. Status checks are cached for 30 seconds to avoid repeated network work; restart or wait after authenticating.

## Status contract

| Status | Meaning |
| --- | --- |
| not_configured | GEE disabled or unsupported auth method |
| auth_required | OAuth credentials absent/expired; run authentication |
| unavailable | Package/network/project/API access failure |
| ok | Initialization and lightweight smoke check succeeded |
| not_implemented | Auth works but real feature extraction is not implemented |
| stub | Explicitly permitted demo feature bundle |

Provider error messages avoid exposing credentials; check project registration/access and Earth Engine API enablement in Google Cloud when initialization fails. A project permission failure can be unavailable even with valid OAuth.

## Implemented boundary

GEEProvider exposes availability(), extract_features_for_point(latitude, longitude, start_date, end_date), and extract_features_for_aoi(geojson, start_date, end_date). Real methods currently return no measurements and an honest status. The service, not provider, owns demo fallback and persistence.

POST /api/v1/features/extract accepts exactly one site_id, coordinates or Polygon AOI plus dates and allow_demo_fallback (false by default). Dates use an exclusive end; invalid ranges/future ends are rejected. Demo fallback requires both request permission and GEE_ALLOW_DEMO_FEATURES=true. It stores a generic integration fixture, never a fake NDVI or Earth Engine measurement.

GET /api/v1/features/sites/{site_id}/availability returns provider status and latest persisted bundle. GET /api/v1/features/sites/{site_id} lists stored bundles.

## Future extraction

Implement reproducible batch extraction for compact Sentinel/Landsat NDVI/LST, DEM terrain and rainfall/soil moisture inputs only after the data team freezes feature definitions and QA. Persist collection/source, observation window, cloud masks, valid-pixel support, sensor/effective resolution, CRS and extraction version. Respect quotas and use batch exports/jobs for larger requests. Materialize features before inference; prediction requests must not depend on live GEE satellite computation.

Current Polygon validation checks ring closure and coordinate ranges, not full geometric topology. Add topology validation and area/size limits before real AOI workloads. No actual export, scientific feature engineering, preprocessing, training or validation is implemented.

Official reference: [Authentication and initialization](https://developers.google.com/earth-engine/guides/auth).
