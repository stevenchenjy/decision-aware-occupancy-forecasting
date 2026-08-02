# Manuscript Figure Record

The final paper uses only the two figures regenerated into `../manuscript/figures/` by [`../scripts/generate_paper_figures.py`](../scripts/generate_paper_figures.py).

| Manuscript asset | Inputs | Role | Scope control |
|---|---|---|---|
| `fig_policy_comparison.png` | `results/canonical_policy_10pct.csv` | Three-model test policy comparison | Historical average, LightGBM, and validation-selected primary hybrid only; no test-ranked or retrospective candidates. |
| `fig_paired_uncertainty.png` | `results/canonical_uncertainty_summary.csv` | Paired daily-block uncertainty contrasts | 2,000 resamples; fixed model and policy selection; explicitly not selection-uncertainty intervals. |

The source charts below remain useful provenance artifacts but are intentionally excluded from the main paper:

- `figures/canonical_empty_metrics_comparison.png` has a truncated y-axis and includes a test-ranked supplementary hybrid.
- `figures/canonical_policy_10pct_comparison.png` is numerically correct but contains an exploratory candidate and is overly dense for the manuscript.
- `figures/example_forecast_*` and `results/test_forecast_probabilities_best_model.csv` are excluded because their legacy generator selected the display model from held-out test AUPRC; the purported false-positive case has zero camera-label conflicts.
- Decision-aware and window-aware figures remain appendix/provenance material only unless a later untouched evaluation is completed.
