# NEW Artifact Integration Audit

## Material Passport

- Origin Skill: academic-research-suite / experiment-agent
- Origin Mode: validate
- Origin Date: 2026-07-10
- Verification Status: VERIFIED for saved-output hybrid regeneration; CANNOT VERIFY for full raw-data retraining because raw Dryad files are not present
- Version Label: new_artifact_integration_audit_v1

## Audit judgment

The July 9 hybrid work is scientifically usable after one provenance repair: the staged script hard-coded the three-way primary weights, even though its report called the result validation-selected. An explicit validation-only 0.05 simplex search was reconstructed from the saved validation predictions. It selects exactly `Historical Average=0.15`, `LightGBM=0.60`, and `Original Transformer=0.25`, reproducing validation Empty AUPRC `0.72863796` and test Empty AUPRC `0.85136961`. The primary hybrid is therefore defensible under that now-declared grid.

The staged `Hybrid balanced tree-deep` result (`0.85537679`) was retained only as exploratory supplementary evidence. Its fixed architecture was part of an ad hoc shortlist and it was highlighted because it was best on test. It is not a headline or deployable selected model.

No evidence of future-label leakage, future-sensor leakage, load-as-predictor leakage, test-selected thresholds, or timestamp misalignment was found in the integrated hybrid calculation. The main unresolved robustness gaps are hybrid-specific seed dispersion and rolling-origin retraining.

## Repository and staging inventory

The initial inventory contained 387 non-`.git` files, of which 215 were under `NEW/`. `NEW/` occupied 657 MB. The important competing locations were:

- `NEW/result/` versus `NEW/results/`
- `NEW/figure/` versus `NEW/figures/`
- three executable/output-bearing notebooks in `NEW/` versus the root reporting-only notebook
- five base prediction exports plus one hybrid export in `NEW/predictions/` versus root `predictions/`
- a staged pinned `requirements.txt` versus the root supported environment files

The complete pre-integration file list, byte sizes, SHA-256 hashes, mapped canonical paths, and dispositions are in `archive/new_staging_2026-07/new_file_manifest.csv` (215 rows).

### Important artifact register

