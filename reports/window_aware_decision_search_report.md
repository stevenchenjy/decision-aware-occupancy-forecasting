# Window-aware decision search report

> **Final-audit status:** exploratory offline, post-bin saved-output diagnostic. A 00:00 anchor is the left label of a completed [00:00, 00:15) input bin, so its effective boundary is 00:15. All "safe" legacy fields mean subsequently camera-label-empty processed-load-proxy overlap, not physical absence, calibrated risk, savings, or a deployable policy. The historical candidates cannot be promoted after the required empirical retraining.

## Material Passport

- Origin Skill: experiment-agent
- Origin Mode: validate/run
- Verification Status: ANALYZED
- Version Label: window_aware_search_v1

## Result in brief

The validation-only study evaluated 8,547 unique weight-threshold pairs under 20 pre-specified window/AUPRC constraint combinations (170,940 constraint rows). The forecasting floors did not change the selected optimum at any window floor because every selected solution already exceeded 99% of the best validation AUPRC.

The clearest validation compromise is the historical `W_min=85%, Q=99%` challenger: `0.40/0.40/0.20` at threshold `0.850`. It produced validation AUPRC `0.7233`, interval conflict `8.56%`, all-camera-label-empty window rate `85.71%` (18/21), and `406.7 kWh of offline load-proxy overlap. This historical selection preceded the current-test retrospective diagnostic.

No result deserves promotion or a headline change now. The enlarged search remains exploratory, and the current test period is already inspected.

## Validation-selected candidates

| W floor | Q floor | Weights S/L/T | Threshold | AUPRC | Interval conflict | All-label-empty windows | Proxy kWh | Coverage | Windows label-empty/total |
|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|
| 80% | 99% | 0.05/0.75/0.20 | 0.875 | 0.7283 | 7.84% | 80.00% | 507.7 | 9.54% | 20/25 |
| 85% | 99% | 0.40/0.40/0.20 | 0.850 | 0.7233 | 8.56% | 85.71% | 406.7 | 7.80% | 18/21 |
| 90% | 99% | 0.30/0.60/0.10 | 0.900 | 0.7231 | 8.08% | 90.00% | 353.0 | 6.94% | 18/20 |
| 95% | 99% | 0.10/0.65/0.25 | 0.950 | 0.7286 | 0.00% | 100.00% | 80.8 | 2.00% | 8/8 |
| 100% | 99% | 0.10/0.65/0.25 | 0.950 | 0.7286 | 0.00% | 100.00% | 80.8 | 2.00% | 8/8 |

## Why about 3% interval conflict still produced four conflict windows

Interval conflict pools intervals across all recommendations, whereas a window becomes conflicting after a single occupied interval. In the retrospective current-test diagnostic:

- The decision-optimal candidate had `10` occupied intervals among `336` recommendations (2.98%), distributed across `4` windows. One conflict window contained seven occupied intervals; three contained one each.
- The 99%-floor candidate had `11` occupied intervals among `356` recommendations (3.09%), also across `4` windows. One contained seven occupied intervals, one contained two, and two contained one each.

Thus low interval conflict does not imply that almost every recommended window is all-camera-label-empty.

## Opportunity cost of stronger window floors

Using the common 99% AUPRC floor (the same optima occur for the other Q settings):

- W>=80%: `507.7 kWh`, `80.0%` all-camera-label-empty windows.
- W>=85%: `406.7 kWh`, a loss of `101.0 kWh` versus W>=80%.
- W>=90%: `353.0 kWh`, a loss of `154.7 kWh` (30.5%).
- W>=95%: `80.8 kWh`, a loss of `426.9 kWh` (84.1%). The discrete optimum is actually 100% all-camera-label-empty.
- W=100%: `80.8 kWh`, a loss of `426.9 kWh` (84.1%). It is the same discrete candidate as W>=95%.

Relative to the unconstrained decision candidate's `577.0 kWh`, W>=90% gives up `224.0 kWh`, and the all-camera-label-empty candidate gives up `496.2 kWh`.

## Interpretation of the existing 99%-AUPRC-floor candidate

The existing 99%-floor candidate has only `75.9%` all-camera-label-empty validation windows (22/29), so it fails even the lowest new 80% window floor. Its retrospective current-test rate is `77.8%`. Its high offline proxy overlap remains descriptively interesting, but it is not attractive under the historical window-aware rule.

## Operational compromise

The W>=85%, Q=99% challenger is the clearest validation compromise: it raises the all-camera-label-empty-window rate by `+5.7` percentage points and offline load-proxy overlap by `+38.2 kWh` versus the canonical validation reference, while keeping interval conflict below 10% and AUPRC above 99% of the validation best. W>=90% has a higher label-empty window rate but no longer exceeds canonical validation proxy overlap; W>=95%/100% is highly conservative with only `8` recommended windows.

This is a validation-based compromise, not evidence of deployment safety.

## Retrospective current-test diagnostic

`results/window_aware_current_test_diagnostic.csv` evaluates every unique frozen definition only after selection. It is explicitly not a fresh untouched evaluation, and its results did not alter the W>=85%, Q=99% rule, any weights, or any threshold.

For transparency, the historical primary challenger produced retrospective point estimates of `0.8610` Empty AUPRC, `2.49%` interval conflict, `93.75%` all-camera-label-empty windows (15/16), and `511.6 kWh of offline load-proxy overlap. These already-inspected outcomes cannot support promotion or further adaptation.

## Robustness and headline decision

- **Headline:** unchanged. The canonical primary remains the official reference.
- **Confidence:** caution. Window outcomes are based on 39 validation and 43 already-inspected test horizons; windows are clustered within days, and this expanded search adds selection multiplicity.
- **Required before promotion:** a new chronological period, fixed candidate application, paired daily-block uncertainty, day-influence analysis, and mechanical application of every gate in `reports/future_untouched_evaluation_protocol.md`.
- **Claims boundary:** offline label-empty load-proxy overlap is not verified energy savings, and observed label-empty windows are not a safety guarantee.

## Statistical-integrity and fallacy scan

Coverage: **11/11** types checked. Simpson/ecological/Berkson/collider/regression-to-mean/reverse-causality mechanisms are not directly tested by this constrained saved-output comparison; no subgroup or causal claim is made. Base rates are accompanied by counts and coverage. All complete saved horizons are retained, reducing survivorship concerns. **Look-elsewhere and garden-of-forking-paths remain cautions** because 170,940 constraint rows summarize an enlarged exploratory search. **Correlation-versus-causation remains a caution:** load opportunity coinciding with observed Empty labels does not prove savings or control safety.

## Recommendation

Keep all window-aware results secondary. Freeze the W>=85%, Q=99% challenger for the primary comparison on a future untouched period, and do not promote it unless every pre-specified protocol gate passes.
