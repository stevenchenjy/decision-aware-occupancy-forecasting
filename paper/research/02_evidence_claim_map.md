# Claim-to-Evidence Map

Only claims with an identified source may enter the paper draft. Citation
support and empirical evidence are separate requirements.

| Candidate claim | Empirical source | Status / manuscript wording |
|---|---|---|
| The task is 24-hour-ahead, 15-minute occupancy forecasting for Building 59 selected south zones. | `DATA.md`, `results/data_summary.csv`, `RESULTS_SUMMARY.md` | Supported. State as dataset-specific. |
| Features exclude future sensor values and controllable electrical loads. | `VALIDITY_CHECKLIST.md`, `results/feature_availability_policy.csv`, pipeline code | Supported. Explain leakage policy in Methods. |
| The primary blend and threshold were selected on validation before test evaluation. | `results/hybrid_lineage.csv`, `results/hybrid_primary_weight_search.csv`, tests | Supported. Show selection flow. |
| The canonical hybrid reached test Empty AUPRC 0.8514. | `results/canonical_model_comparison.csv` | Supported. Separate from daily-block AUPRC scope. |
| The fixed 10% policy produced 490.1 kWh offline opportunity and 0/259 observed conflicts. | `results/canonical_policy_10pct.csv` | Supported only with “offline,” denominator, and finite-sample qualification. |
| The hybrid is better than all baselines. | Pairwise uncertainty table | **Not supported.** Use point estimates and intervals; do not call decisive superiority. |
| Recommendations save 490.1 kWh. | No intervention/counterfactual evidence | **Not supported.** It is realized-load opportunity coinciding with actual emptiness. |
| The approach is safe for deployment. | 43 days, no controls/comfort proof | **Not supported.** Zero observed conflicts is not a guarantee. |
| Decision-aware/window-aware challengers are superior. | Already-inspected test diagnostics | **Exploratory only.** Keep in appendix/future-work unless new test evidence is acquired. |

## Evidence hierarchy for the manuscript

1. **Canonical numerical authority:** saved prediction exports and processed load
   proxy.
2. **Derived canonical tables:** `results/canonical_model_comparison.csv`,
   `results/canonical_policy_10pct.csv`, and
   `results/canonical_uncertainty_summary.csv`.
3. **Methods authority:** `src/hybrid_analysis.py`, `src/lbnl_pipeline.py`, and
   the associated tests.
4. **Narrative authority:** this map, `CLAIMS_AND_LIMITATIONS.md`, and the
   prepared manuscript only after it matches the rows above.
