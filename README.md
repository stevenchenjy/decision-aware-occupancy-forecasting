# Building 59 Occupancy Forecasting: Offline Post-Bin Case Study

## What this project studies

A building-occupancy forecast becomes useful only when it can support a decision. This research repository asks when model outputs identify sustained empty intervals, how often those recommendations conflict with occupancy labels, and how much processed building load coincides with them.

The case study uses the cleaned LBNL Building 59 dataset and compares historical-average, tree-based, neural, and blended forecasts. Its main result is an **offline analysis of saved predictions**, with explicit boundaries between forecast quality, recommendation errors, and a load-opportunity proxy. It is a research case study requiring an empirical rerun, not a deployed building controller or a demonstration of energy savings.

If you are visiting from my [personal website](https://stevenchenjy.github.io/), start here and with [What the saved artifacts support](#what-the-saved-artifacts-support). For the methodology, read the [paper workspace](paper/README.md); for technical reproduction, use [REPRODUCING.md](REPRODUCING.md).

## The analysis in plain language

1. Compare model outputs against the building's recorded empty/occupied labels.
2. Select a model blend and score threshold using validation data.
3. Apply a fixed rule to find consecutive recommended empty intervals in the saved test predictions.
4. Count label conflicts and the processed HVAC/lighting load associated with the intervals.

The inputs use completed 15-minute bins. An anchor labeled `00:00` contains the interval `[00:00, 00:15)` and is treated as available at `00:15`. That timing matters: this saved-output analysis does not demonstrate that the same information would have been available to an operational forecast issued earlier.

## Current scientific status

**Audit verdict: requires empirical rerun.** The committed saved outputs are internally reproducible as an offline, post-bin analysis. They do not establish a real-time day-ahead system or a prospective operational recommendation.

Each stored 15-min anchor label 't' is the left label of the completed input bin '[t, t+15 min)'. Because the models use that anchor record, the effective availability boundary is 't+15 min'; a policy anchor labelled '00:00' is therefore treated as available at '00:15', with target bins through the next '00:15' exclusive. The imported input is the cleaned LBNL release, not the original acquisition stream. Upstream imputation lineage and source timestamp semantics are unavailable, so row-order checks after import do not prove causal source availability.

The authoritative self-audit is [reports/final_self_audit_2026-08-01.md](reports/final_self_audit_2026-08-01.md). It supersedes earlier positive-integration wording where they conflict.

## What the saved artifacts support

- Across **388,032 overlapping test forecast rows from 4,042 anchors**, the nominal validation-selected primary blend has Empty AUPRC **0.8514**; Historical Average has **0.8497** and LightGBM **0.8382**.
- Across **43 non-overlapping midnight-labelled test policy horizons** (effective boundary 00:15), its fixed score rule recommends **259** intervals; all are subsequently camera-label-empty, forming **14** label-safe windows and coinciding with **490.1 kWh** of processed HVAC-plus-lighting proxy.
- LightGBM coincides with **493.9 kWh** but has **11/265 (4.15%)** camera-label conflicts.
- The offline opportunity is not measured saving, controllable capacity, comfort preservation, physical absence, or controller performance.
- The stored outputs are bounded Empty-class scores, not calibrated probabilities. Brier, log loss, and ECE are diagnostics only.
- The reported blend and threshold are nominal validation selections, not uniquely stable optima. See 'results/validation_selection_stability.csv'.

## Model terminology

| Saved identifier | Paper-facing description |
|---|---|
| 'Original Transformer' | Compact encoder-only Transformer with a known-future calendar projection |
| 'DLinear' | Direct linear occupancy-history baseline; not the decomposition-based DLinear architecture |
| 'Hybrid Seasonal-GBDT-Transformer' | Nominal validation-selected primary score blend: Historical 0.15 / LightGBM 0.60 / Transformer 0.25 |

The deep-model runs carry labels 42, 43, and 44, but model construction preceded seed reset. Their ensemble is factual saved-output evidence, not a controlled seed-dispersion study.

## Reproduce the auditable saved-output path

Use a virtual environment and install the repository's requirements first. Python 3.11 is the saved-output CI target; the requirements recommend Python 3.10–3.12. The recorded audit environment and the distinction between supported reproduction paths are documented in [REPRODUCING.md](REPRODUCING.md).

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

Run the following from the repository root. These commands write regenerated analysis and figure artifacts to the working copy:

    python3 -m pytest -q
    python3 scripts/generate_hybrid_artifacts.py
    python3 scripts/audit_validation_selection_stability.py
    python3 scripts/run_decision_aware_joint_search.py
    python3 scripts/run_window_aware_decision_search.py
    python3 paper/scripts/generate_paper_figures.py

These commands regenerate saved-output artifacts; they do **not** retrain base models from empirical source streams. See [REPRODUCING.md](REPRODUCING.md) and the [rerun manifest](paper/audits/rerun_manifest.md).

The external cleaned dataset is not needed for this saved-output path; the required derived inputs are already committed. For dataset provenance and the separate legacy replay, see [DATA.md](DATA.md). `scripts/run_all.py` requires the explicit `--legacy-cleaned-replay` flag and writes to an isolated directory; it is not an empirical rerun entry point.

## Evidence layout

- 'results/' and 'predictions/' — canonical saved forecasts, policy accounting, timing semantics, and validation-stability artifact.
- 'src/' and 'scripts/' — preprocessing, models, canonical analysis, and reproducibility checks.
- 'paper/' — IEEE manuscript, manuscript figures, audits, and submission handoff.
- 'reports/final_self_audit_2026-08-01.md' — final code/results/paper consistency audit.
- 'reports/' — historical reports and current exploratory-search reports; use the final self-audit to interpret historical claims.

## Required empirical next step

Acquire source streams with observation-end timestamps and imputation lineage; define and test the bin-end issue convention; correct deep seed initialization before model construction; lock the environment; retrain and select only on training/validation; then evaluate once on a later untouched period or independent building. A simulator or intervention with equipment and comfort constraints is additionally required for energy or control claims.
