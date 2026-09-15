# API and ML Handoff Contract

Base path: /api/v1. Interactive schema: http://127.0.0.1:8000/docs.

## Endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| GET | /health | Guarded API, DB, PostGIS, GEE and registry status |
| GET | /exploration/sites | ACTIVE saved candidates |
| POST | /exploration/sites | Save candidate name, WGS84 latitude/longitude, region and notes |
| GET | /exploration/sites/{site_id} | Candidate detail, or 404 |
| GET | /exploration/sites/{site_id}/summary | Provider and model readiness |
| GET | /exploration/study-area | Approximate Sausar envelope and sourced MOIL reference points |
| GET | /exploration/rankings | Deterministic demo adapter ordering; explicitly not geological likelihood |
| GET | /exploration/sites/{site_id}/export?format=csv or text | Full candidate and current model-input export |
| GET | /features/sites/{site_id}/availability | GEE status and latest stored bundle |
| POST | /features/provider/check | Explicit live GEE readiness smoke check; ordinary reads use cached status |
| GET | /features/sites/{site_id} | Stored feature history, newest first |
| GET | /features/bundles/{feature_id} | Immutable stored bundle for prediction lineage |
| POST | /features/extract | Queue extraction; 202 JobRecord, not a feature response |
| GET | /features/sites/{site_id}/model-input | Exact typed ModelInput supplied to adapters |
| POST | /predictions/exploration | Resolve site, read stored features, run adapters, save stub prediction |
| GET | /predictions/{prediction_id} | Saved prediction |
| GET | /spectral/reference | Measured USGS pyrolusite laboratory spectrum and provenance |
| GET | /production/overview | Explicitly stub operational overview |
| GET | /decision/recommendations | Demo rules requiring human review |
| POST | /jobs | Immediate or queued prediction demo job |
| GET | /jobs/{job_id} | Poll extraction/prediction status and result |

No public endpoint calls individual ML models. Models are backend plugins, not frontend services.

Health and ordinary feature-availability reads never wait for Google. GEE readiness is cached for up to five minutes; not_checked means no recent live check, not proof that credentials are missing. Use Check GEE in the frontend or POST /features/provider/check for an explicit live check. The independent worker performs its own readiness check when extracting.

## Extraction input and response

Provide exactly one of site_id, coordinates or aoi, plus start_date and end_date (end exclusive, no future dates, maximum 366 days). Coordinates and AOIs are restricted to the approximate Sausar study envelope. AOIs are closed GeoJSON Polygon rings with a small bounding-box budget; complex geometry repair is not implemented.

Example:

```json
{"site_id":"exp_001","start_date":"2025-01-01","end_date":"2025-04-01","allow_demo_fallback":false}
```

Response: job_id, status=queued, request, source=postgresql, is_stub=false, warnings. Poll /jobs/{id}. Completed result is FeatureBundle. Failed jobs can still return an honest unavailable result. Demo fallback requires explicit request consent AND GEE_ALLOW_DEMO_FEATURES=true. Demo bundles have no invented NDVI or spectral curve.

## What the backend supplies to the model

Contract class: backend/app/schemas/ml.py ModelInput, version exploration-model-input-v1.

- site_id and coordinates in EPSG:4326.
- features: nullable FeatureBundle with feature_id, version, source, is_stub, extraction time and date window.
- feature_payload: measured s2_B2/B3/B4/B5/B6/B7/B8/B8A/B11/B12, ndvi, ndmi, land_surface_temperature_c, rainfall_total_mm, soil_moisture_surface, soil_moisture_rootzone, elevation_m and slope_degrees, when available.
- spectral_bands: wavelength_nm, reflectance, native_resolution_m and wavelength caveat.
- quality: collection, status, scene_count, valid_fraction where implemented, native support, latest observation and units for each product.
- missing_inputs: validated geology, drilling assays and trained model are still missing.
- warning: environmental measurements alone do not establish manganese presence or reserves.

Missing products stay absent or null, never zero-filled. Model developers must inspect readiness, product quality and source timestamps. Rainfall is an observed historical sum, not a forecast. SMAP is coarse context, not 10 m mine data. S2 bands are broadband observations, not a hyperspectral manganese signature. No field validation or preprocessing standardization is implied.

## What the model must return

Implement ModelAdapter.predict(ModelInput) -> ModelResult. Register the adapter under prospectivity, grade or production in ModelRegistry; do not instantiate it in a route. The current ModelResult supplies model_name, model_version, value, is_stub, readiness and warning. Real model outputs need reviewed contract changes for scientifically meaningful score_type, calibration and uncertainty: simply setting is_stub=false is not sufficient.

Until validated artifacts exist, ExplorationPrediction is deliberately restricted to demo_ranking_score and insufficient_real_data, with is_stub=true. It returns prediction_id, feature_id, coordinates, model/feature versions, data_timestamp (bundle materialization time), prediction_timestamp, models_used as the models list, and uncalibrated uncertainty. Retrieve the exact feature_id through /features/bundles/{feature_id}. Source observation dates are in FeatureBundle quality; data_timestamp is NOT a sensor acquisition date.

The current stub uses coordinates to produce a deterministic software ordering; measured features are supplied to the adapter but not scientifically interpreted. No model performance metrics are invented.

## Prediction input

Provide site_id OR coordinates, optional as_of and requested_resolution_m. Materialized site features are read only if extracted_at <= as_of. requested_resolution_m is intent only, not an executed raster inference scale. Coordinate-only predictions currently have no stored site feature lookup; save a candidate and extract features before a feature-backed prediction.

allow_demo_features is retained for compatibility but no longer launches extraction during prediction. Queue extraction explicitly first. Normal prediction calls have no GEE dependency.

## Persistence and jobs

Sessions are injected and commit before response; repositories flush writes, business services do not own hidden infrastructure. The local worker claims queued feature_extraction rows using FOR UPDATE SKIP LOCKED. Running jobs survive in the database, but automatic crash recovery/retry is not implemented; inspect and requeue a failed/interrupted extraction. Queued prediction-demo jobs still have no prediction worker; use complete_immediately=true.

Schema changes require an Alembic migration. Feature definition changes require a new feature_version and preprocessing review. Tests must verify contract shape, persistence and honest partial/missing-data behavior.
