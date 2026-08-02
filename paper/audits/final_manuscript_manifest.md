# Final Manuscript Manifest

**Version date:** 2026-08-01  
**Evidence verdict:** **requires empirical rerun**

## Manuscript identity

| Field | Value |
|---|---|
| Title | *Validation-Selected Empty-Window Recommendations: An Offline Post-Bin Occupancy-Forecasting Case Study* |
| Format | Anonymous generic IEEEtran conference-style draft |
| Central contribution | A reproducible saved-output, post-bin evaluation that separates overlapping occupancy-score discrimination from non-overlapping stable-window offline processed-load-proxy accounting. |
| Authorized interpretation | Offline, camera-label-conditioned opportunity accounting from cleaned-release saved outputs. |
| Excluded interpretation | Real-time midnight issuance, calibrated risk, verified energy savings, controllable capacity, comfort preservation, controller performance, or external generalization. |

## Delivered files and hashes

| File | SHA-256 |
|---|---|
| `paper/submission/occupancy_empty_window_ieee_post_bin_case_study.pdf` | `74ad6cbf7c9ad7f408ebcc7b4ffe08d694df425e651e7315fb48308b2bf35da2` |
| `paper/manuscript/main.tex` | `59210eb1942f9da71b9e168c40e21f1930c2984b32b5f583d4656c26d5420f43` |
| `paper/manuscript/references.bib` | `b94a535dc2aff6c6fc9961f3644382a02355b30c00eff39a6c36c6e2427ab2e8` |
| `paper/manuscript/figures/fig_policy_comparison.png` | `e8094bb362307f09c790f29ebd05db228e3df0d443b2b125ad1f905e02966066` |
| `paper/manuscript/figures/fig_paired_uncertainty.png` | `aaab31d0d582c0b42baa9e15e5cc853a4f2b69ae780be6f465a8c250a533709b` |
| `results/canonical_model_comparison.csv` | `bab879926bca482d42698475e8381c0886029d727ce17efff622c810d299d2c2` |
| `results/canonical_policy_10pct.csv` | `a7821c9454584b4e426ae6226acef8825c2f2ce18f41b526ccb8eee891c54dab` |
| `results/validation_selection_stability.csv` | `25e7bf581505c3dfb595ddc32334bdf529b68b6a9b69d98e5848ed9ac6bfd356` |
| `results/forecast_time_semantics.csv` | `9a064864997435cad88e40602f5e8599abfd75c92ad1852b0ab4c164b45f95f1` |

## Canonical numerical anchors

- Forecast scope: Empty AUPRC 0.8513696056 for the primary blend across 388,032 overlapping held-out rows from 4,042 anchors.
- Policy scope: 43 non-overlapping midnight-labelled completed-input-bin horizons with effective 00:15 availability boundaries.
- Fixed policy: threshold 0.875; 259 recommended / 259 subsequently camera-label-empty / 0 conflict intervals; 14 / 14 / 0 windows; 490.1463795 kWh processed HVAC-plus-lighting load-proxy overlap.
- Comparator: LightGBM has 493.9231552 kWh proxy overlap and 11 conflicts among 265 recommendations.
- Selection qualification: primary weights 0.15/0.60/0.25 are a nominal validation-grid maximum; rank 1 exceeds rank 2 by 0.000032 AUPRC, and perturbation checks do not establish a unique winner.

## Required handoff before any external submission

1. Execute the empirical rerun protocol in `rerun_manifest.md` from provenance-tagged source streams without reusing the current test exports for selection.
2. Replace the anonymous author block, data archive placeholder, funding, contribution, and conflict declarations.
3. Switch to the exact target-venue template and page limit, rerun its required PDF checker, and refresh this manifest, figures, references, and compilation audit.
