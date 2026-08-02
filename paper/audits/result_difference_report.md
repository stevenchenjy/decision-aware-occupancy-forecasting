# Result-Difference Report

**Comparison:** pre-audit canonical saved outputs versus regenerated saved-output artifacts after semantic/configuration/documentation repair.  
**Result:** no canonical numerical claim was changed.

| Artifact / claim | Pre-audit value | Regenerated value | Difference | Interpretation |
|---|---:|---:|---:|---|
| Primary weights | 0.15 / 0.60 / 0.25 | 0.15 / 0.60 / 0.25 | 0 | Same validation selection |
| Primary all-overlap Empty AUPRC | 0.8513696056 | 0.8513696056 | 0 | Same saved prediction export |
| Primary Brier / log loss | 0.0927784165 / 0.2984396028 | 0.0927784165 / 0.2984396028 | 0 | Diagnostic values unchanged |
| Primary threshold | 0.875 | 0.875 | 0 | Same validation policy choice |
| Validation conflict | 0.08745247 | 0.08745247 | 0 | Same saved policy accounting |
| Primary opportunity | 490.1463795 kWh | 490.1463795 kWh | 0 | Same processed proxy input |
| Primary intervals | 259 / 259 / 0 | 259 / 259 / 0 | 0 | Recommended / camera-label-safe / conflict |
| Primary windows | 14 / 14 / 0 | 14 / 14 / 0 | 0 | Recommended / camera-label-safe / conflict |
| LightGBM opportunity / conflict | 493.9231552 kWh / 11 of 265 | 493.9231552 kWh / 11 of 265 | 0 | Same saved policy accounting |

## Changes that do affect interpretation, not numbers

- The prior verbal “midnight-issued” claim is replaced with completed-bin/post-bin semantics: 00:00 label, effective 00:15 boundary.
- The data source is now called a cleaned release rather than raw data; source-side imputation remains unresolved.
- 'DLinear' and 'Original Transformer' are paper-facing relabels, retaining legacy identifiers only where required to match CSVs.
- “Probability” and “risk-constrained” claims are replaced by uncalibrated score and empirical validation-conflict wording.
- LightGBM's inactive historical row-sampling description is replaced by explicit no-row-bagging behavior.
- New validation-selection stability results are added; they do not change the canonical selection.

## Unchanged-by-design items

The deep seed-initialization defect was not changed because correcting it changes model weights and requires a complete empirical regeneration. No raw-data retraining was performed, and no test result was used to pick a new candidate.
