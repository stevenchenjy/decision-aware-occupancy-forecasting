# NEW Artifact Integration Report

## Material Passport

- Origin Skill: academic-research-suite / experiment-agent
- Origin Mode: validate and reproduce
- Origin Date: 2026-07-10
- Verification Status: VERIFIED for saved-output integration and regeneration; full base-model retraining not run
- Version Label: new_artifact_integration_report_v1

## Outcome

The valid July hybrid work is integrated into the canonical repository. The primary `Hybrid Seasonal-GBDT-Transformer` is supported as a validation-selected probability ensemble after replacing the staged hard-coded weight assertion with an explicit validation-only 0.05 simplex search. The test-best balanced hybrid remains supplementary.

The original base results were not overwritten. New hybrid tables, predictions, uncertainty summaries, and figures have distinct canonical names. Staged notebooks/scripts/results are archived with a complete SHA-256 manifest; `NEW/` now contains only a closed-staging README.

## Validity judgment

### Primary hybrid: suitable for the main result

- Probability weights: Historical Average 0.15, LightGBM 0.60, original Transformer 0.25.
- Selection: highest validation Empty AUPRC on a 0.05 convex simplex grid.
- Blend level: Empty probability.
- Threshold: 0.875, selected on validation midnight horizons for the 10% conflict policy.
- Test use: fixed-weight, fixed-threshold evaluation.
- Retraining after selection: none.
- Post-hoc calibration: none.

### Balanced hybrid: supplementary only

The balanced candidate reports test Empty AUPRC `0.8554`, but its architecture was part of an undocumented staged shortlist and it was highlighted because it was best on test. Its threshold is validation-selected, but the model itself is test-ranked. It is not promoted to the headline.

## Canonical new results

### Model level

| Model | Empty AUPRC | Status |
|---|---:|---|
| Original Transformer | 0.7621 | original |
| Seasonal-Transformer Blend | 0.8490 | validation-selected intermediate |
| Historical Average | 0.8497 | schedule baseline |
| Hybrid Seasonal-GBDT-Transformer | 0.8514 | validation-selected primary |
| Exploratory Hybrid Balanced Tree-Deep | 0.8554 | test-ranked supplementary |

### Primary 10% policy

- Validation conflict: 8.75%.
- Test conflict: 0/259 = 0.00% observed.
- Safe opportunity: 490.1 kWh.
- Recommendation coverage: 6.27%.
- Recommended/safe/conflict intervals: 259/259/0.
- Recommended/safe/conflict windows: 14/14/0.
- Average recommended window duration: 4.63 hours.
- Opportunity per day: 11.40 kWh/day.
- Test period: 43 non-overlapping daily schedules.

### Differences

- Versus original Transformer: AUPRC +0.0893 (+11.71%); safe opportunity +392.7 kWh (+403.03%); conflict -9.68 percentage points.
- Versus Historical Average: AUPRC +0.0017 (+0.20%); safe opportunity +395.5 kWh (+418.00%); both have 0% observed test conflict.
- Versus LightGBM: AUPRC +0.0132 (+1.58%); safe opportunity -3.8 kWh (-0.76%); conflict -4.15 percentage points; coverage -0.15 percentage points.

Paired daily-block AUPRC intervals for primary-minus-LightGBM `[-0.0050, 0.0426]` and primary-minus-Historical `[-0.0304, 0.0377]` include zero. The small AUPRC point differences are not decisive.

## Discrepancies resolved

1. `0.7621` versus `0.7633`: the exact canonical Transformer test Empty AUPRC is `0.7620963459460512`. No aggregate artifact supports `0.7633`; near-`0.7633` values are individual probabilities. Transformer 6-12 hour AUPRC is `0.76214603`, also rounding to `0.7621`.
2. Hard-coded primary weights: the staged script did not search them. The integrated validation-only simplex search selects the same `0.15/0.60/0.25` point and reproduces `0.85136961`.
3. Singular/plural predictions: `NEW/result` and `NEW/results` exports are numerically equivalent; maximum serialization difference is `4.44e-16`.
4. Test-best model: `0.8554` is retained as exploratory rather than selected.
5. Zero conflict: reported with 259 intervals, 14 windows, 43 days, and finite-sample caution.
6. Figures: staged `figure/` and `figures/` were consolidated under a provenance archive; active figures live only in root `figures/`.

## Robustness and uncertainty

Completed from saved data:

- 2,000 paired daily-block bootstrap resamples (seed 42).
- Primary model and paired AUPRC/safe-opportunity differences.
- Calibration/reliability diagnostics (Brier, log loss, 10-bin ECE).
- Stable-window sensitivity from 0.25 to 4 hours.
- Exact prediction-key, label, probability, and load alignment checks.

Unavailable without retraining/new exports:

- Hybrid-specific seed dispersion: base components average seeds 42/43/44, but aligned per-seed probabilities were not saved.
- Hybrid rolling-origin validation: saved folds omit Transformer predictions.
- Full raw-data reproduction: the external Dryad directory is absent.

The primary's conflict bootstrap interval is degenerate at zero because no observed test block contains a conflict. A descriptive one-sided independent-trial upper bound is 1.15% for 259 intervals and 19.3% for 14 windows; independence is not established.

## Files integrated

### Created

