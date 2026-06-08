# Decision-Aware Occupancy Forecasting Research Prototype

This repository evaluates day-ahead occupancy forecasting for identifying stable empty windows and estimating safe shiftable-load opportunity under occupancy-conflict constraints.

The current implementation is best described as:

`occupancy forecasting + validation-selected risk-constrained recommendation evaluation`

It does not implement a deployed controller, verified energy-savings study, reinforcement-learning scheduler, or learned decision-aware loss.

## Quick Start For Review

For a fast first pass, read:

1. `RESULTS_SUMMARY.md` - main numbers, method notes, and canonical result files.
2. `VALIDITY_CHECKLIST.md` - leakage-prevention and evaluation checks.
3. `CLAIMS_AND_LIMITATIONS.md` - supported claims, unsupported claims, and wording boundaries.
4. `REPRODUCING.md` - full rerun instructions.

## What The Project Does

- Builds 15-minute occupancy labels from LBNL Building 59 selected south-zone occupancy streams.
- Aligns occupancy, WiFi, weather, interior temperature, and electrical meter streams.
- Trains and evaluates Historical Average, LightGBM, Random Forest, DLinear, and Transformer baselines.
- Converts forecasts into stable empty-window recommendations.
- Selects Empty probability thresholds on validation daily schedules and evaluates them on held-out test daily schedules.
- Reports occupancy-conflict risk and offline safe shiftable-load opportunity.

## Main Reported Result

Under the 10% validation-selected occupancy-conflict policy, LightGBM selected an Empty probability threshold of 0.95.

On the held-out test daily schedules:

- Test occupancy-conflict rate: 4.15%.
- Safe shiftable-load opportunity: 493.9 kWh.
- Recommended stable windows: 19.
- Safe stable windows: 16.
- Test target period: 2019-01-09 to 2019-02-21 local Pacific time.

Historical Average has the highest model-level Empty AUPRC, showing strong periodic occupancy structure. LightGBM gives the strongest practical risk-opportunity tradeoff under the 10% recommendation policy in this experiment.

## Important Interpretation

Safe shiftable-load opportunity is an offline estimate of controllable load that coincides with recommended intervals that were actually empty.

Default controllable-load proxy:

`P_controllable = hvac_S + lig_S`

For each safe recommended 15-minute interval:

`kWh = P_controllable * 0.25`

This is not verified energy savings. The repository does not include a counterfactual building simulation, BMS intervention, thermal-comfort model, occupant-response study, or real deployment evaluation.

## Repository Layout

- `src/` - reusable data preparation, feature engineering, modeling, evaluation, policy, energy-accounting, plotting, and pipeline code.
- `scripts/run_all.py` - full Python pipeline for data preparation, model training, prediction export, result tables, and figures.
- `scripts/generate_figures.py` - redraws figures from saved result CSVs without retraining models.
- `scripts/check_environment.py` - checks Python version, third-party packages, and local module imports.
- `LBNL_occupancy_forecasting_main.ipynb` - reporting-only notebook for inspecting saved tables and figures.
- `results/` - canonical CSV outputs.
- `figures/` - canonical PNG figures.
- `predictions/` - per-model test prediction CSV files.
- `results/archive/` and `figures/archive/` - preserved legacy duplicate or alias outputs.

## Detailed Documents

- `RESULTS_SUMMARY.md` - main numbers, method notes, canonical result files, and first figures to inspect.
- `VALIDITY_CHECKLIST.md` - leakage prevention, evaluation protocol, and data-splitting validation.
- `CLAIMS_AND_LIMITATIONS.md` - supported claims, unsupported claims, and wording boundaries.
- `REPRODUCING.md` - full environment, data, test, pipeline, and figure-regeneration instructions.
- `DATA.md` - raw Dryad data placement instructions.
- `SIMULATION_SUMMARY.md` - detailed stable-window and risk-opportunity evaluation notes.
- `FUTURE_WORK.md` - future research and paper-strengthening tasks.

## Reproduce The Results

The raw LBNL data is not committed. Full reproduction requires downloading the Dryad dataset first.

1. Read `DATA.md` and download the LBNL Building 59 dataset from Dryad.
2. Place the extracted data at:

   `doi_10_7941_D1N33Q__v20220202/Building_59/Bldg59_clean data/`

3. Create an environment with Python 3.10-3.12. Python 3.11 is recommended.

   Conda path:

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

4. Check the environment:

   ```bash
   python scripts/check_environment.py
   ```

5. Run unit tests:

   ```bash
   python -m pytest -q
   ```

6. Execute the full pipeline:

   ```bash
   python scripts/run_all.py
   ```

The pipeline writes outputs to `results/`, `figures/`, and `predictions/`.

To regenerate figures from existing result tables without retraining:

```bash
python scripts/generate_figures.py
```

Figure regeneration reads saved CSV files from `results/` and may take several minutes depending on the machine.

Open `LBNL_occupancy_forecasting_main.ipynb` after running the scripts to review the saved report artifacts.

## Current Limitations

- Single-building, selected-zone evaluation.
- Short held-out recommendation test period with 43 non-overlapping daily schedules.
- Model metrics use overlapping rolling forecast intervals, so effective sample size is smaller than the interval count.
- Threshold selection is validation-only, but risk estimates are fragile because daily validation/test blocks are limited.
- Energy opportunity uses realized recorded loads offline and is not deployable expected savings.
- Model training uses standard occupancy losses; the decision-aware part is the evaluation and threshold policy.
- Transformer and DLinear baselines are exploratory and lightly tuned.

Detailed claim boundaries are in `CLAIMS_AND_LIMITATIONS.md`. Leakage and split checks are in `VALIDITY_CHECKLIST.md`. Future-work items are in `FUTURE_WORK.md`.
