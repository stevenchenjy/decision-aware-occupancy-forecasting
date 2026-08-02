# Final Presentation Guide

> **Use this script, not historical presentation figures or guides.** The
> authoritative evidence boundary is [CLAIMS_AND_LIMITATIONS.md](../CLAIMS_AND_LIMITATIONS.md)
> and [final_self_audit_2026-08-01.md](final_self_audit_2026-08-01.md).

## One-sentence thesis

This is a single-building offline post-bin case study: a
validation-selected blend produced a held-out Empty-class AUPRC point estimate
of 0.8514 and 490.1 kWh of camera-label-empty processed load-proxy overlap,
but it does not verify real-time availability, controllability, energy savings,
or future safety.

## Required opening disclosures

- A 00:00 anchor is the left label of the completed [00:00, 00:15) input bin;
  the effective decision boundary is 00:15.
- The reported bounded values are uncalibrated Empty-class scores. Brier,
  log-loss, and ECE are diagnostics; no calibrator was fitted.
- The processed HVAC-plus-lighting kWh is an offline overlap proxy, not a
  counterfactual or measured savings result.
- The source is a cleaned release with unresolved raw-stream and
  upstream-imputation provenance.

## Canonical evidence sequence

1. **Protocol and baselines.** Explain chronological saved validation/test
   separation and the strong historical schedule baseline.
2. **Forecast result.** Show the paper model-comparison table: 0.8514 is a
   point estimate over 388,032 overlapping test rows from 4,042 anchors, not a
   daily policy estimate.
3. **Fixed policy result.** Show the paper policy table: threshold 0.875 was
   selected on validation; the later test contains 259/259/0 recommended,
   camera-label-empty, and occupied-conflict intervals, respectively, across
   14/14/0 windows.
4. **Uncertainty and stability.** State that the selected blend lies in a
   flat validation region and daily-block intervals are conditional on fixed
   selection.
5. **Limitations and next step.** State requires empirical rerun: provenance,
   seed-before-construction retraining, new validation selection, and one
   untouched evaluation period.

## How to discuss exploratory work

Decision-aware and window-aware searches were validation-selected saved-output
diagnostics. They are not headline results and cannot be promoted with the
already inspected current test period. After corrected retraining, they must be
re-selected on a new validation period.

## Do not say

Do not say safe, conflict-free, calibrated, controllable, energy savings,
deployment-ready, or superior without the exact empirical qualification above.