- `src/hybrid_analysis.py`
- `scripts/generate_hybrid_artifacts.py`
- `tests/test_hybrid_analysis.py`
- `results/canonical_model_comparison.csv`
- `results/canonical_policy_10pct.csv`
- `results/hybrid_candidate_registry.csv`
- `results/hybrid_lineage.csv`
- `results/hybrid_seasonal_transformer_weight_search.csv`
- `results/hybrid_primary_weight_search.csv`
- `results/hybrid_selected_threshold_policies.csv`
- `results/hybrid_policy_results_test.csv`
- `results/hybrid_risk_opportunity_threshold_sweeps.csv`
- `results/hybrid_stable_window_sensitivity.csv`
- `results/hybrid_uncertainty_daily_block_bootstrap.csv`
- `results/canonical_uncertainty_summary.csv`
- `results/hybrid_calibration_summary.csv`
- `results/hybrid_reliability_curve_points.csv`
- `results/hybrid_input_alignment_audit.csv`
- `results/hybrid_robustness_scope.csv`
- `results/primary_hybrid_zero_conflict_bound.csv`
- `results/hybrid_lightgbm_historical_same_day.csv`
- `predictions/hybrid_ensemble_validation_predictions.csv`
- `predictions/hybrid_ensemble_test_predictions.csv`
- seven active hybrid figures listed below
- `reports/new_artifact_integration_audit.md`
- this report

### Updated

- `README.md`
- `RESULTS_SUMMARY.md`
- `SIMULATION_SUMMARY.md`
- `CLAIMS_AND_LIMITATIONS.md`
- `FUTURE_WORK.md`
- `REPRODUCING.md`
- `VALIDITY_CHECKLIST.md`
- `DATA.md`
- `LBNL_occupancy_forecasting_main.ipynb`
- `scripts/run_all.py`
- `scripts/generate_figures.py`
- `scripts/check_environment.py`
- `tests/test_imports.py`
- `results/current_run_manifest.csv` (intentional regeneration inventory update only)

### Archived or consolidated

- Original notebooks, staged hybrid script/report/tables, exact staged hybrid prediction export, documentation pins, and presentation aliases: `archive/new_staging_2026-07/`.
- Full original staging file manifest with hashes and dispositions: `archive/new_staging_2026-07/new_file_manifest.csv`.
- Original singular/plural staged figure trees: `figures/archive/new_staging_2026-07/`.
- `NEW/` replaced by `NEW/README.md` pointing to canonical/archive destinations.

Byte-identical and numerically equivalent duplicate CSVs plus runtime debris were removed from active staging after manifesting. Established scientific result tables retained their original hashes; only the generated `current_run_manifest.csv` changed to reflect new artifacts. Unrelated established figures remain byte-stable; four canonical presentation figures were intentionally revised and one fixed-policy figure was added.

## Commands and verification

| Command/check | Result |
|---|---|
| `python3 -m pytest -q` | 20 passed |
| `python3 scripts/generate_hybrid_artifacts.py --bootstrap-reps 2000` | 24 artifacts regenerated |
| `python3 scripts/generate_figures.py` | 26 figures regenerated |
| `python3 scripts/generate_presentation_figures.py` | completed; earlier LightGBM/Historical presentation outputs regenerated |
| Notebook JSON validation | pass |
| Canonical required-path check | all required paths present |
| Original result hash check | all established scientific tables unchanged; generated manifest intentionally changed |
| Original figure hash check | unrelated figures byte-stable; four canonical figures intentionally updated and one added |
| `python3 scripts/check_environment.py` | expected local-environment failure: Python 3.13 unsupported for declared reproduction and LightGBM lacks `libomp`; all local modules, including hybrid analysis, import |
| Full `scripts/run_all.py` | not run; external raw Dryad directory is missing and local LightGBM runtime lacks `libomp` |

## Revised thesis

Strong recurring occupancy schedules explain the performance of Historical Average. A validation-selected probability hybrid combines that schedule prior with nonlinear tabular and temporal-sequence forecasts. In this held-out period its AUPRC point estimate is slightly higher than the schedule baseline, and its 10% policy identifies nearly the same safe opportunity as LightGBM with zero observed conflicts. The small model-level differences are uncertain, and zero observed conflict is not a universal guarantee.

## Recommended professor-presentation artifacts

Use these active paths:

1. `figures/transformer_old_vs_new.png` — concise original-to-seasonal-to-primary story.
2. `figures/canonical_empty_metrics_comparison.png` — eight-model AUPRC/precision/recall/F1 comparison.
3. `figures/canonical_policy_10pct_comparison.png` — fixed validation-selected 10% policy comparison.
4. `figures/risk_opportunity_validation_vs_test_diagnostic.png` — validation/test sweeps, Pareto frontiers, and fixed operating points.
5. `figures/hybrid_stable_window_sensitivity.png` — conflict and opportunity across minimum durations.
6. `figures/hybrid_lightgbm_historical_same_day.png` — explanatory same held-out day for primary hybrid, LightGBM, and Historical Average.
7. `figures/hybrid_reliability_analysis.png` — calibration diagnostic.
8. `results/canonical_model_comparison.csv` — presentation metric source table.
9. `results/canonical_policy_10pct.csv` — presentation policy source table.
10. `results/canonical_uncertainty_summary.csv` — compact uncertainty source table.

Do not use archived `risk_energy_pareto_frontier_clean.png` or the test-ranked balanced model as a deployable headline.
