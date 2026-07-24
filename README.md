# Decision-Aware Occupancy Forecasting Research Prototype

This repository evaluates day-ahead occupancy forecasts for identifying stable empty windows and estimating offline safe shiftable-load opportunity under occupancy-conflict constraints.

The strongest current conclusion concerns a validation-selected probability hybrid:

`seasonal schedule prior + LightGBM + Transformer -> validation-selected risk policy`

It is an offline evaluation framework, not a deployed controller or verified energy-savings study.

## Main result

The primary `Hybrid Seasonal-GBDT-Transformer` combines:

- 15% train-only Historical Average Empty probability
- 60% LightGBM Empty probability
- 25% original Transformer Empty probability

Those weights are the highest-validation-AUPRC point on a declared 0.05 simplex grid. The 10% policy threshold (`0.875`) is then selected on validation midnight forecasts by maximizing safe opportunity subject to validation occupancy conflict `<=10%`.

On 43 held-out test days:

- Empty AUPRC: `0.8514`
- test conflict rate: `0/259 = 0.00%` observed recommended intervals
- safe opportunity: `490.1 kWh`
- recommendation coverage: `6.27%`
- recommended/safe windows: `14/14`
- safe opportunity per day: `11.40 kWh/day`

The point AUPRC is slightly above Historical Average (`0.8497`) and LightGBM (`0.8382`), but paired daily-block confidence intervals for those differences include zero. The observed 0% conflict is specific to this test period and is not a universal safety guarantee.

## Exploratory decision-aware extensions

The canonical model above is unchanged. Two later validation-only searches ask a
different question: which already-saved probability blend and operating threshold
identify more safe load-proxy opportunity while retaining explicit forecasting and
occupancy-conflict safeguards?

- **Joint weight-threshold search:** evaluates all 231 non-negative
  Seasonal/LightGBM/Transformer weight vectors on the 0.05 simplex against 37
  thresholds, for 8,547 validation pairs. It maximizes validation safe opportunity
  subject to interval conflict `<=10%`, positive coverage, and at least one stable
  one-hour window. A 99%-of-best-validation-AUPRC variant limits forecast-quality
  loss.
- **Window-aware search:** applies predeclared AUPRC and fully-safe-window floors
  to the same frozen validation surface. Its primary future challenger is
  `0.40/0.40/0.20` at threshold `0.850`, selected under a fully safe window floor
  of 85% and an AUPRC floor of 99%.

The joint-search challengers produced larger safe-opportunity point estimates on
the already-inspected current test, but also about 3% interval conflict versus zero
observed conflict for the canonical primary. These candidates remain exploratory:
the current test results cannot be used to promote or retune them, and no new
untouched evaluation period is included in this repository.

Start with the [joint-search report](reports/decision_aware_joint_search_report.md),
the [window-aware report](reports/window_aware_decision_search_report.md), and the
[future untouched-evaluation protocol](reports/future_untouched_evaluation_protocol.md).

## Model roles

| Family | Role |
|---|---|
| Historical Average | Train-only weekday/time-slot schedule baseline; defines the seasonal prior |
| LightGBM | Nonlinear tabular reference and strongest established opportunity policy |
| Random Forest, original Transformer, DLinear | Original comparison models |
| Seasonal-Transformer Blend | Validation-selected two-way intermediate (`0.54/0.46`) |
| Hybrid Seasonal-GBDT-Transformer | Validation-selected primary hybrid (`0.15/0.60/0.25`) |
| Exploratory Hybrid Balanced Tree-Deep | Test-ranked supplementary candidate (`0.8554` test AUPRC); not a selected deployment policy |
| Decision-aware joint hybrids | Validation-selected exploratory challengers; not canonical |
| Window-aware hybrid | Frozen future-evaluation challenger (`0.40/0.40/0.20 @ 0.850`); current-test values are retrospective |

## Start here

