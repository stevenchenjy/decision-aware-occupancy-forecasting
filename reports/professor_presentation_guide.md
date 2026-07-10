# Professor Presentation Guide

## Recommended thesis

Strong recurring occupancy schedules explain why the train-only Historical Average is competitive. A validation-selected probability hybrid combines that seasonal prior with LightGBM's nonlinear tabular signal and the original Transformer's temporal-sequence signal. In this 43-day held-out period, its model-level Empty AUPRC point estimate is slightly above the schedule baseline, while its validation-selected 10% policy identifies nearly the same safe shiftable-load opportunity as LightGBM with zero observed conflicts among 259 recommended intervals. The AUPRC differences are uncertain, and zero observed conflict is not a universal guarantee.

## Main presentation sequence

### 1. Research question and protocol

Use the protocol description in `README.md` and `SIMULATION_SUMMARY.md`.

Say aloud:

- Empty is the positive class.
- Every model uses the same chronological validation/test exports and 24-hour horizon.
- Hybrid weights and operating thresholds are selected on validation before test is loaded.
- Recorded `hvac_S + lig_S` is an offline opportunity proxy, not measured savings.

### 2. Original Transformer to primary hybrid

Figure: `figures/transformer_old_vs_new.png`

Claim supported: seasonal blending raises Transformer test Empty AUPRC from `0.7621` to `0.8490`; the validation-selected three-way hybrid reaches `0.8514`. Under the fixed 10% policy, safe opportunity rises from `97.4` to `490.1 kWh`.

Limitation to state: these relative improvements use a weak original-Transformer policy as the denominator; they do not establish superiority over Historical Average or LightGBM.

### 3. Canonical model comparison

Figure: `figures/canonical_empty_metrics_comparison.png`

Table: `results/canonical_model_comparison.csv`

Claim supported: the primary hybrid has the highest validation-selected model-family AUPRC point estimate (`0.8514`), narrowly above Historical Average (`0.8497`) and LightGBM (`0.8382`).

Limitation to state: the paired daily-block AUPRC intervals for primary-minus-Historical and primary-minus-LightGBM include zero. The hatched `0.8554` exploratory candidate is supplementary because its architecture was highlighted after test ranking.

### 4. Fixed 10% policy comparison

Figure: `figures/canonical_policy_10pct_comparison.png`

Table: `results/canonical_policy_10pct.csv`

Claim supported: at validation-selected thresholds, the primary hybrid identifies `490.1 kWh` with `0/259` observed interval conflicts and `14/14` safe windows; LightGBM identifies `493.9 kWh` with `11/265` conflicts and `16/19` safe windows.

Limitation to state: the primary-minus-LightGBM opportunity difference is only `-3.8 kWh`, and its paired bootstrap interval includes zero. Zero conflict is a finite test-period observation.

### 5. Selection versus diagnosis

Figure: `figures/risk_opportunity_validation_vs_test_diagnostic.png`

Table: `results/hybrid_risk_opportunity_threshold_sweeps.csv`

Claim supported: thresholds are chosen on the blue validation surface under the 10% constraint; the red-tinted test surface is diagnostic only.

Limitation to state: do not select a model, weight, or threshold from the test panel. The stars on the test panel are evaluations of validation-selected thresholds.

### 6. Stable-window sensitivity

Figure: `figures/hybrid_stable_window_sensitivity.png`

Table: `results/hybrid_stable_window_sensitivity.csv`

Claim supported: the primary hybrid has zero observed interval conflict across the tested minimum durations of 0.25, 0.5, 1, 2, and 4 hours; safe opportunity declines from `497.0` to `407.8 kWh` as the duration requirement tightens.

Limitation to state: thresholds remain those selected for the one-hour rule; this is sensitivity analysis, not a separately optimized policy for every duration.

### 7. Explanatory held-out day

Figure: `figures/hybrid_lightgbm_historical_same_day.png`

Table: `results/hybrid_lightgbm_historical_same_day.csv`

Claim supported: the figure illustrates how fixed thresholds translate probability forecasts into safe/conflict-marked recommendations for the primary hybrid, LightGBM, and Historical Average on the same test day.

Limitation to state: the day was selected after evaluation for visual informativeness. It is explanatory, not evidence of typical-day performance; the load trace is a recorded proxy, not a savings measurement.

## Appendix

- Compact uncertainty: `results/canonical_uncertainty_summary.csv`
- Full bootstrap output: `results/hybrid_uncertainty_daily_block_bootstrap.csv`
- Reliability analysis: `figures/hybrid_reliability_analysis.png` and `results/hybrid_calibration_summary.csv`
- Exact component lineage: `results/hybrid_lineage.csv`
- Input alignment checks: `results/hybrid_input_alignment_audit.csv`
- Zero-conflict bounds: `results/primary_hybrid_zero_conflict_bound.csv`
- Full provenance audit: `reports/new_artifact_integration_audit.md`

## Avoid in the headline

- Do not call the exploratory balanced hybrid the best selected model.
- Do not describe `0.8514` versus `0.8497` as decisive.
- Do not call `490.1 kWh` realized savings.
- Do not call zero observed conflict a guaranteed risk rate.
- Do not use the diagnostic test sweep to justify the operating threshold.