| Staged artifact or family | Purpose and generator | Inputs | Reproducibility | Relationship and disposition |
|---|---|---|---|---|
| `LBNL_occupancy_transformer_forecasting copy.ipynb` | Earliest two-epoch experiment with Random Forest, Transformer, TFT-lite, PatchTST-lite, fixed threshold, and simplified energy/emissions calculations | Raw LBNL streams | Not suitable for canonical reproduction: different split, timezone handling, model set, and policy | Conflicts with the later fair protocol; archived as an obsolete research record |
| `LBNL_occupancy_transformer_forecasting.ipynb` | Full fair-protocol pipeline writing singular `result/` and `figure/` | Raw LBNL streams | Reproducible only with external raw data and compatible environment | Direct predecessor of the canonical pipeline; archived |
| `LBNL_occupancy_forecasting_main.ipynb` | Later full run writing plural `results/` and `figures/`; source of the saved base-model outputs | Raw LBNL streams | Same raw-data limitation; saved outputs are internally reproducible | Superseded by root `src/lbnl_pipeline.py`, scripts, and reporting notebook; archived |
| `NEW/src/*.py` | Reusable preprocessing, features, models, evaluation, policy, energy, and plotting helpers | Same raw LBNL streams | Byte-identical to root counterparts | Removed as verified duplicates |
| `NEW/scripts/improve_transformer_results.py` | Probability-level seasonal and hybrid blending, validation threshold sweep, test evaluation, and assignment-note generation | Canonical validation/test all-model predictions plus processed load | Deterministic from saved inputs, but primary weights were not searched in code | Archived unchanged; replaced by `src/hybrid_analysis.py` and `scripts/generate_hybrid_artifacts.py` |
| `forecast_predictions_validation_all_models.csv` | 359,520 overlapping validation predictions from 3,745 24-hour anchors | Base-model outputs and labels | Exact root/`NEW/results` duplicate | Root copy retained as canonical input |
| `forecast_predictions_test_all_models.csv` | 388,032 overlapping test predictions from 4,042 24-hour anchors | Base-model outputs and labels | Exact root/`NEW/results` duplicate | Root copy retained as canonical input |
| `NEW/result/forecast_predictions_*` | Earlier serialization of the same prediction run | Same predictions | Numerically equal to plural snapshot; maximum difference `4.44e-16` in Random Forest probabilities | Removed after hash/numeric reconciliation |
| `processed_lbnl_15min_pacific.csv` | Aligned 15-minute labels, sensors, time features, and load streams | Raw LBNL files | All three copies had the same SHA-256 hash | Root copy retained |
| Base per-model predictions | One long-form export each for Historical Average, LightGBM, Random Forest, Transformer, and DLinear | Base combined prediction export | Keys, labels, and probabilities align with the canonical combined export (maximum difference at or below `1e-7`) | Root copies retained |
| `hybrid_transformer_test_predictions.csv` | Staged test probabilities for seasonal, primary, balanced, and tree-seasonal blends | Saved base test probabilities | Deterministic and numerically reproduced | Exact staged file archived; canonical test and validation exports regenerated under `predictions/hybrid_ensemble_*` |
| `improved_transformer_alpha_search.csv` | 0.01 validation grid for Historical Average/Transformer blend | Validation labels and probabilities | Fully reproducible | Integrated as `results/hybrid_seasonal_transformer_weight_search.csv`; staged version archived |
| `improved_transformer_candidate_scores.csv` | Validation/test AUPRC for a small staged candidate shortlist | Validation/test labels and component probabilities | Scores reproducible; shortlist origin not documented | Primary candidate repaired with full declared grid; balanced candidate supplementary; staged table archived |
| `improved_transformer_model_metrics.csv` | Test metrics for staged hybrid candidates | Saved test labels/probabilities | Fully reproducible | Superseded by the eight-model canonical table |
| `improved_transformer_selected_thresholds.csv` | Validation-selected thresholds for 5%, 10%, and 20% risk policies | Midnight validation horizons, load, hybrid probabilities | Fully reproducible | Superseded by `hybrid_selected_threshold_policies.csv` |
| `improved_transformer_policy_results_test.csv` | Fixed-threshold held-out test policy outcomes | Midnight test horizons, load, selected thresholds | Fully reproducible | Superseded by `hybrid_policy_results_test.csv` and `canonical_policy_10pct.csv` |
| `improved_transformer_threshold_sweep_validation_daily.csv` | Hybrid validation threshold sweeps | Same as above | Fully reproducible | Superseded by the combined validation/test diagnostic sweep table |
| Base metric, threshold, policy, energy, stable-window, reliability, horizon, feature, robustness, and example-day CSV families | Main June 6 pipeline outputs | Base prediction exports and processed data; several require raw training to recreate from scratch | 109 staged files were exact canonical duplicates; later root presentation tables extend the snapshot | Root files retained; aliases already under `results/archive/` or staged archive |
| `risk_energy_pareto_*`, `risk_constraint_summary.csv`, metric aliases, and `delivery_manifest.csv` | Presentation-focused aliases/diagnostics from the staged delivery | Existing result tables | Reproducible from saved tables | Archived as staged presentation aliases; not active canonical results |
| `NEW/figure/` and `NEW/figures/` | June presentation figures plus diagnostic Pareto variants | Result CSVs and notebooks | Reproducible; many were duplicated or later regenerated | Both trees preserved under `figures/archive/new_staging_2026-07/`; active figures live only in `figures/` |
| Staged Markdown summaries | June experiment summary, simulation summary, validity checklist, and Chinese assignment notes | Saved tables/notebook output | Text is traceable but predates the hybrid audit | Archived; root documentation revised |
| Staged `requirements.txt` | Exact versions used in the late notebook environment | Environment observation | `torch==2.11.0+cpu` is not portable through the default pip index | Archived for provenance; root bounded requirements and Conda environment retained |
| `ipython/`, `kernels/`, `__pycache__/`, `.DS_Store` | Runtime/editor debris | None | Not research artifacts | Removed from active presentation |

## Canonical data protocol

### Inputs and target

- Raw source: Dryad LBNL Building 59 dataset, selected south-zone streams.
- Required raw files: `occ.csv`, `wifi.csv`, `site_weather.csv`, `zone_temp_interior.csv`, `ele.csv`, and `zone_co2.csv`.
- Frequency: 15 minutes.
- Target: `occupied=1` when maximum selected south-zone occupancy count in a bin is greater than zero; evaluation uses `Empty=1`.
- Forecast horizon: 96 intervals = 24 hours.
- Historical context: 96 intervals = 24 hours.
- Known-future variables: calendar/time variables only.
- Observed sensor variables: issue-time/past values only.
- Excluded predictors: HVAC, lighting, MELS, and total electrical load.

