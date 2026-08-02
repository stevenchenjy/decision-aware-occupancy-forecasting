# Manuscript Integrity Audit

> **Superseded for final interpretation by [final_self_audit.md](final_self_audit.md).** Its prior causal/midnight wording is not retained: the final verdict is **requires empirical rerun**.

**Audit date:** 2026-07-29  
**Verdict:** PASS with explicit, non-removable limitations.

## Evidence, inference, and recommendation

| Layer | Approved content |
|---|---|
| Evidence | A validation-selected three-way probability blend has 0.8514 all-overlap Empty AUPRC; its fixed one-hour test policy produces 490.1 kWh of processed load-proxy opportunity and zero observed camera-label conflicts in 259 recommended intervals across 43 test days. |
| Inference | In this held-out period, the canonical hybrid supplies a transparent operating point with similar offline opportunity to LightGBM and fewer observed camera-label conflicts. Small model-level point differences are uncertain under the reported paired daily-block intervals. |
| Recommendation | Freeze the candidate and evaluate it prospectively on a later untouched period or new building, with equipment, comfort, and counterfactual control outcomes. |

## Protocol controls verified

- Chronological train, validation, and test partitions include 24.25-h gaps.
- The primary weights (0.15/0.60/0.25) are the validation AUPRC optimum on the declared 0.05 simplex grid.
- Policy thresholds are selected only on validation midnight horizons under a 10% conflict constraint.
- The test export is loaded only after canonical selection in the saved-output regeneration path.
- Future sensor values and controllable load streams are excluded from prediction inputs.
- HVAC and lighting are used only for retrospective opportunity accounting. Both kW streams are causally forward-filled where missing (8.03% missing before fill); the nominal accounting weights are 1.0/1.0 and the interval conversion is 0.25 h.
- Forecast metrics and policy metrics explicitly use different scopes: overlapping forecasts versus non-overlapping daily horizons.
- Main figures exclude the test-ranked balanced hybrid and retrospective expanded-search candidates.

## Mandatory language controls verified

- The manuscript says **offline safe load opportunity**, not verified savings.
- Zero conflict is always qualified as *observed* against the selected south-zone camera label in the held-out period and accompanied by count/sample caution.
- The manuscript does not equate camera-label-empty with physical absence or the processed meter-derived load proxy with a fully observed, controllable meter total.
- The discussion rejects comfort, carbon, controller-safety, deployment, and universal-generalization claims.
- Decision-aware and window-aware outputs are labeled exploratory/frozen future challengers in both the main text and Appendix~A.
- The manuscript does not call the work decision-focused learning.

## Residual limitations retained in the manuscript

1. One selected south-zone subset, one building, and 43 test policy days.
2. Raw timestamps are interpreted as UTC on a solar-pattern check; source documentation does not explicitly state the timezone.
3. Camera counts can miss occupants, so camera-label-empty does not establish physical absence.
4. Wi-Fi coverage is sparse before causal filling, while the two load-proxy streams are each 8.03% missing before fill; sensor-availability and imputation robustness are untested.
5. Raw data are not committed; saved-output reproduction does not independently verify raw retraining.
6. Hybrid-specific seed dispersion and full hybrid rolling-origin reconstruction are unavailable from saved outputs.
7. Bootstrap intervals are conditional on selected policy/model and cannot produce unseen conflicts from all-zero observed blocks.
8. Primary weight selection was reconstructed after a previous staged script hard-coded the same weights; this is not a preregistered blind test firewall.
9. No counterfactual energy, thermal comfort, equipment, tariff, or intervention outcome is available.
