# Reproducing the Experiment

There are two supported paths: deterministic hybrid regeneration from committed saved predictions, and full raw-data retraining.

## 1. Environment

Use Python 3.10-3.12; Python 3.11 is the supported CI target.

Conda:

```bash
conda env create -f environment.yml
conda activate decision-aware-occupancy
```

Virtual environment:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

On macOS, LightGBM may require `brew install libomp`.

The staged July environment pins are archived at `archive/new_staging_2026-07/staged_docs/requirements.txt`; they are provenance, not the portable installation file.

## 2. Environment and unit checks

```bash
python scripts/check_environment.py
python -m pytest -q
```

Tests include hybrid convex-blend calculations, weight-grid behavior, validation/test split integrity, fixed-threshold policy accounting, validation-before-test selection ordering, and exact canonical reproduction from saved prediction exports.

## 3. Reproduce the hybrid from saved outputs

This path does not train models and does not require raw Dryad data:

```bash
python scripts/generate_hybrid_artifacts.py
```

It performs the following in order:

1. Validates the canonical validation prediction schema, 96-step anchors, labels, and probabilities.
2. Selects Seasonal-Transformer alpha on validation only (0.01 grid).
3. Selects Historical/LightGBM/Transformer weights on validation only (0.05 simplex grid).
4. Selects probability thresholds on validation midnight horizons.
5. Loads test predictions only after blend weights and operating thresholds are fixed.
6. Applies fixed weights/thresholds to test.
7. Regenerates comparison tables, risk sweeps, Pareto flags, stable-window results, 2,000 paired daily-block bootstrap summaries, calibration diagnostics, predictions, and figures.

Key deterministic checks:

- primary weights: `0.15 / 0.60 / 0.25`
- primary validation AUPRC: `0.72863796`
- primary test Empty AUPRC: `0.85136961`
- primary 10% threshold: `0.875`
- primary test safe opportunity: `490.1464 kWh`
- primary test conflicts: `0/259`

Use `--skip-figures` for tables/predictions only or `--bootstrap-reps N` for a faster diagnostic run.

## 4. Regenerate all figures from saved results

```bash
python scripts/generate_figures.py
python scripts/generate_presentation_figures.py
```

`generate_figures.py` regenerates the established base figures and the integrated hybrid figures. `generate_presentation_figures.py` retains the earlier LightGBM/Historical presentation artifacts for provenance and comparison.

## 5. Full raw-data retraining

Raw data are not committed. Follow `DATA.md` and place:

```text
doi_10_7941_D1N33Q__v20220202/
  Building_59/
    Bldg59_clean data/
      occ.csv
      wifi.csv
      site_weather.csv
      zone_temp_interior.csv
      ele.csv
      zone_co2.csv
```

Then run:

```bash
python scripts/run_all.py
```

This performs data preparation, base-model training, validation selection, held-out evaluation, prediction export, hybrid selection, uncertainty analysis, and figure generation.

## 6. Canonical inputs and outputs

Hybrid inputs:

- `results/forecast_predictions_validation_all_models.csv`
- `results/forecast_predictions_test_all_models.csv`
- `results/processed_lbnl_15min_pacific.csv`

Primary outputs:

- `results/canonical_model_comparison.csv`
- `results/canonical_policy_10pct.csv`
- `results/hybrid_candidate_registry.csv`
- `results/hybrid_lineage.csv`
- `results/hybrid_primary_weight_search.csv`
- `results/hybrid_risk_opportunity_threshold_sweeps.csv`
- `results/hybrid_uncertainty_daily_block_bootstrap.csv`
- `results/canonical_uncertainty_summary.csv`
- `predictions/hybrid_ensemble_validation_predictions.csv`
- `predictions/hybrid_ensemble_test_predictions.csv`

The root reporting notebook reads saved outputs and is intentionally not the source of executable research logic.

## 7. Reproducibility limits

- The saved-output hybrid is deterministic given the committed CSV inputs and supported libraries.
- Exact base-model retraining can vary across CPU/GPU, PyTorch, LightGBM, and BLAS versions even with fixed seeds.
- Full raw-data retraining was not run during the integration because the external Dryad directory is absent.
- Hybrid-specific per-seed and rolling-origin results require new saved predictions or retraining; they cannot be inferred from aggregate exports.
