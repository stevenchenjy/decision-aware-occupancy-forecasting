# Rerun Manifest and Reproducibility Boundary

## Commands executed in this audit

All commands were run from the repository root using the workspace Python 3.13.2 unless noted.

| Command | Purpose | Result |
|---|---|---|
| 'python3 scripts/generate_hybrid_artifacts.py' | Regenerate canonical saved-output hybrid artifacts, uncertainty, figures, and timing semantics. | Completed; canonical values unchanged. |
| 'python3 scripts/audit_validation_selection_stability.py' | New validation-only blend/threshold perturbation diagnostic; no test export read. | Completed; wrote 'results/validation_selection_stability.csv'. |
| 'python3 scripts/run_decision_aware_joint_search.py' | Regenerate exploratory joint-search reports after selection/test ordering repair. | Completed; 8 artifacts written. |
| 'python3 scripts/run_window_aware_decision_search.py' | Regenerate exploratory window-aware reports after ordering repair. | Completed; 10 artifacts written. |
| 'python3 paper/scripts/generate_paper_figures.py' | Regenerate manuscript-only figures from canonical CSVs. | Completed. |
| 'python3 -m pytest -q' | Full repository regression suite after substantive changes. | Recorded in final compilation/integrity audit. |
| Tectonic build and PDF render | Compile and inspect revised IEEE manuscript. | Recorded in final compilation audit. |

## What these commands do not do

They do not download original streams, establish source timestamp or imputation provenance, retrain base models, correct deep initialization, or produce a fresh untouched prospective test period. They are deterministic/saved-output regeneration steps, not an empirical rerun.

## Mandatory empirical rerun protocol

1. Obtain original or provenance-tagged source streams, including observation-end timestamps, source timezone confirmation, checksum/version identifiers, and per-value imputation lineage.
2. Declare the source interval convention. Persist separate fields for observation end, bin label, effective issue time, target interval start, and target interval end.
3. Implement and test the convention uniformly for occupancy, sensors, weather, and meters. Do not rely on default resampling semantics.
4. Move seed initialization before construction of every stochastic deep module. Preserve CPU/GPU determinism settings and record hardware/software versions.
5. Create an immutable environment lockfile/container and data manifest with hashes. Archive trained-model and per-seed prediction artifacts.
6. Define a chronological training/validation/test protocol before fitting. Keep the current historical test exports out of all new selection and tuning.
7. Retrain all base models. Recreate validation predictions, select blend/threshold only on validation, and save the full selection surface.
8. Evaluate the fixed candidate once on a later untouched period or independent building. Report both all-overlap forecast metrics and non-overlapping policy metrics with the post-bin issue boundary.
9. Run missingness/staleness and load-proxy sensitivity analyses. If probability/risk claims are desired, fit calibration/conformal methods on validation only.
10. For energy/control claims, add a counterfactual simulator or field intervention with equipment, tariff, indoor-condition, comfort, and occupant constraints.

## Required outputs before upgrading the verdict

- Raw/provenance data manifest and reproducible environment lock.
- Updated prediction exports and model/seed lineage.
- Recomputed canonical tables, figures, stability analysis, and uncertainty analysis.
- Fresh untouched-policy evaluation.
- A new integrity audit showing the revised code, results, manuscript, and citations agree.
