# Window-aware decision search audit

## Material Passport

- Origin Skill: experiment-agent
- Origin Mode: validate/run
- Verification Status: ANALYZED
- Version Label: window_aware_audit_v1

## Audit conclusion

**PASS.** Existing definitions and the three reported current-test window outcomes reproduce exactly.

The audit uses saved predictions and processed load outputs only. It does not retrain a base model or require the Dryad raw directory.

## Exact current definitions

- **Recommended interval:** a 15-minute interval whose uncalibrated Empty score is at or above the fixed threshold and belongs to a contiguous above-threshold run of at least four intervals. Shorter runs are not recommended.
- **Camera-label-empty interval:** a recommended interval with subsequently observed `actual_empty_positive=1`.
- **Conflict interval:** a recommended interval with observed `actual_empty_positive=0` (occupied).
- **Stable recommended window:** one maximal contiguous run of recommended intervals within a midnight-labelled completed-input-bin 96-step horizon; its effective availability boundary is 00:15 for a 00:00 label. Windows do not join across horizon/day boundaries.
- **All-camera-label-empty window:** a stable recommended window for which every interval is subsequently observed Empty.
- **Conflict window:** a stable recommended window containing **any** occupied interval. One occupied 15-minute interval is sufficient.
- **Interval conflict rate:** `conflict intervals / recommended intervals`; defined as zero when there are no recommendations, although candidate eligibility separately requires positive coverage and at least one window.
- **Window precision:** `all-camera-label-empty windows / recommended windows`.
- **All-camera-label-empty window rate:** the same binary-window quantity as window precision; legacy output columns retain `fully_safe` names for compatibility.
- **Offline label-empty load-proxy overlap (kWh):** `(hvac_S + lig_S) * 0.25 h`, clipped at zero by the existing mapping, summed only for recommended intervals subsequently observed Empty. This is a processed load-proxy overlap, not verified savings or controllable energy.
- **Recommendation coverage:** `recommended intervals / all intervals` across the non-overlapping midnight policy horizons.

The implementation in `src/hybrid_analysis.py` confirms that `window_summary` increments `conflict_windows` whenever `actual_empty[day, start:end].all()` is false. Therefore any occupied interval makes the whole recommended window conflicting.

## Reproduction of reported current outcomes

| Frozen strategy | Recommended windows | All-camera-label-empty windows | Conflict windows | Status |
|---|---:|---:|---:|---|
| Canonical forecast-optimal | 14 | 14 | 0 | pass |
| Exploratory decision-optimal | 21 | 17 | 4 | pass |
| Exploratory 99% AUPRC-floor | 18 | 14 | 4 | pass |

The decision-optimal and 99%-floor candidates each have four conflict windows even though their interval conflict rates are near 3%, because occupied intervals are distributed across four distinct recommended windows and the window metric is binary.

## Saved-input sufficiency

- Unique validation weight-threshold pairs: 8547 (231 weight vectors × 37 thresholds).
- Validation policy horizons: 39 non-overlapping midnight horizons.
- Best validation Empty AUPRC: 0.7286379575.
- The validation grid includes interval counts, offline label-empty load-proxy overlap, coverage, and window counts. Validation predictions and the processed load table support per-window severity reconstruction.
- The current test export supports a retrospective diagnostic only. It is not a fresh untouched evaluation and is not accepted by the validation selection function.

## Inconsistencies or blockers

- None.