### Chronological splits

| Split | Anchors | Forecast rows | First target | Last target |
|---|---:|---:|---|---|
| Train | 17,861 | 1,714,656 | 2018-05-23 00:00 Pacific | 2018-11-25 23:45 Pacific |
| Validation | 3,745 | 359,520 | 2018-11-28 00:00 Pacific | 2019-01-06 23:45 Pacific |
| Test | 4,042 | 388,032 | 2019-01-09 00:00 Pacific | 2019-02-21 02:00 Pacific |

Both train-validation and validation-test measured gaps are 24.25 hours. Threshold policies use 39 validation and 43 test midnight anchors, yielding non-overlapping daily horizons for opportunity accounting.

### Seeds and base-model hyperparameters

- Seeds: 42, 43, 44; probabilities are averaged across seeded runs.
- LightGBM: 320 estimators, learning rate 0.05, 31 leaves, minimum child samples 50, subsample 0.85, column sample 0.85, L2 regularization 1.0, balanced classes, maximum 200,000 sampled training rows per seed.
- Random Forest: 70 estimators, maximum depth 14, minimum leaf size 20, square-root feature sampling, balanced subsample classes, maximum 200,000 sampled rows per seed.
- Transformer: `d_model=32`, 4 heads, one encoder layer, dropout 0.10, AdamW learning rate `1e-3`, maximum 12 epochs, patience 4, batch size 256.
- DLinear: same 96-step history/horizon, seeded training budget and early-stopping controls as recorded in `results/model_training_control.csv` and `results/training_history.csv`.

## Hybrid architecture and selection

“Seasonal” means the train-only Historical Average probability for the local weekday and 15-minute time slot. It is not a learned seasonal decomposition and does not use validation/test labels.

- Seasonal component: strong recurring schedule prior.
- GBDT component: LightGBM prediction using nonlinear combinations of lagged occupancy, rolling history, issue-time sensors, horizon position, and known-future calendar features.
- Transformer component: sequence model using the prior 96-step multivariate history plus known-future time features for the next 96 steps.
- Blend level: convex averaging of `Empty` probabilities. No logit-, feature-, or decision-level fusion is used.
- Seasonal-Transformer weight: validation AUPRC grid from 0.00 to 1.00 in steps of 0.01; selected Transformer weight 0.46.
- Primary hybrid weights: validation AUPRC simplex grid in steps of 0.05; selected `0.15/0.60/0.25` for Historical Average/LightGBM/Transformer.
- Retraining after selection: none. The hybrids operate on fixed base ensemble probabilities; no model is refit on validation or test.
- Calibration: no post-hoc calibration. Probability averaging improves Brier/log-loss point estimates, and calibration is assessed diagnostically only.
- Thresholds: swept from 0.05 to 0.95 in increments of 0.025 on validation midnight horizons.
- Risk selection: maximize validation safe opportunity subject to recommendation conflict rate `<= delta`; if no point qualifies, use the minimum-conflict fallback and flag the constraint miss.
- Test use: fixed weights and thresholds are applied once for primary reporting. Complete test threshold sweeps are labeled diagnostic and are not used to select operating points.

## Discrepancy reconciliation

### Original Transformer AUPRC

The canonical aggregate test Empty AUPRC is `0.7620963459460512`, computed over all 388,032 saved rolling forecast rows and rounded to `0.7621`. It is reproduced from:

- `results/forecast_predictions_test_all_models.csv`
- `predictions/transformer_test_predictions.csv`
- the two later full notebooks in the archive
- `results/model_metrics_empty_positive.csv`

No aggregate AUPRC artifact supports `0.7633`. Values near `0.7633` occur as individual predicted probabilities, not aggregate metrics. The closest aggregate secondary value is the Transformer 6-12 hour bucket AUPRC `0.76214603`, which also rounds to `0.7621`. Therefore `0.7633` is treated as a transcription or row-value confusion, not a separate canonical run. The obsolete early notebook reports occupied-positive Transformer AUPRC `0.951651` on a different split/protocol and is not comparable.

