# Data Directory

## Nested directories

data/raw/ stores future original inputs; .gitkeep retains the empty directory. Contents are ignored by Git.
data/processed/ stores future validated/materialized features; .gitkeep retains it and generated contents are ignored.
data/samples/ is reserved for deliberately non-confidential sample inputs; .gitkeep retains it.
Current runtime sample sites and production targets live in typed backend repositories, not these directories.

## What contributors can add

Start with a versioned schema, explicit target, units, WGS84 location and prediction cutoff.
Define required/optional columns and rejected-row reporting; do not silently coerce invalid records.
Add genuine dataset/product IDs, acquisition timestamps, AOI, processing/feature version and source resolutions.
Keep environmental variables separate: rainfall, coarse soil moisture, NDVI and LST must be available at prediction time.
Separate forecast-at-origin rainfall from observed/reanalysis history.
Preserve label_source: positive, true_negative and background. Spatial splits and occurrence-derived features must be fold-safe.
Use local projected metric CRS for buffers/distances; never treat degrees as metres.
Materialize GEE batch outputs before prediction; record missing/stale features as unavailable.
MOIL operational history is necessary for real production backtests; synthetic data validates software only.

## Future integration and evidence gates

Replace repositories with PostGIS access after database and schema smoke tests.
The notebook signal check, measured baseline and meaningful spatial validation must precede claims of a real exploration model.
Production needs chronological holdout and empirically checked intervals.
No real data, extraction, ingestion engine, persistence or retraining exists in this prototype.
Never commit private mine data, credentials or raw satellite archives. Public samples must identify themselves as examples.
