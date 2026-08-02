# Independent Manuscript Review Closeout

> **Superseded for final interpretation by [final_self_audit.md](final_self_audit.md).** The prior “next-24-h” timing resolution did not account for left-labelled completed bins.

**Audit date:** 2026-07-29  
**Verdict:** Scientifically defensible as a bounded, single-building offline evaluation.

## High-priority findings closed

| Review finding | Resolution in final manuscript |
|---|---|
| The 490.1-kWh quantity was described too broadly as recorded load. | It is now defined as a processed, meter-derived HVAC-plus-lighting proxy with nominal 1.0/1.0 accounting weights, kW-to-kWh conversion by 0.25 h, and causal forward fill after 8.03% missingness per stream. |
| Zero conflicts could be read as verified physical absence. | The target and every headline result identify the selected south-zone camera-derived label; the discussion explicitly says camera-label-empty is not physical absence. |
| “Day-ahead” could imply a 24-h lead time for every action. | The title and text now use **next-24-h**. Methods state that targets begin 15 min after the forecast anchor and end 24 h later. |
| Base-model reproducibility was under-specified. | A model-specification table adds feature availability, seed averaging (42/43/44), tabular/deep training settings, Transformer dimensions, and validation-loss early stopping. |
| Threshold selection was incomplete. | Methods specify the 37-value 0.050--0.950 grid, the 10% validation conflict constraint, safe-opportunity objective, Empty-recall tie-break, and offline-only nature of the objective. |
| Policy run extraction and endpoint scope were ambiguous. | The protocol now states horizon-local run extraction and the exact 2019-02-21 02:00 data endpoint. |
| Final-page layout was sparse and Fig. 2 annotations were tight. | The redundant exploratory-status table was replaced by concise status prose; bibliography columns balance on the final page, and Fig. 2 was regenerated with added annotation room. |

## Residual, non-removable limitations

The manuscript retains the following limitations rather than hiding them: a one-building selected-zone study; camera-label rather than physical-absence evidence; load-proxy imputation; unconfirmed source timezone; missing raw-data retraining; conditional bootstrap intervals; reconstructed rather than preregistered hybrid selection; no hybrid seed dispersion or full hybrid rolling-origin reconstruction; no counterfactual energy, comfort, equipment, tariff, or intervention outcome; and nonfresh decision-aware/window-aware diagnostics.

## External release requirements

The author must supply the target venue, author metadata, contribution/funding/conflict declarations, and persistent artifact archive URL, then rebuild with the venue's toolchain and run the IEEE PDF Checker. These are release metadata and packaging requirements, not unresolved scientific findings.
