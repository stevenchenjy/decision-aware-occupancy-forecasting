# No-Raw-Data Upgrade Report

Report date: 2026-07-10

## Scope and outcome

All defensible upgrades supported by the committed saved validation/test predictions and processed load proxy were completed without downloading Dryad data or retraining a base model. The primary validation-selected hybrid remains scientifically defensible under the saved-output protocol. No test leakage was found in its weight or threshold selection.

## Upgrades completed

- Reproduced Seasonal-Transformer and three-way primary blend weights from validation probabilities.
- Reproduced the primary test Empty AUPRC and every fixed-policy count from saved exports.
- Added `results/hybrid_lineage.csv`, with one row per component, source probability columns, weights, selection inputs, objectives, fixed threshold, and evaluation outputs.
- Added `results/canonical_uncertainty_summary.csv`, a compact paired daily-block uncertainty table.
- Added `figures/canonical_policy_10pct_comparison.png`.
- Added absolute and percentage improvements to `figures/transformer_old_vs_new.png`.
- Marked the exploratory candidate as supplementary in the canonical metrics/policy figures.
- Made the test threshold sweep unmistakably diagnostic in `figures/risk_opportunity_validation_vs_test_diagnostic.png`.
- Expanded the same-day figure with actual-occupancy shading, safe/conflict recommendation shading, thresholds, a complete legend, and the `hvac_S + lig_S` load-proxy panel.
- Added exact canonical reproduction and no-test-selection regression tests.
- Added the professor guide and current consistency audit.
- Rechecked Markdown targets; no missing relative links were found.

## Validity judgment

The primary `Hybrid Seasonal-GBDT-Transformer` is a convex Empty-probability blend:

| Component | Weight | Contribution |
|---|---:|---|
| Historical Average | 0.15 | Train-only weekday/time-slot seasonal prior |
| LightGBM | 0.60 | Nonlinear tabular relationships |
| Original Transformer | 0.25 | Learned temporal sequence signal |

Weights were selected by maximum validation Empty AUPRC on a non-negative 0.05 simplex grid. The 10% operating threshold was selected separately on non-overlapping validation midnight horizons by maximum safe opportunity subject to validation conflict at or below 10%. No recalibration was applied. The models were not retrained after selection.

The exploratory balanced tree-deep candidate remains supplementary. Although its threshold is validation-selected, its architecture was retained because it was test-best, so its `0.8554` test AUPRC cannot be promoted as a headline selected result.

## Canonical results after regeneration

- Original Transformer: Empty AUPRC `0.7621`; 10% policy `97.4 kWh`, `3/31 = 9.68%` conflict.
- Seasonal-Transformer: Empty AUPRC `0.8490`; `457.9 kWh`, `0/249` observed conflicts.
- Primary hybrid: Empty AUPRC `0.8514`; threshold `0.875`; validation conflict `8.75%`; `490.1 kWh`, `0/259` observed conflicts, `14/14` safe windows.
- LightGBM reference: Empty AUPRC `0.8382`; `493.9 kWh`, `11/265 = 4.15%` conflict, `16/19` safe windows.
- Historical Average: Empty AUPRC `0.8497`; `94.6 kWh`, `0/66` observed conflicts.

The primary-minus-LightGBM safe-opportunity point difference is `-3.8 kWh` (`-0.76%`), and the paired daily-block 95% interval is `[-208.2, 174.6] kWh`. The primary-minus-Historical AUPRC difference is `+0.0042`, with interval `[-0.0304, 0.0377]`. These results support “nearly the same” and “slightly higher point estimate,” not decisive superiority.

## Checks run

```text
python3 scripts/generate_hybrid_artifacts.py
python3 scripts/generate_figures.py
python3 -m pytest -q
python3 scripts/check_environment.py
```

Results:

- 27 hybrid artifacts regenerated deterministically.
- 27 presentation/base figure files regenerated from saved results.
- 20 tests passed (wall time varies by machine).
- Canonical weights, AUPRC, threshold, safe opportunity, conflicts, intervals, and windows reproduced exactly within numeric tolerance.
- All prediction alignment checks pass, including reproduction of archived staged hybrid probabilities.
- Visual QA passed for the canonical metrics, fixed-policy, risk, stable-window, old/new, reliability, and same-day figures.
- No raw Dryad file was used.
- The environment check reports the expected local setup limitations: the active interpreter is Python 3.13 rather than the supported 3.10-3.12 range, and LightGBM cannot load because macOS `libomp` is absent. All local modules import, and this does not block saved-output regeneration.

## Checks not possible from saved outputs

- Hybrid-specific multiple-seed dispersion requires aligned per-seed validation/test component probabilities. Aggregate seed-averaged predictions cannot recover it.
- Hybrid rolling-origin validation requires Transformer predictions on the same saved rolling folds. Those predictions are absent.
- Full base-model retraining and raw feature-pipeline revalidation require the external Dryad package and a supported Python 3.10-3.12 environment.
- External-building/season validation requires new data.
- Counterfactual savings, comfort, and causal control claims require intervention or simulation evidence beyond recorded load coincidence.
- Formal calibrated/conformal risk guarantees require a predeclared validation-only procedure and more effective independent samples.

## Environment note

The saved-output analysis runs under the available Python 3.13 environment. The repository's full training environment targets Python 3.10-3.12; local LightGBM import may additionally require macOS `libomp`. These environment limits do not affect the regenerated saved-output hybrid tables, which do not import the training stack.

## Recommended presentation package

Use the paths and speaking notes in `reports/professor_presentation_guide.md`. The central artifacts are:

- `figures/transformer_old_vs_new.png`
- `figures/canonical_empty_metrics_comparison.png`
- `figures/canonical_policy_10pct_comparison.png`
- `figures/risk_opportunity_validation_vs_test_diagnostic.png`
- `figures/hybrid_stable_window_sensitivity.png`
- `figures/hybrid_lightgbm_historical_same_day.png`
- `results/canonical_model_comparison.csv`
- `results/canonical_policy_10pct.csv`
- `results/canonical_uncertainty_summary.csv`
