# Building 59 Occupancy Forecasting: Offline Post-Bin Case Study

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

    python3 -m pytest -q
    python3 scripts/generate_hybrid_artifacts.py
    python3 scripts/audit_validation_selection_stability.py
    python3 scripts/run_decision_aware_joint_search.py
    python3 scripts/run_window_aware_decision_search.py
    python3 paper/scripts/generate_paper_figures.py

These commands regenerate saved-output artifacts; they do **not** retrain base models from empirical source streams. See [REPRODUCING.md](REPRODUCING.md) and the [rerun manifest](paper/audits/rerun_manifest.md).

## Evidence layout

- 'results/' and 'predictions/' — canonical saved forecasts, policy accounting, timing semantics, and validation-stability artifact.
- 'src/' and 'scripts/' — preprocessing, models, canonical analysis, and reproducibility checks.
- 'paper/' — IEEE manuscript, manuscript figures, audits, and submission handoff.
- 'reports/final_self_audit_2026-08-01.md' — final code/results/paper consistency audit.
- 'reports/' — historical reports and current exploratory-search reports; use the final self-audit to interpret historical claims.

## Required empirical next step

Acquire source streams with observation-end timestamps and imputation lineage; define and test the bin-end issue convention; correct deep seed initialization before model construction; lock the environment; retrain and select only on training/validation; then evaluate once on a later untouched period or independent building. A simulator or intervention with equipment and comfort constraints is additionally required for energy or control claims.
