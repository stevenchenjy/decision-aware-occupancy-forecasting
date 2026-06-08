# Offline Evaluation Summary: Risk-Constrained Stable Empty-Window Recommendation

## Purpose

This offline evaluation converts day-ahead occupancy forecasts into threshold-based empty-window recommendations for facility-management decision support. The operating question is:

How much safe shiftable-load opportunity can be identified while keeping occupancy-conflict risk below a chosen constraint?

The default selected example is LightGBM under the 10% validation-selected occupancy-conflict policy.

## 1. Stable-Window Evaluation

Stable empty window means the model recommends Empty for at least N consecutive 15-minute intervals. This is closer to real building operations than evaluating isolated 15-minute intervals.

LightGBM, 10% validation-selected policy, selected Empty threshold = 0.95:

| Minimum window | Test conflict rate | Window precision | Window recall | Safe opportunity | kWh/day | Recommended windows | Safe windows | Average duration |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 hour | 4.15% | 84.21% | 27.14% | 493.9 kWh | 11.49 | 19 | 16 | 3.49 h |
| 2 hours | 3.69% | 86.67% | 31.37% | 482.7 kWh | 11.23 | 15 | 13 | 4.07 h |
| 4 hours | 1.48% | 80.00% | 22.73% | 313.2 kWh | 7.28 | 5 | 4 | 6.75 h |

Files:

- `results/stable_window_metrics.csv`
- `figures/stable_window_sensitivity.png`

## 2. Pareto Frontier Analysis

The Pareto analysis sweeps Empty probability thresholds and plots:

- X-axis: occupancy conflict rate
- Y-axis: safe shiftable-load opportunity in kWh

This shows each model's risk-reward tradeoff instead of a single operating point.

Files:

- `results/energy_risk_tradeoff_threshold_sweep.csv`
- `results/energy_risk_pareto_frontier.csv`
- `figures/energy_risk_tradeoff_pareto.png`

## 3. Energy Opportunity Clarification

The reported 493.9 kWh comes from:

- Load variables: `hvac_S + lig_S`
- Load interpretation: proxy controllable load, HVAC south plus lighting south
- Formula: `kWh = kW * 0.25` for each 15-minute interval
- Safe opportunity: recommended intervals that are actually empty only
- Conflict intervals are excluded from safe opportunity

LightGBM, 10% validation-selected policy:

| Quantity | Value |
|---|---:|
| Gross recommended load opportunity | 537.9 kWh |
| Conflict load excluded | 44.0 kWh |
| Safe shiftable-load opportunity | 493.9 kWh |
| kWh/day | 11.49 |
| Recommended windows | 19 |
| Safe windows | 16 |
| kWh/safe window | 30.87 |

Statistical period:

- Test target period: 2019-01-09 00:00:00-08:00 to 2019-02-21 02:00:00-08:00
- Non-overlapping daily schedules: 43

Double-counting prevention:

- Energy-risk policy uses non-overlapping daily forecast anchors.
- Stable windows are extracted as disjoint consecutive runs.
- Overlapping rolling forecasts are not summed for energy opportunity.

Important wording:

This is safe shiftable-load opportunity, not verified energy savings. Confirmed savings would require a counterfactual energy baseline, simulation, or intervention data.

Files:

- `results/safe_shiftable_load_opportunity.csv`
- `figures/safe_shiftable_load_by_model.png`

## 4. Robustness Checks

The package includes three robustness checks.

### Block Bootstrap Confidence Intervals

LightGBM, 10% policy, daily block bootstrap:

| Metric | Mean | 95% CI |
|---|---:|---:|
| Empty AUPRC | 0.8384 | [0.7700, 0.8958] |
| Occupancy conflict rate | 4.43% | [0.00%, 11.82%] |
| Safe shiftable-load opportunity | 527.2 kWh | [95.8, 1195.6] |

### Rolling-Origin Validation

LightGBM rolling-origin temporal validation:

- Mean Empty AUPRC: 0.7951
- Mean Empty F1: 0.7196

### Multiple Random Seeds

LightGBM multiple-seed check:

- Empty AUPRC mean: 0.8354, range/CI stored in `results/robustness_summary.csv`
- Empty F1 mean: 0.7579, range/CI stored in `results/robustness_summary.csv`

Files:

- `results/robustness_summary.csv`
- `results/block_bootstrap_confidence_intervals.csv`
- `results/rolling_origin_cv.csv`
- `results/seed_model_metrics.csv`

## 5. Example-Day Visualization

The LightGBM example day illustrates how forecast becomes recommendation:

1. Forecast future Empty probability.
2. Apply the selected Empty threshold.
3. Keep only stable windows with at least 1 continuous hour.
4. Mark recommended windows as safe or conflict based on actual occupancy.
5. Overlay HVAC+lighting load during the horizon.

Selected example:

- Model: LightGBM
- Policy: 10% validation-selected occupancy-conflict policy
- Selected threshold: 0.95
- Forecast anchor: 2019-02-17 00:00:00-08:00

Figure:

- `figures/example_day_lightgbm_recommendation.png`

The figure includes actual occupancy, predicted Empty probability, selected threshold, recommended windows, safe windows, conflict window definition, and load during the recommendation horizon.
