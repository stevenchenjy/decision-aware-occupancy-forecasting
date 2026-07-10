# Validity Checklist

## Base pipeline

- [x] Raw timestamps are interpreted as UTC and converted to `America/Los_Angeles` before time features.
- [x] `occupied=1` is defined from the maximum selected south-zone occupancy count greater than zero.
- [x] Evaluation uses `Empty=1`.
- [x] Train, validation, and test splits are chronological.
- [x] Train-validation and validation-test gaps are 24.25 hours.
- [x] All models use a 96-step history and 96-step forecast horizon.
- [x] Historical Average uses training labels only.
- [x] Rolling features end before the forecast anchor (`arr[anchor-window:anchor]`).
- [x] Missing inputs use causal forward-fill plus fixed zero for leading gaps.
- [x] Future sensor values are excluded.
- [x] HVAC, lighting, MELS, and total electric load are excluded from model features.
- [x] Load is used only for offline opportunity accounting.
- [x] Base seeded models use seeds 42, 43, and 44.

## Hybrid integration

- [x] Validation/test combined prediction exports have unique `(anchor, target, horizon)` keys.
- [x] Every anchor has ordered horizon steps 1-96.
- [x] Repeated predictions for a target timestamp agree on the actual label.
- [x] Per-model test exports align with combined keys, labels, and probabilities.
- [x] Validation targets end before test targets begin.
- [x] Seasonal-Transformer alpha is selected on validation only.
- [x] Primary three-way weights are selected on validation only using a declared 0.05 simplex grid.
- [x] Test predictions are loaded by the integration routine only after weights are fixed.
- [x] Hybrids blend Empty probabilities; no features, logits, labels, or decisions are mixed.
- [x] Hybrid weights sum to one and are non-negative.
- [x] No hybrid is retrained on validation or test.
- [x] No post-hoc calibration is fit on test.
- [x] Probability thresholds are selected on validation midnight horizons only.
- [x] Opportunity selection maximizes validation safe kWh subject to validation conflict constraints.
- [x] Fixed thresholds are evaluated on 43 held-out test midnight horizons.
- [x] Full test threshold sweeps are labeled diagnostic and are not selection inputs.
- [x] The test-ranked balanced candidate is labeled exploratory/supplementary.
- [x] Test prediction timestamps align to processed HVAC+lighting load timestamps.

Machine-readable evidence: `results/hybrid_input_alignment_audit.csv`, `results/hybrid_candidate_registry.csv`, and `results/hybrid_primary_weight_search.csv`.

## Uncertainty and robustness

- [x] 2,000 paired daily-block bootstrap resamples are reported for the primary, LightGBM, Historical Average, and their differences.
- [x] Calibration diagnostics include Brier, log loss, 10-bin ECE, and a reliability curve.
- [x] Stable-window sensitivity covers 0.25, 0.5, 1, 2, and 4 hours.
- [ ] Hybrid-specific seed dispersion: blocked by missing aligned per-seed component predictions.
- [ ] Hybrid rolling-origin validation: blocked by missing Transformer predictions for saved rolling folds.
- [ ] External/cross-building validation: not available.
- [ ] Counterfactual savings and thermal-comfort validation: not available.

## Interpretation checks

- [x] Zero observed conflict is described with sample size and finite-sample caution.
- [x] Small AUPRC differences are not described as decisive.
- [x] Opportunity is not described as verified savings.
- [x] No causal, comfort, carbon, deployment, or universal-generalization claim is made.

See `reports/new_artifact_integration_audit.md` for the full provenance and 11/11 statistical-fallacy scan.
