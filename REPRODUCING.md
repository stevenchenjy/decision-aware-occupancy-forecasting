# Reproducing The Experiment

This document describes the supported reproducibility path. The executable research logic lives in `src/`, while `LBNL_occupancy_forecasting_main.ipynb` is reporting-only and reads saved outputs.

## 1. Python Environment

Use Python 3.10-3.12. Python 3.11 is recommended because it is used by CI.

Conda is the most robust path:

```bash
conda env create -f environment.yml
conda activate decision-aware-occupancy
```

Virtualenv path:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

If `python3.11` is not available, use another Python 3.10-3.12 interpreter and confirm with:

```bash
python --version
```

Python 3.13 is not a supported reproduction target for this repository.

On macOS, LightGBM may require OpenMP:

```bash
brew install libomp
```

## 2. Data

Follow `DATA.md`. The raw LBNL data is not committed to this repository.

Expected path:

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

Run the helper for manual download and placement instructions:

```bash
python scripts/download_data.py
```

The helper does not automatically download the Dryad package.

## 3. Environment Check

After activating the environment, run:

```bash
python scripts/check_environment.py
```

This checks the Python version, imports the main third-party packages, and imports all local `src` modules.

## 4. Unit Tests

The unit tests use synthetic data and do not require the LBNL dataset.

```bash
python -m pytest -q
```

The repository includes `pytest.ini`, so `pytest -q` also works from the repository root when the environment is active.

## 5. Execute The Full Pipeline

Full reproduction requires the raw data directory from Section 2.

```bash
python scripts/run_all.py
```

The script runs `src.lbnl_pipeline.run_pipeline`, which performs:

- data preparation
- feature engineering
- model training
- validation threshold selection
- held-out test evaluation
- prediction exports
- energy-opportunity accounting
- result table generation
- figure generation

Outputs are written under:

```text
results/
figures/
predictions/
```

Prediction exports are generated in two formats:

- all-model long-form tables in `results/forecast_predictions_validation_all_models.csv` and `results/forecast_predictions_test_all_models.csv`
- per-model test prediction CSV files in `predictions/`

## 6. Regenerate Figures Only

After `results/` exists, regenerate plots without retraining models:

```bash
python scripts/generate_figures.py
```

This reads saved CSV files from `results/` and writes PNG files to `figures/`. Figure regeneration may take several minutes.

## 7. Reporting Notebook

Open the reporting notebook after running the scripts:

```text
LBNL_occupancy_forecasting_main.ipynb
```

The notebook is intentionally reporting-only. It reads saved CSV tables and PNG figures; it is not the source of executable experiment logic.

## 8. Canonical Outputs

Use the canonical outputs below for review:

- Model metrics: `results/model_metrics_empty_positive.csv`
- Validation-selected thresholds: `results/selected_threshold_policies.csv`
- Test policy results: `results/threshold_policy_results_test.csv`
- Pareto frontier: `results/energy_risk_pareto_frontier.csv`
- Stable-window summary: `results/stable_window_metrics.csv`
- Detailed continuous-window metrics: `results/continuous_empty_window_policy_results_test.csv`
- Prediction export: `results/forecast_predictions_test_all_models.csv`

Legacy aliases are preserved in `results/archive/` and `figures/archive/`.

## 9. Notes On Exact Reproduction

The pipeline trains stochastic models with fixed seeds and averages several seeded predictions. Exact bitwise reproducibility may vary across CPU/GPU backends and library versions, especially for PyTorch. The scientific logic should remain stable when the same raw data, splits, code revision, and supported dependency versions are used.
