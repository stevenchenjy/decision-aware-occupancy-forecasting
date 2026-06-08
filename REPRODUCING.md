# Reproducing The Experiment

This document describes the current reproducibility path without changing the scientific logic in `LBNL_occupancy_forecasting_main.ipynb`.

## 1. Environment

Use Python 3.10-3.12. Python 3.11 is recommended for CI and local reruns.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

For Conda users:

```bash
conda env create -f environment.yml
conda activate decision-aware-occupancy
```

## 2. Data

Follow [DATA.md](DATA.md). The raw LBNL data is not committed to this repository.

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

## 3. Environment Check

```bash
python scripts/check_environment.py
```

This imports the main third-party packages and all local `src` modules.

## 4. Execute The Notebook

```bash
python scripts/run_all.py
```

The script uses `nbclient` to execute `LBNL_occupancy_forecasting_main.ipynb` in place and writes an executed copy to:

```text
results/executed_notebook.ipynb
```

The notebook generates result tables and figures under:

```text
results/
figures/
predictions/
```

## 5. Unit Tests

The unit tests use small synthetic data and do not require the LBNL dataset.

```bash
pytest -q
```

## 6. Notes On Exact Reproduction

The current notebook trains stochastic models with fixed seeds and averages several seeded predictions. Exact bitwise reproducibility may vary across CPU/GPU backends and library versions, especially for PyTorch. The reported scientific logic should remain stable if the same data, splits, and dependency versions are used.

