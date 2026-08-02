# Final Self-Audit: Code, Results, and Manuscript Consistency

**Audit date:** 2026-08-01  
**Scope:** repository source, committed processed/prediction exports, canonical and exploratory result artifacts, root documentation, IEEE manuscript, figures, tests, and bibliography.  
**Final verdict:** **requires empirical rerun**

## Executive conclusion

The committed saved-output evidence is internally reproducible after the corrections recorded below. It supports an offline, post-bin analysis in which the stored left-labelled anchor bin is available only after it closes. It does not support a real-time midnight-issued policy or prospective operating claim. The manuscript, root documentation, metadata artifacts, and canonical scripts now use the same evidence boundary.

The primary numerical result did not change: the nominal validation-selected blend has all-overlap Empty AUPRC 0.8513696056; the fixed policy has 259 recommended, 259 subsequently camera-label-empty, and 0 camera-label-conflict intervals in 14/14 windows, coinciding with 490.1463795 kWh of processed load proxy. These values remain offline overlap calculations, not energy savings.

## Findings and disposition

| ID | Severity | Finding and evidence | Disposition |
|---|---|---|---|
| T1 | High | Pandas 15-min records are left-closed/left-labelled. The anchor row used by tabular and sequence inputs summarizes '[t,t+15 min)', while historical wording claimed a recommendation at t. Processed data demonstrate multi-observation bins. | Explicit resampling convention, timestamp-offset validation, 'forecast_time_semantics.csv', and post-bin manuscript wording added. A real-time claim still requires empirical rerun. |
| T2 | High | Input source is 'Bldg59_clean data'; source-side interpolation/imputation provenance and original observation-end timestamps are unavailable. Local forward fill cannot undo it. | Paper and docs state clean-release/provenance limit. Requires provenance-tagged empirical source rerun. |
| M1 | High | Legacy 'DLinear' is a single 96-to-96 occupancy-history linear mapping, not decomposition-based DLinear. | Paper-facing label changed to direct linear occupancy baseline; legacy key retained for artifact traceability. No numeric rerun required for the rename. |
| M2 | High | Legacy 'Original Transformer' is compact encoder-only with calendar projection, not a full original encoder-decoder Transformer. | Paper-facing label changed to compact Transformer encoder; citation scope narrowed. No numeric rerun required. |
| M3 | High | Deep modules are constructed before seed reset. Nominal seeds 42/43/44 do not control initialization. | Historical code is annotated and manuscript discloses the defect. Correcting behavior requires full retraining and regeneration; not performed without verified source data. |
| H1 | Medium | LightGBM previously advertised 0.85 row subsampling, but installed LightGBM has no row bagging when 'subsample_freq=0'. | Code explicitly records 'subsample=1.0', 'subsample_freq=0', and column fraction 0.85, preserving observed behavior. Test added. |
| S1 | Medium | The primary full-overlap weight winner exceeds rank 2 by 0.000032 AUPRC; eight candidates are within 0.0005. Validation perturbations alter winner/threshold choices. | Validation-only stability script/result/table added. No test-informed replacement selection was made. |
| P1 | Medium | Stratified tree training and weighted deep loss, with no calibrator, do not justify calibrated-probability/risk language. | Paper/docs now call outputs uncalibrated Empty-class scores; Brier/log loss/ECE are diagnostics only. |
| D1 | Medium | Wi-Fi is 81.57% missing before unbounded row-order fill. HVAC and lighting are each 8.03% missing before proxy filling. | Prominent manuscript limitation and corrected feature metadata. Staleness/capped-fill sensitivity requires empirical rerun. |
| O1 | Medium | Opportunity is a processed HVAC-plus-lighting overlap with recommendations and later camera-empty labels, not a counterfactual intervention. | Equations, captions, documents, and figures retain offline load-proxy language; no savings or controller claim remains. |
| X1 | Medium | Earlier exploratory routines read test diagnostics before completing their audit narrative, risking an ambiguous workflow. | Code reordered so validation candidates are frozen before test reads; fresh saved-output reports regenerated. Results remain exploratory due historical test exposure. |
| R1 | Low | Abstract/root documents mixed 388,032 overlapping forecast rows with 43 policy horizons. | All main claims split forecast and policy scopes; claim matrix added. |
| B1 | Low | Model citation metadata/linkage were sound, but DLinear/Transformer citation context over-implied implementations. | Citation context corrected; 24/24 references verified. |

## Checks that passed

- Canonical blend/threshold selection in the saved-output path is validation-before-test.
- Prediction exports have consistent 96-step target offsets and chronological split separation.
- Empty is the positive class; policy conflict denominator is recommended intervals; stable windows require four contiguous score-thresholded intervals.
- Proxy formula is 'max(hvac_S + lig_S, 0) × 0.25 h' and recomputes to canonical policy totals.
- Canonical figures consume only canonical saved CSVs; main paper excludes test-ranked/exploratory candidates.
- Decision-aware and window-aware candidate selection now precedes their test diagnostics; they remain status-controlled exploratory work.
- Citation linkage: 24 cited keys, 24 bibliography entries, 0 unresolved, 0 orphaned.

## Non-removable limitations

1. Original raw streams, observation-end timestamps, source timezone confirmation, checksums, and source-side imputation lineage are absent.
2. The left-labelled completed-bin anchor invalidates an unqualified 00:00 real-time issue claim.
3. Correct deep initialization requires retraining all deep models and every dependent output.
4. One building, selected zones, 39 validation policy horizons, and 43 historical test policy horizons limit generalization.
5. Camera labels do not prove physical absence; source sensor staleness and proxy missingness lack sensitivity analysis.
6. Fixed-selection bootstrap intervals exclude selection uncertainty and cannot create unseen conflicts from all-zero observed conflict blocks.
7. No calibrated score model, counterfactual controller, thermal simulation, comfort result, or field intervention exists.
8. Environment is not locked and raw base-model retraining was not executed in this audit.

## Final release condition

The manuscript may be read as a carefully bounded offline post-bin case study, but it must not be submitted or represented as a prospective operational method until the empirical rerun protocol in the rerun manifest is completed. The immediate next step is to obtain provenance-tagged source streams and execute the locked empirical rerun without reusing the current test set for selection.

Supporting files:

- 'code_paper_consistency_log.md'
- 'rerun_manifest.md'
- 'result_difference_report.md'
- 'reference_audit_final.md'
- 'final_claim_matrix.md'
