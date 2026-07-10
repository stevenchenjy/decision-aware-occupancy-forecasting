# Results Summary

## Revised scientific conclusion

Building 59 occupancy has strong weekday/time-of-day structure, which explains the competitive Historical Average baseline. A validation-selected probability ensemble combines that train-only seasonal prior with LightGBM's nonlinear tabular signal and the Transformer's temporal sequence signal. Its test Empty AUPRC point estimate is slightly above the schedule baseline, while its validation-selected 10% policy identifies `490.1 kWh` of safe opportunity—within `3.8 kWh` of LightGBM—with zero observed conflicts among 259 recommended intervals in this 43-day test period.

The model-level advantage over Historical Average and LightGBM is not decisive: paired daily-block AUPRC difference intervals include zero. Likewise, zero observed conflict is not a guarantee of zero future risk.

## Protocol

- Dataset: LBNL Building 59 selected south-zone streams.
- Local timezone: `America/Los_Angeles` after UTC interpretation.
- Frequency: 15 minutes.
- History/horizon: 96/96 steps (24 hours each).
- Positive class: Empty=1.
- Splits: chronological, with 24.25-hour train-validation and validation-test gaps.
- Model metrics: all overlapping rolling forecast rows.
- Policy selection/evaluation: 39 validation and 43 test non-overlapping midnight horizons.
- Stable recommendation: at least four consecutive 15-minute intervals.
- Default opportunity: recorded `hvac_S + lig_S`, multiplied by 0.25 hour, counted only when recommended and actually empty.

## Model-level test comparison

| Model | Role | Empty AUPRC | Empty precision | Empty recall | Empty F1 |
|---|---|---:|---:|---:|---:|
| Historical Average | schedule baseline | 0.8497 | 0.7264 | 0.8015 | 0.7621 |
| LightGBM | reference | 0.8382 | 0.7610 | 0.7593 | 0.7601 |
| Random Forest | original | 0.8329 | 0.7510 | 0.8019 | 0.7756 |
| Original Transformer | original | 0.7621 | 0.7253 | 0.6022 | 0.6581 |
| DLinear | original | 0.5933 | 0.5764 | 0.6657 | 0.6179 |
| Seasonal-Transformer Blend | validation-selected intermediate | 0.8490 | 0.7465 | 0.7408 | 0.7436 |
| Hybrid Seasonal-GBDT-Transformer | validation-selected primary | 0.8514 | 0.7677 | 0.7556 | 0.7616 |
| Exploratory Hybrid Balanced Tree-Deep | test-ranked supplementary | 0.8554 | 0.7659 | 0.7649 | 0.7654 |

Source: `results/canonical_model_comparison.csv`.

## Validation-selected 10% policies

| Model | Threshold | Validation conflict | Test conflict | Safe kWh | Recommended/safe/conflict intervals | Recommended/safe windows | Coverage | kWh/day |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Historical Average | 0.950 | 8.33% | 0.00% | 94.6 | 66 / 66 / 0 | 12 / 12 | 1.60% | 2.20 |
| LightGBM | 0.950 | 9.61% | 4.15% | 493.9 | 265 / 254 / 11 | 19 / 16 | 6.42% | 11.49 |
| Random Forest | 0.925 | 4.20% | 5.32% | 359.5 | 188 / 178 / 10 | 10 / 7 | 4.55% | 8.36 |
| Original Transformer | 0.900 | 2.20% | 9.68% | 97.4 | 31 / 28 / 3 | 2 / 1 | 0.75% | 2.27 |
| DLinear | 0.875 | 7.55% | 43.87% | 185.1 | 155 / 87 / 68 | 7 / 3 | 3.75% | 4.30 |
| Seasonal-Transformer Blend | 0.800 | 8.53% | 0.00% | 457.9 | 249 / 249 / 0 | 14 / 14 | 6.03% | 10.65 |
| Hybrid Seasonal-GBDT-Transformer | 0.875 | 8.75% | 0.00% | 490.1 | 259 / 259 / 0 | 14 / 14 | 6.27% | 11.40 |
| Exploratory Hybrid Balanced Tree-Deep | 0.875 | 8.14% | 0.00% | 446.5 | 256 / 256 / 0 | 14 / 14 | 6.20% | 10.38 |

