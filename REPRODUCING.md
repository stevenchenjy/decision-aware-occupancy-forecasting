# Reproducing the Audited Artifacts

## Two distinct paths

1. **Saved-output regeneration (verified here):** reads committed processed/prediction CSVs and reproduces downstream analysis.
2. **Empirical retraining (not verified here):** requires source streams with timestamp/imputation provenance, corrected initialization, and a locked environment.

Do not describe the first path as a full raw-data rerun.

## Current environment

The audit ran with the workspace Python 3.13.2 and imported NumPy 1.26.4, pandas 2.3.3, scikit-learn 1.9.0, PyTorch 2.12.0, LightGBM 4.6.0, Matplotlib 3.10.9, and seaborn 0.13.2. The historical environment checker targets Python 3.10--3.12 and is not a lockfile. Record an exact lockfile/container before an empirical retraining.

## Saved-output regeneration

From the repository root:

    python3 -m pytest -q
    python3 scripts/generate_hybrid_artifacts.py
    python3 scripts/audit_validation_selection_stability.py
    python3 scripts/run_decision_aware_joint_search.py
    python3 scripts/run_window_aware_decision_search.py
    python3 paper/scripts/generate_paper_figures.py

The canonical generator validates prediction alignment, repeats the validation-only primary blend/threshold selection, and writes canonical result, uncertainty, calibration-diagnostic, figure, and time-semantics artifacts. The stability script intentionally reads validation and processed exports only; it does not select a replacement model. The two expanded searches are saved-output exploratory diagnostics.

## Key inputs and outputs

Inputs:

- 'results/forecast_predictions_validation_all_models.csv'
- 'results/forecast_predictions_test_all_models.csv'
- 'results/processed_lbnl_15min_pacific.csv'

Important outputs:

- 'results/forecast_time_semantics.csv'
- 'results/canonical_model_comparison.csv'
- 'results/canonical_policy_10pct.csv'
- 'results/canonical_uncertainty_summary.csv'
- 'results/validation_selection_stability.csv'
- 'paper/audits/rerun_manifest.md'

Expected canonical values are AUPRC 0.8513696056, threshold 0.875, opportunity 490.1463795 kWh, 259/259/0 recommended/safe/conflict intervals, and 14/14 windows. These values are post-bin saved-output calculations, not prospective controls.

## Quarantined legacy cleaned-release replay

The external folder historically expected by the pipeline contains 'Bldg59_clean data', a cleaned release rather than original raw acquisition streams. It may be placed under:

    doi_10_7941_D1N33Q__v20220202/Building_59/Bldg59_clean data/

The command below is deliberately a **legacy replay only**. It requires an explicit acknowledgement, writes outside the canonical saved-output directories, and must not be cited as a new empirical/prospective result:

    python3 scripts/run_all.py --legacy-cleaned-replay

## Empirical rerun requirements

Do not use `scripts/run_all.py` for this path. Build a new protocol-locked empirical runner only after:

1. obtain original/provenance-tagged streams and observation-end timestamps;
2. declare and test the bin closure, label, and availability convention;
3. correct deep seed setting before model construction;
4. pin packages and record data hashes;
5. quarantine a later untouched test period;
6. retrain, select only on training/validation, and evaluate exactly once.

Without these steps, saved-output regeneration and a legacy cleaned-release replay cannot establish a prospective operational claim.
