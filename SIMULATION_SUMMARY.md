# Offline Post-Bin Recommendation Summary

**Audit status: requires empirical rerun.** This is an offline score-to-policy accounting exercise, not a counterfactual building simulation or a deployed control study.

## Policy interpretation

For each model, a score threshold is selected on 39 validation midnight-labelled horizons to maximize offline safe opportunity subject to empirical interval conflict no greater than 10% and a one-hour stable-window rule. The fixed rule is then accounted on 43 historical test horizons. A midnight label is a completed '[00:00,00:15)' input bin, so its effective boundary is 00:15.

## Primary saved-output result

| Quantity | Value |
|---|---:|
| Nominal selected score threshold | 0.875 |
| Validation interval conflict | 8.75% |
| Test interval conflict | 0/259 = 0.00% observed |
| Offline safe opportunity | 490.1 kWh |
| Recommended/safe/conflict intervals | 259 / 259 / 0 |
| Recommended/safe/conflict windows | 14 / 14 / 0 |

The proxy is 'max(hvac_S + lig_S, 0) × 0.25 h' only where a recommendation and subsequent camera-empty label coincide. It is not energy saved, shifted energy, controllable capacity, physical absence, or a safety guarantee.

## Non-unique selection

The primary weights and threshold are nominal validation choices rather than robustly unique optima. See 'results/validation_selection_stability.csv'. Expanded decision-aware/window-aware results are retrospective exploratory diagnostics, not substitutes for a later untouched evaluation.
