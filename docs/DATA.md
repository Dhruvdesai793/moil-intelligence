# Data

data/raw and data/processed are reserved and ignored except .gitkeep. data/samples is for small nonsensitive software fixtures. Never store real MOIL confidential data or credentials in public git.

Current demo sites are seeded by backend/scripts/seed_db.py into exploration_sites. Demo features are generic contract fixtures stored in site_features only after explicit fallback permission. They are not satellite observations, training labels or validated geology.

Feature payloads preserve origin, observation date window, extraction timestamp, feature_version/source/is_stub/readiness/warning. Predictions retain the selected feature version and extraction timestamp. Historical queries exclude bundles materialized after as_of.

Contributors should implement versioned validated ingestion contracts, rejected-row reports, source provenance, ground truth formats and reproducible feature QA before scientific modeling. WGS84 is storage/display CRS; metric calculations require projection. Follow audit signal/baseline/holdout gates before claiming usefulness.