1. [RESULTS_SUMMARY.md](RESULTS_SUMMARY.md) — canonical results, differences, and uncertainty.
2. [New artifact audit](reports/new_artifact_integration_audit.md) — provenance and experimental-validity audit.
3. [Integration report](reports/new_artifact_integration_report.md) — integration changes and presentation paths.
4. [Professor presentation guide](reports/professor_presentation_guide.md) — recommended main/appendix artifacts and speaking notes.
5. [Current consistency audit](reports/current_result_consistency_audit.md) — cross-file numerical and claim consistency checks.
6. [No-raw-data upgrade report](reports/no_raw_data_upgrade_report.md) — upgrades completed from saved outputs and remaining raw-data blockers.
7. [VALIDITY_CHECKLIST.md](VALIDITY_CHECKLIST.md) — leakage and selection checks.
8. [CLAIMS_AND_LIMITATIONS.md](CLAIMS_AND_LIMITATIONS.md) — supported wording and claim boundaries.
9. [REPRODUCING.md](REPRODUCING.md) — raw-data, saved-output, testing, and figure commands.
10. [Decision-aware joint-search report](reports/decision_aware_joint_search_report.md) — validation-only joint weight-threshold results.
11. [Window-aware search report](reports/window_aware_decision_search_report.md) — stable-window constraints and the frozen future challenger.

## Canonical outputs

- Eight-model metrics: `results/canonical_model_comparison.csv`
- Validation-selected 10% policies: `results/canonical_policy_10pct.csv`
- Hybrid weights and provenance: `results/hybrid_candidate_registry.csv`
- Primary-hybrid component lineage: `results/hybrid_lineage.csv`
- Validation weight searches: `results/hybrid_seasonal_transformer_weight_search.csv` and `results/hybrid_primary_weight_search.csv`
- Validation/test risk sweeps: `results/hybrid_risk_opportunity_threshold_sweeps.csv`
- Stable-window sensitivity: `results/hybrid_stable_window_sensitivity.csv`
- Daily-block uncertainty: `results/hybrid_uncertainty_daily_block_bootstrap.csv`
- Compact professor-facing uncertainty: `results/canonical_uncertainty_summary.csv`
- Calibration: `results/hybrid_calibration_summary.csv`
- Hybrid predictions: `predictions/hybrid_ensemble_validation_predictions.csv` and `predictions/hybrid_ensemble_test_predictions.csv`

Established base results remain in place; the hybrid integration does not silently replace them.

## Key figures

- `figures/canonical_empty_metrics_comparison.png`
- `figures/canonical_policy_10pct_comparison.png`
- `figures/risk_opportunity_validation_vs_test_diagnostic.png`
- `figures/hybrid_stable_window_sensitivity.png`
- `figures/hybrid_lightgbm_historical_same_day.png`
- `figures/transformer_old_vs_new.png`
- `figures/hybrid_reliability_analysis.png`

## Exploratory decision-aware figures

- `figures/decision_aware_joint_validation_frontier.png`
- `figures/decision_aware_joint_test_comparison.png`
- `figures/window_aware_validation_tradeoff.png`

## Repository layout

- `src/` — reusable data, model, evaluation, policy, and hybrid-analysis code.
- `scripts/run_all.py` — full raw-data training/evaluation path.
- `scripts/generate_figures.py` — regenerate base and hybrid figures from saved results.
- `scripts/generate_hybrid_artifacts.py` — regenerate hybrid weights, tables, uncertainty, predictions, and figures without retraining.
- `results/`, `figures/`, `predictions/` — canonical outputs.
- `reports/` — audit and integration reports.
- `archive/new_staging_2026-07/` — staged notebook/script/result provenance.
- `figures/archive/new_staging_2026-07/` — staged singular/plural figure trees.
- `NEW/README.md` — closed staging manifest.

## Quick reproduction from saved outputs

```bash
python -m pytest -q
python scripts/generate_hybrid_artifacts.py
python scripts/generate_figures.py
```

Full model retraining requires the external Dryad raw data described in `DATA.md`.

## Interpretation boundary

Safe opportunity is the recorded `hvac_S + lig_S` load during recommended intervals that were actually empty:

`kWh = max(hvac_S + lig_S, 0) * 0.25 hour`

This is not verified savings, comfort preservation, carbon reduction, causal impact, or production readiness.