The balanced model's threshold was selected on validation, but its model architecture remains test-ranked; this row is diagnostic/supplementary rather than a selected deployment recommendation.

Source: `results/canonical_policy_10pct.csv`.

## Primary-hybrid differences

| Comparator | Empty AUPRC difference | Relative AUPRC difference | Safe-kWh difference | Relative safe-kWh difference | Test conflict-rate difference | Coverage difference |
|---|---:|---:|---:|---:|---:|---:|
| Original Transformer | +0.0893 | +11.71% | +392.7 kWh | +403.03% | -9.68 percentage points | +5.52 percentage points |
| Historical Average | +0.0017 | +0.20% | +395.5 kWh | +418.00% | 0.00 percentage points | +4.68 percentage points |
| LightGBM | +0.0132 | +1.58% | -3.8 kWh | -0.76% | -4.15 percentage points | -0.15 percentage points |
| Seasonal-Transformer Blend | +0.0024 | +0.28% | +32.3 kWh | +7.04% | 0.00 percentage points | +0.24 percentage points |

Differences are arithmetic point-estimate comparisons, not proof of superiority.

## Uncertainty

Two thousand paired bootstrap resamples use the 43 non-overlapping midnight test horizons and keep the validation-selected thresholds fixed.

| Quantity | Point estimate | 95% daily-block bootstrap interval |
|---|---:|---:|
| Primary hybrid daily-horizon Empty AUPRC | 0.8522 | [0.7918, 0.9016] |
| Primary hybrid safe opportunity | 490.1 kWh | [153.1, 966.7] |
| Primary minus LightGBM daily-horizon Empty AUPRC | +0.0163 | [-0.0050, +0.0426] |
| Primary minus Historical Average daily-horizon Empty AUPRC | +0.0042 | [-0.0304, +0.0377] |
| Primary minus LightGBM safe opportunity | -3.8 kWh | [-208.2, +174.6] |
| Primary minus Historical Average safe opportunity | +395.5 kWh | [+127.0, +786.2] |

The all-overlap headline AUPRC (`0.8514`) and daily-horizon bootstrap point (`0.8522`) use different row scopes. The latter avoids summing overlapping daily forecasts and is used for uncertainty.

All observed primary-hybrid conflict blocks are zero, so a nonparametric bootstrap cannot create unseen conflicts and returns `[0,0]`. A one-sided independent-trial 95% upper bound is approximately 1.15% for 259 intervals and 19.3% for 14 windows; interval/window independence is not established. These are cautionary bounds, not guarantees.

Source: `results/hybrid_uncertainty_daily_block_bootstrap.csv` and `results/primary_hybrid_zero_conflict_bound.csv`.

## Calibration and robustness

- Primary hybrid Brier: `0.0928`; log loss: `0.2984`; 10-bin diagnostic ECE: `0.0253`.
- No post-hoc probability recalibration was applied.
- Stable-window sensitivity is available from 0.25 to 4 hours.
- Base components average seeds 42, 43, and 44.
- Hybrid-specific seed dispersion is unavailable because aligned per-seed component predictions were not saved.
- Hybrid rolling-origin validation is unavailable because saved folds omit Transformer predictions.

See `results/hybrid_calibration_summary.csv`, `results/hybrid_stable_window_sensitivity.csv`, and `results/hybrid_robustness_scope.csv`.

## Canonical interpretation

Supported: the hybrid identifies recorded periods where shiftable load coincides with predicted and realized emptiness under an offline validation-selected policy.

Not supported: verified savings, causal energy reduction, comfort preservation, generalization beyond this building/period, or guaranteed zero-conflict operation.
