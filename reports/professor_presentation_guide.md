# Professor Presentation Guide

## Presentation status

The canonical headline remains the validation-selected `0.15/0.60/0.25` Seasonal/LightGBM/Transformer hybrid at threshold `0.875`. Decision-aware and window-aware candidates are exploratory, and their already-inspected current-test values must not be used to promote or further tune them.

## Recommended thesis

Strong recurring occupancy schedules explain why the train-only Historical Average is competitive. A validation-selected probability hybrid combines that seasonal prior with LightGBM's nonlinear tabular signal and the original Transformer's temporal-sequence signal. In this 43-day held-out period, its Empty AUPRC point estimate is slightly above the schedule baseline, while its validation-selected 10% policy identifies nearly the same safe load-proxy opportunity as LightGBM with zero observed conflicts among 259 recommended intervals. The AUPRC differences are uncertain, zero observed conflict is not a guarantee of future safety, and recorded safe opportunity is not measured energy savings.

## Main presentation sequence

### 1. Research question and protocol

Use `README.md` and `SIMULATION_SUMMARY.md`.

State explicitly:

- Empty is the positive class.
- Models use chronological validation and test exports with 24-hour horizons.
- Canonical weights and operating thresholds were fixed on validation before test evaluation.
- Recorded `hvac_S + lig_S` is an offline opportunity proxy, not realized savings.

### 2. Original Transformer to canonical primary

Figure: `figures/transformer_old_vs_new.png`

Supported claim: seasonal blending raises test Empty AUPRC from `0.7621` to `0.8490`; the validation-selected three-way primary reaches `0.8514`. Under the fixed 10% policy, safe opportunity rises from `97.4` to `490.1 kWh`.

Required limitation: this does not establish decisive superiority over Historical Average or LightGBM.

### 3. Canonical model comparison

Figure: `figures/canonical_empty_metrics_comparison.png`

Table: `results/canonical_model_comparison.csv`

Supported claim: the canonical primary has a test Empty AUPRC point estimate of `0.8514`, narrowly above Historical Average (`0.8497`) and LightGBM (`0.8382`).

Required limitation: paired daily-block AUPRC intervals include zero. The hatched `0.8554` balanced candidate is supplementary because its architecture was highlighted after test ranking.

### 4. Fixed 10% policy comparison

Figure: `figures/canonical_policy_10pct_comparison.png`

Table: `results/canonical_policy_10pct.csv`

Supported claim: the canonical primary identifies `490.1 kWh` of safe opportunity with `0/259` observed interval conflicts and `14/14` fully safe windows; LightGBM identifies `493.9 kWh` with `11/265` conflicts and `16/19` fully safe windows.

Required limitation: zero observed conflict is a finite-period observation; the opportunity difference from LightGBM is small and uncertain.

### 5. Selection versus diagnosis

Figure: `figures/risk_opportunity_validation_vs_test_diagnostic.png`

State explicitly: the validation surface selects operating points. Test surfaces are diagnostic only and cannot justify another model, weight, or threshold choice.

### 6. Stable-window sensitivity and example day

Figures:

- `figures/hybrid_stable_window_sensitivity.png`
- `figures/hybrid_lightgbm_historical_same_day.png`

Required limitations: the sensitivity keeps the one-hour-rule thresholds fixed, and the illustrated day was chosen for explanation after evaluation rather than as evidence of typical performance.

## Exploratory decision-aware appendix

Use this material after the canonical story, not as a replacement headline.

Figures:

- `figures/forecast_optimal_vs_decision_optimal.png` for validation-selected weights, thresholds, AUPRC, conflict, and opportunity;
- `figures/decision_aware_joint_validation_frontier.png` for the validation-only trade-off surface;
- `figures/decision_aware_joint_test_comparison.png` for descriptive evaluation after candidates were fixed.

Source tables:

- `results/decision_aware_joint_selected_candidates.csv`
- `results/decision_aware_joint_auprc_floor_sensitivity.csv`

| Status | Weights S/L/T | Threshold | Current-test Empty AUPRC | Interval conflict | Safe opportunity |
|---|---|---:|---:|---:|---:|
| Canonical primary | `0.15/0.60/0.25` | 0.875 | 0.8514 | 0.00% observed | 490.1 kWh |
| Exploratory decision-optimal | `0.65/0.05/0.30` | 0.775 | 0.8604 | 2.98% | 623.5 kWh |
| Exploratory 99%-AUPRC-floor | `0.35/0.35/0.30` | 0.800 | 0.8569 | 3.09% | 650.4 kWh |

Speaking note: 8,547 weight-threshold pairs were searched on validation. The exploratory opportunity gains are point estimates, trade zero observed canonical conflict for about 3% interval conflict, and have no prespecified paired confirmation on another untouched period.

## Exploratory window-aware appendix

Figures:

- `figures/window_aware_validation_tradeoff.png`
- `figures/interval_vs_window_safety.png`
- `figures/window_conflict_severity.png`

Source tables:

- `results/window_aware_selected_candidates.csv`
- `results/window_conflict_severity_metrics.csv`
- `results/window_aware_current_test_diagnostic.csv`

The frozen primary future challenger is `0.40/0.40/0.20` at threshold `0.850`, selected on validation under interval conflict `<=10%`, fully safe window rate `>=85%`, and Empty AUPRC `>=99%` of the best validation AUPRC. Its current-test values—AUPRC `0.8610`, interval conflict `2.49%`, `15/16` fully safe windows, and `511.6 kWh`—are retrospective diagnostics only.

Speaking note: a low pooled interval-conflict rate can still produce several conflict windows because one occupied interval makes an entire recommended window conflicting. Do not use the current-test diagnostic to revise the window floor or select another challenger.

## Future-evaluation slide

Use `reports/future_untouched_evaluation_protocol.md` and `reports/next_phase_recommendation.md`.

The correct next claim is procedural: candidates are frozen for one-shot evaluation on a genuinely new chronological period. The canonical primary remains in place unless every prespecified promotion gate passes.

## Avoid in the headline

- Do not call any exploratory candidate the new best or deployable model.
- Do not use current-test point estimates to choose among frozen candidates.
- Do not describe `0.8514` versus nearby baselines as decisive.
- Do not call safe opportunity realized or measured savings.
- Do not call zero observed conflict a guaranteed risk rate.
- Do not imply that the current test is still untouched.
