# Results Summary

## Research Question

Can day-ahead occupancy forecasts identify stable empty windows and estimate safe shiftable-load opportunity while limiting occupancy-conflict risk?

This repository evaluates an offline recommendation framework:

1. Forecast occupied/empty probability for the next 24 hours.
2. Select Empty probability thresholds on validation daily schedules.
3. Recommend stable empty windows on held-out test daily schedules.
4. Count occupancy conflicts and safe shiftable-load opportunity.

## Dataset

- Dataset: LBNL Building 59 Office Building Dataset, Dryad DOI `10.7941/D1N33Q`.
- Scope: selected south-zone streams from Building 59.
- Frequency: 15-minute intervals.
- Local timezone: `America/Los_Angeles`.
- Test target period: 2019-01-09 to 2019-02-21 local Pacific time.
- Test daily schedules: 43 non-overlapping daily forecast horizons.
- Empty is the positive class for recommendation metrics.

## Method Notes

- Raw timestamps are treated as UTC and converted to `America/Los_Angeles` before generating hour, day-of-week, weekend, month, and holiday features.
- Raw occupancy uses `occupied=1`; recommendation evaluation flips the positive class to `Empty=1`.
- The pipeline uses chronological train/validation/test splits with 24.25-hour gaps.
- Historical Average uses training labels only.
- Rolling occupancy features use `arr[anchor-window:anchor]`, excluding current and future labels.
- Missing values use causal forward-fill plus fixed 0.0 for leading gaps.
- Future sensor values and load variables are excluded from model inputs.

## Models Evaluated

- Historical Average
- LightGBM
- Random Forest
- Transformer
- DLinear

TFT and PatchTST are not part of the main experiment because a fair comparison would require matched feature inputs, splits, seeds, and tuning budget.

## Main Finding

Historical Average has the highest model-level Empty AUPRC, showing that periodic occupancy structure is strong. Under the 10% validation-selected recommendation policy, LightGBM provides the strongest practical risk-opportunity tradeoff in the current experiment.

The recommendation objective is:

`maximize safe shiftable-load opportunity subject to occupancy conflict rate <= delta`

with validation-selected delta values of 5%, 10%, and 20%.

## 10% Policy Results

The 10% policy selects each model's Empty probability threshold on validation daily schedules by maximizing safe shiftable-load opportunity subject to validation occupancy-conflict rate `<= 10%`. The selected threshold is then evaluated once on held-out test daily schedules.

| Model | Selected Empty threshold | Test occupancy-conflict rate | Safe shiftable-load opportunity | Recommended intervals | Safe intervals |
|---|---:|---:|---:|---:|---:|
| Historical Average | 0.950 | 0.00% | 94.6 kWh | 66 | 66 |
| LightGBM | 0.950 | 4.15% | 493.9 kWh | 265 | 254 |
| Random Forest | 0.925 | 5.32% | 359.5 kWh | 188 | 178 |
| Transformer | 0.900 | 9.68% | 97.4 kWh | 31 | 28 |
| DLinear | 0.875 | 43.87% | 185.1 kWh | 155 | 87 |

Source table: `results/threshold_policy_results_test.csv`.

## LightGBM 10% Headline Result

LightGBM, 10% validation-selected occupancy-conflict policy:

- Selected Empty probability threshold: 0.95.
- Test occupancy-conflict rate: 4.15%.
- Safe shiftable-load opportunity: 493.9 kWh.
- Gross recommended controllable opportunity: 537.9 kWh.
- Conflict controllable kWh excluded: 44.0 kWh.
- Recommended stable windows: 19.
- Safe stable windows: 16.
- Safe opportunity per day: 11.49 kWh/day.

The default controllable-load proxy is:

`P_controllable = hvac_S + lig_S`

For each safe recommended 15-minute interval:

`kWh = P_controllable * 0.25`

## Forecasting Metrics

Model-level test metrics use Empty as the positive class. These metrics are computed over overlapping rolling forecast intervals, so effective sample size is smaller than the raw interval count.

| Model | Empty AUPRC | Empty AUROC | Empty F1 | Empty precision | Empty recall |
|---|---:|---:|---:|---:|---:|
| Historical Average | 0.8497 | 0.9262 | 0.7621 | 0.7264 | 0.8015 |
| LightGBM | 0.8382 | 0.9291 | 0.7601 | 0.7610 | 0.7593 |
| Random Forest | 0.8329 | 0.9307 | 0.7756 | 0.7510 | 0.8019 |
| Transformer | 0.7621 | 0.9034 | 0.6581 | 0.7253 | 0.6022 |
| DLinear | 0.5933 | 0.7944 | 0.6179 | 0.5764 | 0.6657 |

Source table: `results/model_metrics_empty_positive.csv`.

## Important Interpretation

This is an offline opportunity estimate.

This is not verified energy savings.

The repository does not include a counterfactual building simulation, BMS intervention, thermal-comfort model, occupant-response study, or real deployment evaluation. The energy numbers should be interpreted as safe shiftable-load opportunity under the recorded test period and recorded load streams.

## Canonical Result Files

- Model metrics: `results/model_metrics_empty_positive.csv`
- Validation-selected policies: `results/selected_threshold_policies.csv`
- Test policy results: `results/threshold_policy_results_test.csv`
- Threshold sweep and Pareto input: `results/energy_risk_tradeoff_threshold_sweep.csv`
- Pareto frontier output: `results/energy_risk_pareto_frontier.csv`
- Stable-window summary: `results/stable_window_metrics.csv`
- Detailed continuous-window metrics: `results/continuous_empty_window_policy_results_test.csv`
- Energy sensitivity: `results/energy_sensitivity_analysis.csv`
- Prediction export: `results/forecast_predictions_test_all_models.csv`

Legacy duplicate or alias outputs are preserved under `results/archive/`.

## First Figures To Inspect

- `figures/energy_risk_tradeoff_pareto.png` - threshold sweep showing risk versus safe opportunity.
- `figures/threshold_policy_safe_opportunity.png` - safe opportunity under validation-selected risk constraints.
- `figures/threshold_policy_occupancy_conflict.png` - held-out test conflict rate under selected policies.
- `figures/stable_window_sensitivity.png` - sensitivity to minimum empty-window duration.
- `figures/model_metrics_empty_positive.png` - Empty-positive model metrics.
