# Publication-Readiness Audit

> **Superseded workspace note.** The authoritative final status is
> **requires empirical rerun** for prospective claims; see
> [final_self_audit.md](../audits/final_self_audit.md). The historical record
> below predates the completed post-bin, provenance, calibration, and
> seed-initialization audit and must not be used as current paper wording.

## Historical record

**Audit date:** 2026-07-29  
**Scope:** repository artifacts, source code, reported outputs, documentation,
and reproducibility checks. This is an audit of the current evidence, not a new
experiment.

## Verdict

**Conditionally ready for a narrowly framed IEEE-style paper.** The repository
has a coherent offline experiment, validation-before-test selection, explicit
claim boundaries, saved prediction inputs, and passing regression tests. Its
evidence supports a transparent single-building case study; it does not support
deployment, causal-energy, comfort, universal-safety, or cross-building claims.

## Evidence already present

| Area | Status | Evidence |
|---|---|---|
| Research problem | Present | Next-24-h (96-step) occupancy forecasting for stable empty-window recommendations at 15-minute resolution. |
| Data provenance | Present, externally reproducible | Public LBNL Building 59 Dryad dataset, DOI `10.7941/D1N33Q`; raw data are not committed. |
| Temporal protocol | Strong | Chronological train/validation/test split, 24.25-hour gaps, validation-only blend/threshold selection. |
| Baselines | Strong | Historical Average, LightGBM, Random Forest, Transformer, and DLinear are evaluated under a shared target and split. |
| Decision evaluation | Strong for offline evidence | Stable windows require four consecutive intervals; opportunity and conflict are measured on non-overlapping midnight horizons. |
| Uncertainty | Partial but useful | 2,000 paired daily-block bootstrap summaries exist for the canonical hybrid and key baselines. |
| Leakage controls | Strongly documented | Future-label/sensor/load exclusion and alignment checks are recorded in `VALIDITY_CHECKLIST.md` and result audits. |
| Reproduction from saved outputs | Strong | Saved prediction exports and deterministic hybrid generation are documented. |
| Regression tests | Passed locally | `python3 -m pytest -q -p no:cacheprovider` completed with **36 passed** on 2026-07-29. |

## Defensible headline evidence

For the canonical validation-selected Seasonal--LightGBM--Transformer blend
(0.15/0.60/0.25), the held-out period contains 43 non-overlapping policy
horizons. Reported values are Empty AUPRC 0.8514, 490.1 kWh *offline safe
shiftable-load opportunity*, and 0 observed conflicts among 259 recommended
intervals. The model-level AUPRC and safe-opportunity differences versus the
Historical Average and LightGBM baselines have uncertainty intervals that include
zero where documented. This is evidence of a carefully evaluated operating point,
not decisive model superiority.

Canonical sources: `RESULTS_SUMMARY.md`,
`results/canonical_model_comparison.csv`,
`results/canonical_policy_10pct.csv`, and
`results/hybrid_uncertainty_daily_block_bootstrap.csv`.

## Required claim boundaries

The manuscript must not claim:

- verified energy savings, emissions reduction, thermal comfort, or causal
  intervention effects;
- a deployed building controller, operational safety guarantee, or production
  readiness;
- statistically decisive superiority of the canonical hybrid over Historical
  Average or LightGBM;
- generalization beyond the observed Building 59 period;
- confirmation or promotion of the post-hoc exploratory joint/window-aware
  challengers.

Use “offline safe shiftable-load opportunity” and “zero observed conflicts in the
held-out period,” with the relevant denominator, instead of “energy savings” and
“safe.”

## What makes this publishable now

The methodological contribution must be framed as the **evaluation protocol**:
prediction models are compared using both forecasting metrics and a
validation-selected, risk-constrained stable-window decision metric. The paper
should make the strong schedule baseline, uncertainty, and evidence limitations
part of the result rather than hide them.

## What would materially strengthen a submission

1. Lock and evaluate the already-frozen challenger once on a genuinely new
   chronological period, following `reports/future_untouched_evaluation_protocol.md`.
2. Regenerate and save per-seed component predictions for the hybrid.
3. Run matched rolling-origin evaluation that includes the Transformer and all
   hybrid components.
4. Add at least one additional building/season, ideally using the public source
   data and an unchanged protocol.
5. Add a calibration/conformal risk-control study on validation data only.
6. If operational claims are desired, add counterfactual simulation or a real
   intervention with comfort constraints; do not infer it from realized load.
7. Audit sensor freshness and run feature-group ablations. In particular, both
   WiFi features are missing before fill for 81.57% of rows
   (`results/feature_coverage.csv`); causal forward-fill avoids future leakage
   but may leave operationally stale input values.

## Isolated legacy-artifact issue

Do **not** use the old generic example-day artifacts as inferential evidence.
The legacy full pipeline sorts `model_metrics_df` by held-out test AUPRC and
sets `best_model` from the first row (`src/lbnl_pipeline.py`, lines 1319--1321
and 1480--1485). That test-selected display choice is then used to generate
`results/test_forecast_probabilities_best_model.csv` and example-day figures.
In the current artifact, `results/example_case_days.csv` labels 2019-01-13 as a
`false_positive_recommendation_day` despite `conflict_count=0`.

This defect does not alter the canonical hybrid's validation-only selection,
canonical tables, or their tests. It does make the legacy
`example_forecast_*`/`test_forecast_probabilities_best_model.csv` family
unsuitable for a manuscript until it is regenerated with a pre-specified model
and case-selection rule and corrected labels.
