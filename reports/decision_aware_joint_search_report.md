# Decision-aware joint weight-threshold search

> **Final-audit status:** exploratory offline, post-bin saved-output diagnostic. A 00:00 anchor is the left label of a completed [00:00, 00:15) input bin, so its effective boundary is 00:15. "Safe" legacy fields mean subsequently camera-label-empty processed-load-proxy overlap, not physical absence, calibrated risk, savings, or a deployable policy. This search cannot replace the canonical result or promote a candidate after the required empirical retraining.

## Material Passport

- Origin Skill: experiment-agent
- Origin Mode: validate/run
- Verification Status: ANALYZED
- Version Label: decision_aware_joint_search_v1

## Result in brief

The joint search did choose different unconstrained decision-optimal weights from the canonical `0.15/0.60/0.25`; the 99%-AUPRC-floor candidate also differed. Candidates were selected exclusively on validation. The held-out test was loaded only after weights and thresholds were fixed.

Keep the 99%-floor candidate as a secondary exploratory result. Its held-out point estimates are promising, but the same test period cannot both motivate a replacement and provide a fresh confirmation, and no paired uncertainty analysis was prespecified for this enlarged search.

## Validation-selected strategies

| Candidate | Weights (Seasonal/LGBM/Transformer) | Threshold | AUPRC | Conflict | Label-empty proxy kWh | Coverage | Intervals (rec/label-empty/conflict) | Windows (rec/all-label-empty/conflict) |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Current primary hybrid (forecast-optimal) | 0.15/0.60/0.25 | 0.875 | 0.7286 | 8.75% | 368.5 | 7.02% | 263/240/23 | 15/12/3 |
| Decision-optimal 10% hybrid | 0.65/0.05/0.30 | 0.775 | 0.7144 | 9.35% | 577.0 | 10.28% | 385/349/36 | 28/22/6 |
| Decision-optimal hybrid (99% AUPRC floor) | 0.35/0.35/0.30 | 0.800 | 0.7262 | 9.80% | 575.1 | 10.90% | 408/368/40 | 29/22/7 |

Relative to the forecast-optimal reference, the unconstrained decision candidate changed validation AUPRC by -0.0142, conflict by +0.61 percentage points, and offline proxy overlap by +208.5 kWh. The 99%-floor candidate changed those quantities by -0.0025, +1.06 percentage points, and +206.6 kWh, respectively.

## AUPRC-floor sensitivity (validation only)

| AUPRC floor | Weights (Seasonal/LGBM/Transformer) | Threshold | Validation AUPRC | Conflict | Label-empty proxy kWh | Coverage | Windows |
|---|---|---:|---:|---:|---:|---:|---:|
| no_floor | 0.65/0.05/0.30 | 0.775 | 0.7144 | 9.35% | 577.0 | 10.28% | 28 |
| 95% | 0.65/0.05/0.30 | 0.775 | 0.7144 | 9.35% | 577.0 | 10.28% | 28 |
| 98% | 0.65/0.05/0.30 | 0.775 | 0.7144 | 9.35% | 577.0 | 10.28% | 28 |
| 99% | 0.35/0.35/0.30 | 0.800 | 0.7262 | 9.80% | 575.1 | 10.90% | 29 |

This is a constrained sensitivity analysis, not an arbitrary weighted-sum score. Every row enforces interval conflict `<=10%`, positive coverage, and at least one stable recommended window.

## Held-out test evaluation of fixed candidates

| Candidate | Weights (Seasonal/LGBM/Transformer) | Threshold | AUPRC | Conflict | Label-empty proxy kWh | Coverage | Intervals (rec/label-empty/conflict) | Windows (rec/all-label-empty/conflict) |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Current primary hybrid (forecast-optimal) | 0.15/0.60/0.25 | 0.875 | 0.8514 | 0.00% | 490.1 | 6.27% | 259/259/0 | 14/14/0 |
| Decision-optimal 10% hybrid | 0.65/0.05/0.30 | 0.775 | 0.8604 | 2.98% | 623.5 | 8.14% | 336/326/10 | 21/17/4 |
| Decision-optimal hybrid (99% AUPRC floor) | 0.35/0.35/0.30 | 0.800 | 0.8569 | 3.09% | 650.4 | 8.62% | 356/345/11 | 18/14/4 |
| LightGBM reference | 0.00/1.00/0.00 | 0.950 | 0.8382 | 4.15% | 493.9 | 6.42% | 265/254/11 | 19/16/3 |
| Historical Average reference | 1.00/0.00/0.00 | 0.950 | 0.8497 | 0.00% | 94.6 | 1.60% | 66/66/0 | 12/12/0 |

