# LBNL Occupancy Forecasting Experiment Summary

## 1. Research Goal

This package evaluates day-ahead occupancy forecasting for identifying stable empty windows in an office building. The downstream goal is facility-management support: HVAC setback, lighting reduction, or controllable-load scheduling during predicted stable empty windows.

The recommendation objective is:

`maximize safe shiftable-load opportunity subject to occupancy conflict rate <= delta`

with delta values of 5%, 10%, and 20%.

## 2. Dataset

The experiment uses the LBNL Berkeley Office Building Dataset, Building 59 selected south zones, from `doi_10_7941_D1N33Q__v20220202`. Occupancy labels, WiFi, weather, interior temperature, and south electrical meters are aligned to 15-minute intervals.

## 3. Timezone Handling

Raw timestamps are treated as UTC, then converted to `America/Los_Angeles` before generating hour, day-of-week, weekend, month, and holiday features. The raw 10:00-12:00 empty anomaly is explained as a timezone artifact because those raw UTC hours map to early morning Pacific Time.

## 4. Label Handling

Raw occupancy uses `occupied=1`. Recommendation evaluation flips the positive class to `Empty=1`, because the task is to find empty windows safely.

## 5. Leakage Prevention

The pipeline uses chronological train/validation/test splits with 24.25-hour gaps. Historical Average uses train labels only. Rolling occupancy features use `arr[anchor-window:anchor]`, so current/future labels are excluded. Missing values use causal forward-fill plus 0.0 for leading gaps. Future sensor values and all load variables are excluded from model inputs.

## 6. Model List

Main models:

- Historical Average
- LightGBM
- Random Forest
- DLinear
- Transformer

TFT and PatchTST are left as appendix/future candidates because a fair comparison would require matched tuning budget and exogenous-variable setup.

## 7. Threshold Policy

Each model is swept over empty-probability thresholds. Thresholds are selected on validation daily forecasts by maximizing safe shiftable-load opportunity subject to occupancy-conflict constraints of 5%, 10%, or 20%. The selected threshold is then evaluated once on the test split.

## 8. Energy Opportunity Definition

This value represents safe shiftable-load opportunity, not verified energy savings from an implemented control action.

Default opportunity uses the selected south proxy controllable load:

`P_controllable = hvac_S + lig_S`

For each safe recommended 15-minute interval:

`kWh = P_controllable * 0.25`

Intervals with occupancy conflict are excluded from safe opportunity. Additional 100%, 50%, and 25% controllability scenarios are saved in `results/safe_shiftable_load_opportunity.csv`.

## 9. Main Results

Under a 10% validation-selected occupancy-conflict constraint, LightGBM achieved a 4.15% test occupancy conflict rate and identified 493.9 kWh of safe shiftable-load opportunity. Historical Average had the highest Empty AUPRC, showing strong periodic occupancy patterns, but produced much lower safe opportunity under the same risk-constrained recommendation policy. DLinear satisfied the validation constraint but failed on the test split, suggesting weak generalization.

At the same 10% policy:

| Model | Test conflict | Safe opportunity |
|---|---:|---:|
| Historical Average | 0.00% | 94.6 kWh |
| LightGBM | 4.15% | 493.9 kWh |
| Random Forest | 5.32% | 359.5 kWh |
| DLinear | 43.87% | 185.1 kWh |
| Transformer | 9.68% | 97.4 kWh |

Historical Average has strong model-level Empty AUPRC, but it is conservative at low-risk thresholds. LightGBM gives the best practical risk-opportunity tradeoff in the 10% setting.

## 10. Limitations

- No confirmed energy savings are claimed because no counterfactual baseline energy model, simulator, or intervention data is available.
- No full thermal comfort impact is claimed because setpoint response, PMV/PPD, and occupant feedback are unavailable.
- Carbon emissions avoided are not claimed because no location-matched, time-varying grid carbon intensity or load-shifting response model is used.
- Full RL scheduling is not implemented in this phase.
- Conclusions are limited to LBNL Building 59 selected zones.

## 11. Files Included

- `LBNL_occupancy_forecasting_main.ipynb`: runnable end-to-end notebook.
- `src/`: reusable pipeline modules.
- `results/`: CSV outputs for data splits, metrics, policies, ablations, robustness, and energy opportunity.
- `figures/`: PNG figures for model metrics, threshold tradeoffs, stable windows, examples, and feature importance.
- `predictions/`: per-model test prediction files.
- `VALIDITY_CHECKLIST.md`: leakage and validity checklist.
- `requirements.txt`: Python dependency list.

## 12. How To Rerun

1. Activate the OCR environment or install dependencies from `requirements.txt`.
2. Open `LBNL_occupancy_forecasting_main.ipynb`.
3. Run all cells from top to bottom.
4. The notebook writes outputs to `results/` and `figures/`.
5. The current delivery also includes per-model prediction files in `predictions/`.
