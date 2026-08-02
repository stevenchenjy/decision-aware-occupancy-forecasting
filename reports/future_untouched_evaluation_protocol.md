# Historical frozen-candidate registry and empirical-rerun handoff

> **Final-audit status:** the 8 frozen candidates in this saved-output search are historical exploratory diagnostics only. They cannot be promoted, carried into corrected retraining, or applied as the next empirical evaluation.

## Why the old future protocol is superseded

The final audit requires provenance-tagged source streams, explicit observation-end and post-bin issue timestamps, seed initialization before deep-model construction, a locked environment, full model retraining, and fresh validation-only selection. Those changes alter the score-generating experiment. Reusing historic saved-output weights or thresholds after them would be a new unvalidated choice, not a frozen confirmation.

## Required corrected protocol

1. Obtain and hash provenance-tagged streams; preserve source timezone, observation-end, bin-start, bin-end, effective issue, target-start, and target-end fields.
2. Retrain every model under seed-before-construction and a locked software/hardware environment.
3. Select model family, blend weights, score threshold, and any window rule only on a newly declared chronological validation period.
4. Freeze that newly selected policy without inspecting the later evaluation period.
5. Evaluate it once on a later untouched period or independent building, reporting post-bin forecast and policy scopes separately.
6. Treat camera-label-empty processed-load-proxy overlap as offline accounting only; energy, comfort, controllability, calibrated-risk, and deployment claims require additional evidence.

See paper/audits/rerun_manifest.md for the authoritative empirical-rerun checklist. The current test and the existing decision-aware/window-aware diagnostics remain retrospective and may not be used to retune or promote a candidate.
