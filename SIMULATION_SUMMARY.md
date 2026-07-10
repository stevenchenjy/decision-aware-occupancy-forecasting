# Offline Risk-Constrained Recommendation Summary

## Purpose

This is an offline decision-layer evaluation, not a building simulation in the counterfactual-control sense. Forecast probabilities are converted into stable empty-window recommendations, and recorded load is counted as safe opportunity only when the recommendation coincides with actual emptiness.

## Policy definition

For each model and risk limit `delta`:

1. Evaluate Empty thresholds `0.05..0.95` in steps of `0.025` on non-overlapping validation midnight horizons.
2. Require at least four consecutive recommended Empty intervals (one hour).
3. Select the threshold that maximizes validation safe opportunity subject to occupancy conflict `<= delta`.
4. Apply the fixed threshold once to the 43 held-out test midnight horizons.

The default risk limit is 10%.

## Primary hybrid 10% policy

| Quantity | Value |
|---|---:|
| Selected Empty threshold | 0.875 |
| Validation conflict rate | 8.75% |
| Test conflict rate | 0/259 = 0.00% observed |
| Recommendation coverage | 6.27% |
| Safe opportunity | 490.1 kWh |
| Gross opportunity | 490.1 kWh |
| Opportunity per day | 11.40 kWh/day |
| Recommended/safe/conflict intervals | 259 / 259 / 0 |
| Recommended/safe/conflict windows | 14 / 14 / 0 |
| Average recommended window duration | 4.63 hours |
| Test schedules | 43 days |

The same test-period comparison is:

- LightGBM: 493.9 kWh, 4.15% conflict, 265 recommended intervals, 19 windows.
- Historical Average: 94.6 kWh, 0.00% conflict, 66 intervals, 12 windows.
- Original Transformer: 97.4 kWh, 9.68% conflict, 31 intervals, 2 windows.
- Seasonal-Transformer Blend: 457.9 kWh, 0.00% conflict, 249 intervals, 14 windows.

## Opportunity calculation

Default controllable-load proxy:

`P_controllable = max(hvac_S + lig_S, 0)`

Per safe 15-minute interval:

`opportunity_kWh = P_controllable * 0.25`

Conflict intervals are excluded from safe opportunity. Daily midnight horizons prevent energy double counting across the overlapping model-evaluation forecasts.

## Stable-window sensitivity

The integrated sensitivity table evaluates minimum recommended durations of 0.25, 0.5, 1, 2, and 4 hours while keeping each model's validation-selected 10% threshold fixed. The primary hybrid remains at zero observed interval conflicts across those tested minimum durations; safe opportunity decreases from 497.0 kWh at 0.25 hours to 407.8 kWh at 4 hours.

Source: `results/hybrid_stable_window_sensitivity.csv` and `figures/hybrid_stable_window_sensitivity.png`.

## Risk-opportunity interpretation

The canonical two-panel figure distinguishes:

- validation sweeps used for threshold selection,
- Pareto-efficient frontiers,
- validation-selected 10% operating points,
- held-out test sweeps shown only as diagnostics.

The test sweep must not be used to choose a model, weight, or threshold. The exploratory balanced hybrid appears in the plot for supplementary comparison only.

Source: `results/hybrid_risk_opportunity_threshold_sweeps.csv` and `figures/risk_opportunity_validation_vs_test_diagnostic.png`.

## Uncertainty and safety language

Zero observed conflict is a finite-sample observation, not proof of a zero-risk policy. All 14 observed primary-hybrid recommendation windows were safe, but a one-sided independent-window upper bound is still about 19.3%, and the independence assumption is not justified. The held-out period is short and contains only one building and season range.

Use “safe shiftable-load opportunity under recorded test labels,” not “verified savings” or “guaranteed safe control.”
