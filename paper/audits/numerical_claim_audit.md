# Numerical Claim Audit

> **Superseded for final scope wording by [final_claim_matrix.md](final_claim_matrix.md) and [final_self_audit.md](final_self_audit.md).** The numerical values remain useful; earlier causal/midnight and test-count statements are not final.

**Audit date:** 2026-07-29  
**Verdict:** PASS, conditional on the stated evaluation scopes.

## Authority hierarchy

| Claim family | Authoritative source | Scope that must remain attached |
|---|---|---|
| Dataset and splits | `results/data_summary.csv`, `results/split_summary.csv`, `results/data_split_summary.csv` | One selected Building~59 south-zone subset. |
| Forecast metrics | `results/canonical_model_comparison.csv` | 388,032 overlapping test forecast rows. |
| Policy outcomes | `results/canonical_policy_10pct.csv` | 43 non-overlapping midnight-anchored test horizons; 4,128 intervals. |
| Weight and threshold provenance | `results/hybrid_primary_weight_search.csv`, `results/hybrid_selected_threshold_policies.csv`, `results/hybrid_lineage.csv` | Validation only. |
| Uncertainty | `results/canonical_uncertainty_summary.csv` | 2,000 paired daily-block resamples; fixed selection. |
| Calibration and sensitivity | `results/hybrid_calibration_summary.csv`, `results/hybrid_stable_window_sensitivity.csv` | Diagnostic/fixed-threshold only. |
| Noncanonical candidates | `results/decision_aware_joint_*`, `results/window_aware_*` | Appendix/status only. |

The legacy `results/block_bootstrap_confidence_intervals.csv` and `results/robustness_summary.csv` were excluded: they contain older 200-replicate bootstrap summaries rather than canonical point estimates or current paired 2,000-replicate intervals.

## Main manuscript claim map

| Manuscript location | Claim | Saved value | Source | Status |
|---|---|---:|---|---|
| Methods; Table I | Data rows / forecast horizon / split gap | 26,413 rows; 96 history + 96 target steps; 24.25 h gaps | `data_summary.csv`, `config.json`, `split_summary.csv` | Pass |
| Methods; Table II | Seed aggregation and fixed model settings | Seeds 42/43/44; 200,000 tabular rows/seed; 12 deep epochs; patience 4 | `config.json`, `model_training_control.csv`, `model_run_metadata.csv` | Pass |
| Methods | Policy threshold grid and constraint | 37 values, 0.050--0.950 by 0.025; $C_{\mathrm{val}}\leq0.10$ | `config.json`, `threshold_grid_metadata.csv`, `hybrid_selected_threshold_policies.csv` | Pass |
| Methods; Table I | Load-proxy conversion and missingness | 1.0/1.0 accounting weights; 0.25 h; 8.0339% missing per HVAC/lighting stream before fill | `controllable_load_assumptions.csv`, `controllable_load_inventory.csv`, `feature_coverage.csv` | Pass |
| Abstract; Table II | Primary all-overlap Empty AUPRC | 0.8514 | `canonical_model_comparison.csv` | Pass |
| Abstract; Table II | Historical / LightGBM AUPRC | 0.8497 / 0.8382 | `canonical_model_comparison.csv` | Pass |
| Abstract; Table III; Fig. 1 | Primary threshold / validation conflict | 0.875 / 8.75% | `hybrid_lineage.csv`, `canonical_policy_10pct.csv` | Pass |
| Abstract; Table III; Fig. 1 | Primary test opportunity / interval conflict | 490.1 kWh / 0 of 259 | `canonical_policy_10pct.csv` | Pass |
| Abstract; Table III; Fig. 1 | Primary safe windows | 14 of 14 | `canonical_policy_10pct.csv` | Pass |
| Abstract; Table III; Fig. 1 | LightGBM opportunity / interval conflict | 493.9 kWh / 11 of 265 (4.15%) | `canonical_policy_10pct.csv` | Pass |
| Table IV; Fig. 2 | Primary daily AUPRC | 0.8522 [0.7918, 0.9016] | `canonical_uncertainty_summary.csv` | Pass |
| Table IV; Fig. 2 | Primary minus LightGBM AUPRC | +0.0163 [-0.0050, +0.0426] | `canonical_uncertainty_summary.csv` | Pass |
| Table IV; Fig. 2 | Primary minus historical AUPRC | +0.0042 [-0.0304, +0.0377] | `canonical_uncertainty_summary.csv` | Pass |
| Table IV; Fig. 2 | Opportunity contrasts | -3.8 [-208.2, +174.6] and +395.5 [+127.0, +786.2] kWh | `canonical_uncertainty_summary.csv` | Pass |
| Results | Primary calibration diagnostics | Brier 0.0928; log loss 0.2984; ECE 0.0253 | `hybrid_calibration_summary.csv` | Pass |
| Results | Fixed-threshold 1/2/4-h sensitivity | 490.1 / 490.1 / 407.8 kWh; 14 / 14 / 11 safe windows | `hybrid_stable_window_sensitivity.csv` | Pass |
| Results | Finite-sample zero-event cautions | 1.15% intervals; 19.3% windows under independence | `primary_hybrid_zero_conflict_bound.csv` | Pass, explicitly conditional |
| Appendix A | Joint/window diagnostic figures | 8,547 joint pairs; 623.5/650.4 kWh; 511.6 kWh at 2.49% | `decision_aware_joint_*`, `window_aware_*` | Status-controlled exploratory only |

## Recalculation and test evidence

An independent read-only numerical audit recomputed canonical model metrics, policy outcomes, blend weights, thresholds, calibration values, stable-window counts, and zero-event bounds from the committed prediction and processed-load exports. Values matched the canonical artifacts to floating-point precision. The repository regression suite also passed with **36 tests**.

## Required interpretation controls

1. `0.8514` is an all-overlap test AUPRC; `0.8522` is a daily-block point estimate. They must never be substituted for one another.
2. `490.1 kWh` is a processed, meter-derived HVAC-plus-lighting proxy coinciding with recommendation and realized camera-derived Empty labels. It uses nominal 1.0/1.0 HVAC/lighting accounting weights, a kW-to-kWh factor of 0.25 h, and causal forward fill; each input stream is 8.03% missing before that fill. It is not energy savings, controllable capacity, a fully observed meter total, or a load-shift outcome.
3. Bootstrap intervals condition on selected weights and thresholds and do not include model-selection uncertainty.
4. Zero observed conflicts are not a future safety guarantee or proof of physical absence. All observed primary blocks are conflict free only against the selected south-zone camera label, so a nonparametric bootstrap cannot synthesize unseen conflicts or undetected occupants.
5. Decision-aware and window-aware diagnostics cannot replace the canonical primary without a new untouched test period.
