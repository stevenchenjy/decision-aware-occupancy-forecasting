# Decision-aware joint search input audit

## Material Passport

- Origin Skill: experiment-agent
- Origin Mode: validate/run
- Verification Status: ANALYZED
- Version Label: decision_aware_joint_audit_v1

## Audit conclusion

**PASS.** The saved outputs are sufficient for every requested validation metric and fixed-candidate test evaluation.

This audit uses committed saved outputs only. It does not access the external Dryad directory and does not retrain a base model.

## Exact source files

- `results/forecast_predictions_validation_all_models.csv` — 77,946,480 bytes; SHA-256 `40ef315fcaff23a84235f7831dfd61d6225f834daf5571a3d939dab740eac80d`
- `results/forecast_predictions_test_all_models.csv` — 81,901,167 bytes; SHA-256 `f0aa4ff98419a2686a7e393a72c837afdf464e38bea3d650a2da6cdd7f4021be`
- `results/processed_lbnl_15min_pacific.csv` — 6,625,451 bytes; SHA-256 `b060ce8205f94dfac43194dc185e3d2f56eefcefecf3bf9e625331aba14099a4`
- `results/hybrid_primary_weight_search.csv` — 19,512 bytes; SHA-256 `4d65acf484b4aa0c0538d7d1d34b142f616b643410e6a5abcca793ec89df53ed`
- `results/hybrid_selected_threshold_policies.csv` — 5,243 bytes; SHA-256 `e1b41696b42b933d5336dd1191a578ffa2c5e88e4a6d7802447dd5227d3cce76`
- `results/hybrid_policy_results_test.csv` — 6,457 bytes; SHA-256 `e508c2191b99ff7b16361b5fddb5e17ac8e9f37e68a72e8c0808171391d9da89`
- `results/canonical_model_comparison.csv` — 1,859 bytes; SHA-256 `bab879926bca482d42698475e8381c0886029d727ce17efff622c810d299d2c2`
- `results/canonical_policy_10pct.csv` — 1,703 bytes; SHA-256 `a7821c9454584b4e426ae6226acef8825c2f2ce18f41b526ccb8eee891c54dab`
- `predictions/historical_average_test_predictions.csv` — 41,821,676 bytes; SHA-256 `c708440609e92d5026e1da3c9b5509b4040f4568a5c05fd8752c9de5fca85971`
- `predictions/lightgbm_test_predictions.csv` — 44,954,982 bytes; SHA-256 `207b4639dce1f470dff10c11789f18ac6fe847219975c8cadc7d319dbd7fb897`
- `predictions/transformer_test_predictions.csv` — 39,846,119 bytes; SHA-256 `58368515c2c0584ac5f58ba132ff5026eff120e54f0e1842114d5c7c49905b96`

The combined validation export is the only saved validation file that contains aligned Historical Average, LightGBM, and Transformer probabilities. Individual saved test exports are redundant alignment checks; the combined test export is the evaluation source.

## Required columns

- Validation/test predictions: `split, anchor_time, target_time, horizon_step, actual_occupied, actual_empty_positive, historical_average_empty_probability, lightgbm_empty_probability, transformer_empty_probability`.
- Processed load proxy: `date_local`, `hvac_S`, and `lig_S` from the processed saved table.
- The Empty label is `actual_empty_positive = 1 - actual_occupied`.
- The interval load proxy is `max(hvac_S + lig_S, 0) * 0.25 h`, following the current implementation.

## Validation and test scopes


| Scope | Rolling rows | 96-step anchors | Midnight-labelled post-bin policy horizons | Policy rows | Target-time range |
|---|---:|---:|---:|---:|---|
| Validation | 359,520 | 3,745 | 39 | 3,744 | `2018-11-28 00:00:00-08:00` to `2019-01-06 23:45:00-08:00` |
| Held-out test | 388,032 | 4,042 | 43 | 4,128 | `2019-01-09 00:00:00-08:00` to `2019-02-21 02:00:00-08:00` |


- Forecast Empty AUPRC uses every overlapping rolling prediction row in the relevant split.
- Policy selection/evaluation uses non-overlapping midnight-labelled completed-input-bin 96-step horizons only; a 00:00 label has an effective 00:15 availability boundary.
- Validation ends at `2019-01-06 23:45:00-08:00`; test begins at `2019-01-09 00:00:00-08:00`. The scopes do not overlap when the audit passes.
- Processed-load-proxy mapping covered 359520 validation rows and 388032 test rows; the direct check found no missing timestamp matches.

## Prediction-export alignment

- per_model_export_alignment:Historical Average: **pass** — keys/labels match=True; max probability difference=0
- per_model_export_alignment:LightGBM: **pass** — keys/labels match=True; max probability difference=0
- per_model_export_alignment:Original Transformer: **pass** — keys/labels match=True; max probability difference=0

## Current selection and recommendation logic

- Weight search: all 231 legal Historical Average/Seasonal, LightGBM, and compact-Transformer score weights on the 0.05 simplex grid; select the maximum validation Empty AUPRC on all overlapping validation forecasts.
- Canonical forecast-optimal weights: `0.15 / 0.60 / 0.25`; best saved validation Empty AUPRC `0.7286379575`.
- Threshold grid: 37 Empty-score thresholds from `0.05` through `0.95` in `0.025` increments. Scores are not calibrated probabilities.
- Current 10% policy: maximize validation offline camera-label-empty load-proxy overlap among thresholds with empirical interval-level occupancy-conflict rate `<= 0.10`; use Empty recall as the same-proxy tie-break. The canonical hybrid threshold is `0.875`.
- Stable recommendation: the uncalibrated score remains at or above threshold for at least four consecutive 15-minute intervals (one hour) within each midnight-labelled post-bin horizon. Every interval in a qualifying run is recommended.
- Interval conflict rate: occupied recommended intervals divided by all recommended intervals. A window is all-camera-label-empty only if every interval in that window is actually Empty.
- Offline load-proxy overlap: the saved HVAC-south plus lighting-south load proxy summed only over recommended intervals whose subsequently observed label is Empty. This is offline opportunity accounting, not verified energy savings.

## Sufficiency by requested metric

| Requested quantity | Available source | Status |
|---|---|---|
| Validation Empty AUPRC | validation labels + three aligned probability columns | available |
| Validation conflict and coverage | midnight labels + stable-window mask | available |
| Validation offline load-proxy overlap | midnight-labelled post-bin labels + timestamp-mapped HVAC/lighting kWh | available |
| Recommended/safe/conflict intervals | stable mask + labels | available |
| Recommended/safe windows | existing run extraction and all-empty window definition | available |
| Fixed held-out evaluation | chronologically disjoint test export + fixed validation candidates | available |

## Missing inputs or scientific blockers

- None.

The saved exports do not support new base-model training, per-seed joint-hybrid dispersion, or new rolling-origin hybrid folds, but none of those are required for this saved-output joint search.