- Unconstrained decision-optimal versus current primary: AUPRC +0.0090, conflict +2.98 percentage points, offline proxy overlap +133.3 kWh. The validation proxy-overlap difference carried to the held-out point estimate.
- 99%-floor decision-optimal versus current primary: AUPRC +0.0055, conflict +3.09 percentage points, offline proxy overlap +160.3 kWh. The validation proxy-overlap difference carried to the held-out point estimate.
- Unconstrained decision-optimal versus LightGBM: AUPRC +0.0222, conflict -1.17 percentage points, offline proxy overlap +129.6 kWh.
- 99%-floor decision-optimal versus LightGBM: AUPRC +0.0188, conflict -1.06 percentage points, offline proxy overlap +156.5 kWh.
- Current primary versus LightGBM on test: AUPRC +0.0132, conflict -4.15 percentage points, offline proxy overlap -3.8 kWh.

The decision-aware proxy-overlap differences are sizable as point estimates (+27.2% without a floor and +32.7% with the 99% floor versus the current hybrid), but they trade zero observed conflict for roughly 3% conflict. Without a prespecified paired uncertainty analysis or another untouched evaluation period, statistical or operational meaningfulness is not established.

These are descriptive point estimates on one held-out period. The label-empty proxy overlap means processed HVAC-plus-lighting load coinciding with recommendations that were subsequently observed camera-label-empty; it is neither verified energy savings nor a guarantee of safety.

## Coverage and conservatism

No selected hybrid met the prespecified diagnostic flag of below 1% validation coverage or two or fewer validation windows. Coverage and window counts still need to be interpreted alongside conflict: zero or low conflict from very few recommendations is not strong evidence of general safety.

## Scientific interpretation

- The weight search optimized 231 simplex points jointly with 37 thresholds (8,547 validation pairs), so the decision candidates are exploratory and exposed to selection optimism even though test leakage was prevented.
- AUPRC is constant across thresholds for a fixed weight vector; policy outcomes are evaluated only on 39 non-overlapping validation midnight horizons. The 43 test horizons are a modest operational sample and windows are clustered within days.
- Comparison with LightGBM and the current hybrid is descriptive. No confidence interval or hypothesis test was prespecified for the enlarged joint search, so small point-estimate differences should not be called meaningful improvements.
- Keep the 99%-floor candidate as a secondary exploratory result. Its held-out point estimates are promising, but the same test period cannot both motivate a replacement and provide a fresh confirmation, and no paired uncertainty analysis was prespecified for this enlarged search.

## Statistical-integrity and fallacy scan

Coverage: **11/11** experiment-agent fallacy types checked.

| Check | Disposition |
|---|---|
| Simpson's paradox | Not assessable from the aggregate joint table; no subgroup claim is made. |
| Ecological fallacy | Avoided: claims remain at forecast-horizon/interval level, not individual occupants. |
| Berkson's paradox | No new sample filtering was introduced beyond the fixed chronological splits. |
| Collider bias | No covariate adjustment is performed in this saved-output search. |
| Base-rate neglect | AUPRC, coverage, interval counts, and observed Empty outcomes are reported together. |
| Regression to the mean | No extreme-case pre/post subgroup is analyzed. |
| Survivorship bias | All complete saved horizons in the declared scopes are used; missing-load mapping was zero. |
| Look-elsewhere effect | **Caution:** 8,547 validation pairs were searched; held-out results are descriptive confirmation only. |
| Garden of forking paths | **Caution:** this is a newly specified exploratory objective; floor sensitivity is reported to expose that choice. |
| Correlation versus causation | **Caution:** opportunity accounting does not establish energy savings or causal control effects. |
| Reverse causality | Not directly applicable to fixed forecasts evaluated against subsequent labels. |

## Recommendation

Keep the 99%-floor candidate as a secondary exploratory result. Its held-out point estimates are promising, but the same test period cannot both motivate a replacement and provide a fresh confirmation, and no paired uncertainty analysis was prespecified for this enlarged search.
