# Current Result Consistency Audit

> **Historical audit superseded for final wording by [final_self_audit_2026-08-01.md](final_self_audit_2026-08-01.md).** Numerical reconciliation remains useful; post-bin timing/source-provenance limits are authoritative in the final audit.

Audit date: 2026-07-10

## Outcome

The current canonical tables, summaries, figures, and prediction lineage agree on the headline results. No unresolved numerical or claim inconsistency was found. The integration preserves two deliberately different AUPRC scopes: the all-overlap model-comparison value (`0.8514`) and the non-overlapping daily-horizon bootstrap point (`0.8522`). They are labeled separately and should not be interchanged.

## Canonical authority order

1. Saved validation/test prediction exports and processed load proxy.
2. `src/hybrid_analysis.py` plus `scripts/generate_hybrid_artifacts.py`.
3. `results/canonical_model_comparison.csv`, `results/canonical_policy_10pct.csv`, and `results/canonical_uncertainty_summary.csv`.
4. Narrative summaries and presentation figures generated from those tables.

## Checked headline values

| Quantity | Canonical value | Consistency result |
|---|---:|---|
| Original Transformer Empty AUPRC | 0.76209635 | Consistently rounded to 0.7621 |
| Seasonal-Transformer Empty AUPRC | 0.84898413 | Consistently rounded to 0.8490 |
| Primary hybrid Empty AUPRC | 0.85136961 | Consistently rounded to 0.8514 |
| Exploratory balanced Empty AUPRC | 0.85537677 | Consistently labeled test-ranked/supplementary |
| Primary 10% threshold | 0.875 | Validation-selected everywhere |
| Primary validation conflict | 8.745% | Consistently rounded to 8.75% |
| Primary test conflict | 0/259 = 0% | Always accompanied by finite-sample caution |
| Primary safe opportunity | 490.1464 kWh | Consistently rounded to 490.1 kWh |
| LightGBM test conflict | 11/265 = 4.1509% | Consistently rounded to 4.15% |
| LightGBM safe opportunity | 493.9232 kWh | Consistently rounded to 493.9 kWh |
| Original Transformer test conflict | 3/31 = 9.6774% | Consistently rounded to 9.68% |
| Original Transformer safe opportunity | 97.4392 kWh | Consistently rounded to 97.4 kWh |

## Resolved discrepancies

### Transformer 0.7621 versus 0.7633

The canonical aggregate test Empty AUPRC is `0.7620963459460512`, reproduced over all 388,032 saved rolling forecast rows. No aggregate result supports `0.7633`. Values around `0.7633` are individual prediction values; the Transformer 6-12 hour bucket is `0.76214603`, and Historical Average Empty F1 is `0.762095`. These are plausible sources of transcription or metric-label confusion. The canonical Transformer result remains `0.7621`.

### Headline AUPRC versus bootstrap point

`results/canonical_model_comparison.csv` evaluates all overlapping test predictions and reports primary AUPRC `0.85136961`. Daily-block uncertainty uses 43 non-overlapping midnight-anchored forecasts and therefore has point estimate `0.852212`. This is a scope difference, not drift.

### Opportunity floating-point precision

Older float32 policy tables contain differences around `1e-6 kWh` (for example, LightGBM `493.9231567` versus canonical `493.9231552`). These round identically and arise from numeric precision. The canonical hybrid generator recomputes with aligned float64 arrays.

## Selection and lineage checks

- Primary weights are `Historical Average=0.15`, `LightGBM=0.60`, and `Original Transformer=0.25`; they are non-negative and sum to one.
- The chosen simplex point maximizes validation Empty AUPRC on the declared 0.05 grid.
- The 0.875 threshold maximizes validation safe opportunity among primary-hybrid points with validation conflict at or below 10%.
- The generator fixes weights and thresholds before loading the test export.
- Test sweeps are labeled diagnostic and are absent from selection function interfaces.
- Machine-readable evidence is in `results/hybrid_lineage.csv` and `results/hybrid_input_alignment_audit.csv`.

## Documentation and link checks

The following documents use the same model roles and thesis: `README.md`, `RESULTS_SUMMARY.md`, `SIMULATION_SUMMARY.md`, `CLAIMS_AND_LIMITATIONS.md`, `FUTURE_WORK.md`, `REPRODUCING.md`, `VALIDITY_CHECKLIST.md`, and `DATA.md`. A local Markdown link scan found zero missing relative targets.

Established pre-hybrid figures remain for provenance, but `reports/professor_presentation_guide.md` identifies the canonical professor-facing package. The old LightGBM/Historical presentation figures are not recommended as headline artifacts.

## Verification performed

```text
python3 scripts/generate_hybrid_artifacts.py
python3 scripts/generate_figures.py
python3 -m pytest -q
```

Result: 27 hybrid artifacts and 27 figure files regenerated; 20 tests passed. Figures were visually inspected after regeneration. `scripts/check_environment.py` separately reports the expected unsupported local Python 3.13 and missing macOS `libomp`; all local modules import, and saved-output regeneration is unaffected.
