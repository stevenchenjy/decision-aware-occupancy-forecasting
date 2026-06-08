# Results Archive

This folder preserves legacy or duplicate CSV outputs that are no longer the canonical files for review.

No scientific output was deleted. These files are kept for traceability only.

## Canonical Replacements

| Archived file | Use this canonical file instead | Reason |
|---|---|---|
| `model_metrics.csv` | `../model_metrics_empty_positive.csv` | Byte-identical alias; canonical name states Empty-positive semantics. |
| `model_level_empty_metrics.csv` | `../model_metrics_empty_positive.csv` | Byte-identical alias; canonical name states Empty-positive semantics. |
| `lightgbm_feature_importance.csv` | `../permutation_importance.csv` | Byte-identical alias; canonical name describes the method. |
| `risk_energy_pareto_frontier.csv` | `../energy_risk_pareto_frontier.csv` and `../energy_risk_tradeoff_threshold_sweep.csv` | Older naming/schema; canonical files use current energy-risk terminology. |
| `threshold_policy_results.csv` | `../threshold_policy_results_test.csv` | Older summary schema; canonical file contains the held-out test policy results. |
| `risk_constraint_summary.csv` | `../threshold_policy_results_test.csv` and `../selected_threshold_policies.csv` | Derived summary; canonical split separates validation selection from test evaluation. |
| `delivery_manifest.csv` | `../current_run_manifest.csv` | Older manifest generated before archive cleanup. |

## Canonical Review Tables

- Model metrics: `../model_metrics_empty_positive.csv`
- Validation-selected thresholds: `../selected_threshold_policies.csv`
- Test policy results: `../threshold_policy_results_test.csv`
- Energy-risk threshold sweep: `../energy_risk_tradeoff_threshold_sweep.csv`
- Pareto frontier: `../energy_risk_pareto_frontier.csv`
- Stable-window summary: `../stable_window_metrics.csv`
- Detailed continuous-window metrics: `../continuous_empty_window_policy_results_test.csv`
- Current manifest: `../current_run_manifest.csv`
