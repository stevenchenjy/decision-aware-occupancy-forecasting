# Validity Checklist

**Overall verdict: requires empirical rerun.** Checkmarks below distinguish saved-output integrity from unresolved prospective validity.

## Saved-output integrity

- [x] Canonical prediction exports have aligned anchor, horizon-step, target-time, label, and score keys.
- [x] Target-time offset is asserted as 'target_time = anchor_time + horizon_step × 15 min'.
- [x] Canonical blend weights and policy thresholds are selected on validation exports before canonical test scores are read.
- [x] Policy accounting uses non-overlapping horizons; safe opportunity matches the processed HVAC-plus-lighting proxy formula.
- [x] Core saved-output numbers reproduce: AUPRC 0.8513696056, threshold 0.875, 259/259/0 intervals, 14/14 windows, 490.1463795 kWh.
- [x] LightGBM behavior explicitly records no row bagging ('subsample=1', 'subsample_freq=0') and 0.85 column sampling.
- [x] Exploratory joint/window routines now freeze validation candidates before test diagnostics are loaded.
- [x] Decision-aware and window-aware point estimates remain labelled exploratory, not canonical.

## Prospective / empirical gaps

- [ ] The 00:00 left label is a verified decision timestamp. **No:** it represents [00:00,00:15) and is treated as available at 00:15.
- [ ] Source-side causal availability is verified. **No:** inputs begin from a cleaned release with unresolved imputation lineage and timestamp semantics.
- [ ] Raw-stream end-to-end retraining is reproducible. **No:** original streams are not committed.
- [ ] Deep seed initialization is controlled. **No:** construction precedes seed reset in the historical implementation.
- [ ] Score calibration supports a probability/risk claim. **No:** no calibrator is fitted; Brier/log loss/ECE are diagnostics only.
- [ ] Wi-Fi stale-value sensitivity is quantified. **No:** pre-fill missingness is 81.57% and no staleness cap is applied.
- [ ] Selection robustness is established. **No:** validation perturbations show nearby blend/threshold choices change.
- [ ] Independent prospective evaluation is complete. **No:** only historical saved test horizons exist.
- [ ] Energy, comfort, or controller effects are evaluated. **No.**

## Evidence

- 'results/forecast_time_semantics.csv'
- 'results/validation_selection_stability.csv'
- 'results/hybrid_primary_weight_search.csv'
- 'results/canonical_policy_10pct.csv'
- 'reports/final_self_audit_2026-08-01.md'
- 'paper/audits/final_claim_matrix.md'
