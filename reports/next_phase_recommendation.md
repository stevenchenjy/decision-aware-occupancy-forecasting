# Next Phase Recommendation

> **Required next phase: empirical rerun before any untouched-candidate
> evaluation.** The workspace verdict is **requires empirical rerun** for
> prospective claims.

## Exact next action

Acquire provenance-tagged source streams and construct a new locked experiment:
source timestamps and observation-end availability, data hashes, package lock,
seed-before-model-construction, and a later untouched test period must all be
specified before training.

## Decision rule

The current saved-output canonical, decision-aware, and window-aware results
are historical diagnostics. Do not carry their weights, thresholds, AUPRC
floors, or window floors into a corrected retraining study as frozen
candidates. Select new candidates on the new validation period only, document
selection stability, then evaluate the newly frozen set once on the untouched
period.

## Minimum empirical deliverables

- source-data and environment manifests with checksums;
- timing/availability and missing-data provenance audit;
- aligned per-seed prediction exports for training, validation, and test;
- validation-only model, blend, threshold, and window selection record;
- untouched evaluation with all-overlap metrics, post-bin policy metrics,
  empirical conflict counts, window counts, and conditional daily-block
  uncertainty;
- a report that calls kWh a processed load-proxy overlap rather than energy
  savings.

## Explicitly prohibited

- treating the legacy cleaned-release replay as a new empirical result;
- using the current saved test period to select or promote a model;
- promoting any historical decision-aware/window-aware candidate after
  corrected retraining;
- claiming verified savings, controllability, real-time deployment, calibrated
  probability, or probabilistic safety without new supporting evidence.
