# Notebooks Directory Guide

This file explains `notebooks/`.

```text
notebooks/
├── 00_data_sanity.ipynb
├── 01_baseline.ipynb
└── 02_simple_ml.ipynb
```

## Purpose

Notebooks are for learning, data inspection, baselines, and early model experiments. They should help the team decide whether a modeling path is defensible before adding backend/API/frontend complexity.

The audit explicitly recommends notebook-only signal checks before wiring PostGIS, FastAPI, and Streamlit.

The current application uses software fixtures only; it does not count as passing this scientific gate.

## Files

`00_data_sanity.ipynb` should inspect available data, missingness, units, timestamps, coordinate systems, duplicates, and basic distributions.

`01_baseline.ipynb` should define a simple baseline for the task. Every prediction task needs a baseline so model performance has context.

`02_simple_ml.ipynb` should compare a simple ML model against the baseline. It should not become production runtime code.

## Notebook Rules From The Audit

For exploration:

- Use spatial validation.
- Keep pseudo-absence/background strategy explicit.
- Retain sampling metadata.
- Handle CRS/buffer correctness using projected metric CRS where needed.

For production:

- Treat it as forecasting.
- Use chronological backtesting.
- Track forecast origin, horizon, feature cutoff, and actual outcome.
- Do not use future observations.

For all ML:

- Define the target before training.
- Define the as-of time.
- Start with compact feature groups.
- Avoid feature explosion.
- Do not claim scientific validity from synthetic data.

## Contribution Rules

- Keep notebooks readable.
- Put reusable runtime code into backend modules later.
- Save conclusions in docs when they affect architecture.
- Keep private data out of committed notebooks.
- Clear large outputs before committing if they make reviews noisy.

## Improvement Path

Near-term:

- Fill `00_data_sanity.ipynb` once sample or real allowed data exists.
- Use `01_baseline.ipynb` before any first model.
- Use `02_simple_ml.ipynb` to decide whether Sprint 1b should proceed.

Later:

- Convert proven notebook logic into backend services, providers, repositories, or ML adapters.
- Keep notebooks as experiment records, not application dependencies.
