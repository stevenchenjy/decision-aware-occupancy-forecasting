# Claims and Limitations

## Required status line

> This is an offline, post-bin saved-output case study. The current repository supports reproducible opportunity accounting, not a prospective real-time operating claim. Audit verdict: requires empirical rerun.

## Supported wording

- The source is the cleaned LBNL Building 59 release; the repository analyzes selected south-zone streams at 15-min resolution.
- An anchor labelled 't' represents the completed left-labelled bin '[t,t+15 min)'; the effective availability boundary is 't+15 min'.
- Empty is the positive class for recommendation-oriented metrics and means no detected occupant in selected camera counts, not verified physical absence.
- The canonical primary blend uses Historical/LightGBM/compact-Transformer scores with nominal weights 0.15/0.60/0.25 selected on validation AUPRC before canonical test scores are read.
- The all-overlap primary AUPRC is 0.8514 across 388,032 rows (4,042 anchors); 43 horizons apply only to fixed policy accounting.
- The primary fixed policy has 259/259 subsequently camera-label-empty recommendations, 14/14 camera-label-safe windows, and 490.1 kWh of offline processed-load-proxy opportunity.
- The primary point AUPRC advantage is small, paired contrasts cross zero, and validation perturbations do not identify unique blend weights or threshold.
- LightGBM has 493.9 kWh proxy opportunity and 11/265 camera-label conflicts under its nominal validation-selected policy.
- Decision-aware and window-aware results are exploratory historical diagnostics, not a replacement primary result.

## Mandatory qualifiers

- Call the outputs “uncalibrated Empty-class scores in [0,1],” not calibrated probabilities.
- Call the 10% rule an “empirical validation interval-conflict cutoff,” not a future-risk guarantee.
- Call the opportunity an “offline processed-load-proxy overlap,” not savings, shifted energy, capacity, or delivered flexibility.
- Display models as “compact Transformer encoder (legacy Original Transformer)” and “direct linear occupancy baseline (legacy DLinear)”.
- Explain that deep models were built before seed reset; saved seed labels do not establish controlled initialization.

## Unsupported claims

Do not claim real-time midnight issuance, causal source preprocessing, source-level leakage freedom, calibrated risk, verified energy savings, comfort preservation, physical absence, controller performance, zero future conflict, generalization beyond this building/period, statistically decisive model superiority, or fresh confirmation of expanded searches.

## Required empirical next step

Use raw/provenance-tagged source streams with observation-end timestamps; define the bin-end convention; correct seed initialization; lock environment and selection protocol; fully retrain; and evaluate once on a later untouched period or new building. Add a simulation or intervention before making energy/control claims.
