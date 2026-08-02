# Results Summary: Saved-Output, Post-Bin Analysis

**Status: requires empirical rerun** for any prospective or operational claim. This document reports reproducible calculations from committed processed and prediction exports. It does not report a full raw-data retraining.

## Timing and source boundary

- A stored anchor 't' is the left label of completed bin '[t,t+15 min)'.
- Effective availability is 't+15 min'; a '00:00' policy label means an effective '00:15' boundary.
- The 96 targets span '[t+15 min,t+24 h+15 min)'.
- The input is the **cleaned** Building 59 release. Upstream imputation and original observation-end provenance are not reconstructible from this repository.

## Separate evaluation scopes

| Scope | Unit | Primary result |
|---|---:|---:|
| Forecast discrimination | 388,032 overlapping test rows / 4,042 anchors | Empty AUPRC 0.8514 |
| Fixed policy accounting | 43 non-overlapping midnight-labelled test horizons / 4,128 target intervals | 259 recommendations, 0 observed camera-label conflicts, 490.1 kWh proxy |

The two scopes must not be combined into “AUPRC on 43 test days.”

## Canonical forecast comparison

All values below derive from 'results/canonical_model_comparison.csv'. Scores are bounded Empty-class scores; no calibrator is fitted.

| Paper-facing model | Empty AUPRC | Empty Brier | Empty precision | Empty recall | Empty F1 |
|---|---:|---:|---:|---:|---:|
| Historical Average | 0.8497 | 0.0974 | 0.7264 | 0.8015 | 0.7621 |
| LightGBM | 0.8382 | 0.0956 | 0.7610 | 0.7593 | 0.7601 |
| Compact Transformer encoder (legacy 'Original Transformer') | 0.7621 | 0.1136 | 0.7253 | 0.6022 | 0.6581 |
| Direct linear occupancy baseline (legacy 'DLinear') | 0.5933 | 0.1812 | 0.5764 | 0.6657 | 0.6179 |
| Primary hybrid | 0.8514 | 0.0928 | 0.7677 | 0.7556 | 0.7616 |

The primary-hybrid point margins are +0.0017 over Historical Average and +0.0132 over LightGBM. Paired daily-block intervals for both AUPRC contrasts cross zero.

## Fixed policy comparison

Every threshold was nominally selected on 39 validation policy horizons to maximize offline safe load opportunity subject to empirical validation interval conflict no greater than 10%. “Safe” means recommended and subsequently camera-label-empty.

| Model | Score threshold | Validation conflict | Test conflict | Offline safe opportunity | Safe/recommended intervals | Safe/recommended windows |
|---|---:|---:|---:|---:|---:|---:|
| Historical Average | 0.950 | 8.33% | 0/66 (0.00%) | 94.6 kWh | 66/66 | 12/12 |
| LightGBM | 0.950 | 9.61% | 11/265 (4.15%) | 493.9 kWh | 254/265 | 16/19 |
| Primary hybrid | 0.875 | 8.75% | 0/259 (0.00%) | 490.1 kWh | 259/259 | 14/14 |

The 490.1 kWh figure is the processed 'max(hvac_S + lig_S, 0) × 0.25 h' overlap where recommendations and subsequent camera-empty labels coincide. It is not savings, capacity, or an intervention effect.

## Conditional uncertainty and selection stability

- Fixed-policy 2,000-replicate daily-block bootstrap: primary daily-horizon AUPRC 0.8522 [0.7918, 0.9016]; opportunity 490.1 kWh [153.1, 966.7].
- Primary minus LightGBM AUPRC: +0.0163 [-0.0050, +0.0426]; opportunity: -3.8 kWh [-208.2, +174.6].
- The all-zero observed primary conflict blocks cannot estimate unseen conflict; the bootstrap conflict interval is zero only conditional on this test period.
- In the 231-weight full-overlap validation grid, ranks 1 and 2 differ by 0.000032 AUPRC and eight candidates are within 0.0005.
- In a separate validation-only daily-block diagnostic (1,000 resamples of 39 horizons), the canonical blend is selected 23 times (2.3%); the canonical threshold 0.875 is selected 111 times (11.1%). This is a sensitivity diagnostic, not a post-hoc replacement selection.

Sources: 'results/canonical_uncertainty_summary.csv', 'results/validation_selection_stability.csv', and 'results/hybrid_primary_weight_search.csv'.

## Interpretation

Supported: reproducible post-bin score and policy accounting under the saved cleaned-source exports.

Unsupported: real-time availability at 00:00, source-causal preprocessing, calibrated risk, verified energy savings, comfort, physical absence, controller safety, external generalization, or fresh confirmation of decision-aware/window-aware exploratory candidates.