### Directory and serialization differences

- Singular `result/` versus plural `results/` combined prediction files are numerically identical apart from floating serialization noise no larger than `4.44e-16`.
- Root and `NEW/results/` canonical combined prediction files were byte-identical.
- Root figures were regenerated later and therefore differ in bytes from staged PNGs; the underlying source tables remain reconciled.
- `Historical Average` also has Empty F1 `0.762095`, which rounds to `0.7621`; this is a different metric and is another possible source of label confusion.

## Experimental-validity verdict

| Check | Verdict | Evidence |
|---|---|---|
| Same split boundaries and horizon | Pass | Hybrids consume the exact base validation/test rows; 96 steps per anchor |
| Same target and stable-window rule | Pass | `actual_empty_positive=1-actual_occupied`; default minimum is four 15-minute steps |
| No future-label or sensor leakage | Pass | Base pipeline uses shifted history and issue-time sensors; hybrids add no features |
| No test-derived feature engineering | Pass | Hybrids use saved component probabilities only |
| No test-selected primary weights | Pass after repair | Explicit validation-only simplex search selects the reported primary weights |
| No test-selected primary threshold | Pass | Threshold selected on 39 validation midnight horizons |
| Comparable timestamps and labels | Pass | Unique prediction keys, consistent repeated labels, matching per-model exports |
| Load alignment | Pass | All test target timestamps map to processed `hvac_S + lig_S` interval kWh under the missing-data gate |
| Probability calibration | Diagnostic only | No recalibration; Brier/log loss/ECE reported |
| Exploratory balanced candidate | Supplementary only | Architecture is not backed by a documented pre-test search; retained because test-best |

## Robustness and uncertainty availability

- Implemented for the primary hybrid: 2,000 paired daily-block bootstrap resamples, calibration/reliability diagnostics, and stable-window sensitivity.
- Multiple seeds: base components average seeds 42/43/44, but per-seed aligned component predictions were not saved. Hybrid-specific seed dispersion cannot be reconstructed without retraining.
- Rolling-origin: saved folds cover Historical Average, LightGBM, and Random Forest only. Transformer fold predictions are missing, so the full hybrid cannot be evaluated without retraining.
- The 0-conflict bootstrap distribution is degenerate because every observed primary-hybrid test block has zero conflicts. This does not establish zero future risk. With 259 recommended intervals, the one-sided 95% independent-trial upper bound is about 1.15%; with 14 windows it is about 19.3%. Independence is not established, so both are descriptive sensitivity bounds.

## Statistical fallacy scan

Coverage: 11/11 checked.

| Fallacy | Finding |
|---|---|
| Simpson's paradox | Not demonstrated; no subgroup reversal claim is made |
| Ecological fallacy | Avoided; claims are restricted to selected-zone schedules, not individual occupants |
| Berkson's paradox | No relevant admission/filter mechanism; single-building selection limits external validity |
| Collider bias | No causal regression claim; load is excluded from predictors |
| Base-rate neglect | Empty prevalence and precision/recall/AUPRC are reported |
| Regression to the mean | Not a pre/post extreme-group design |
| Survivorship bias | No participant attrition; data coverage limits are documented |
| Look-elsewhere effect | Caution: the balanced candidate is test-ranked and therefore supplementary |
| Garden of forking paths | Caution: staged fixed hybrid shortlist lacked a declared search; primary grid is now explicit |
| Correlation implies causation | Avoided; opportunity is not described as verified energy savings |
| Reverse causality | Not applicable to the predictive comparison; no causal direction is claimed |

## Disposition summary

- Main result: validation-selected Hybrid Seasonal-GBDT-Transformer.
- Validated intermediate: Seasonal-Transformer Blend.
- Reference comparisons: Historical Average and LightGBM.
- Supplementary only: Exploratory Hybrid Balanced Tree-Deep and other staged ad hoc hybrids.
- Archive: executable notebooks, staged script/report/tables, singular/plural figures, presentation aliases, and exact staged hybrid prediction export.
- Removed from active presentation: byte-identical duplicates, numerically equivalent duplicate serializations, caches, kernel metadata, and editor debris.
- Active `NEW/`: only `NEW/README.md`, which points to canonical and archived destinations.
