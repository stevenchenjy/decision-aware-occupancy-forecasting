# Code–Paper Consistency Log

**Audit date:** 2026-08-01  
**Interpretation:** “Aligned” means the paper names and bounds the existing implementation correctly. It does not mean the result is prospective.

| Topic | Code / saved artifact | Manuscript / documentation alignment | Status |
|---|---|---|---|
| Bin semantics | 'src/lbnl_pipeline.py' uses explicit left-closed/left-labelled resampling; 'src/hybrid_analysis.py' checks 15-min target offsets; 'results/forecast_time_semantics.csv' records effective boundary. | Methods, Table I, abstract, results, conclusion, README, results summary, data guide all state completed bin '[t,t+15 min)' and effective 't+15 min'. | Aligned |
| Source provenance | Configured directory is 'Bldg59_clean data'; no raw source folder or checksums are committed. | Paper says cleaned release and explicitly denies source-causal/prospective availability. | Aligned limitation |
| Forecast horizon | Future positions are anchor + 1 through +96; 96 left-labelled targets occupy '[t+15 min,t+24 h+15 min)'. | Methods/table state same; midnight-labelled policy horizon is 00:15 through next 00:15 exclusive. | Aligned |
| Historical baseline | Train-only weekday/time-slot average in 'src/lbnl_pipeline.py'. | Tables and methods call it train-only historical schedule baseline. | Aligned |
| LightGBM | Explicit configuration: column fraction 0.85, no row bagging ('subsample=1', 'subsample_freq=0'); stratified training. | Model table states no row bagging and does not describe inactive 0.85 row sampling. | Aligned |
| Linear model | Class 'DLinear' applies one 'Linear(96,96)' mapping to past occupied channel. | Display name is direct linear occupancy baseline; legacy key only for matching exports. | Aligned |
| Transformer | 'SequenceTransformer' is compact encoder-only with known-future calendar projection. | Display name is compact Transformer encoder; no encoder-decoder/original-architecture claim. | Aligned |
| Seed handling | Modules are instantiated before 'train_deep_model' invokes seed reset. | Model table and limitations state historical seed labels do not establish controlled initialization. | Aligned limitation; empirical rerun required |
| Score interpretation | Trees use stratified sampling and deep training uses weighted BCE; no calibrator is fitted. | Paper calls outputs uncalibrated scores; Brier/log loss/ECE are diagnostics. | Aligned |
| Canonical blend | 'select_weights_from_validation' selects 0.15/0.60/0.25 on validation before test read. | Methods call it nominal validation grid maximum, not unique optimum. | Aligned |
| Policy threshold | Validation only; 37 thresholds; four-step stable mask; conflict denominator recommendations. | Equations and table define empirical validation conflict cutoff and camera-label-conflict scope. | Aligned |
| Opportunity | 'controllable_kwh' applies processed HVAC+lighting proxy and 0.25 h factor to subsequently label-safe intervals. | Equations/captions call it offline processed-load-proxy overlap, not savings. | Aligned |
| Scope | 'canonical_model_comparison.csv' uses 388,032 overlapping rows; policy CSV uses 43 daily horizons. | Abstract/results/docs separate both scopes. | Aligned |
| Stability | 'scripts/audit_validation_selection_stability.py' reads validation/processed only. | Results/Table IV say diagnostic does not replace canonical selection. | Aligned |
| Expanded searches | Candidate selection is now staged before test diagnostic read; existing diagnostics are historical. | Appendix and docs call them exploratory/frozen future challengers. | Aligned |
| Reproducibility | Saved outputs regenerate; no raw data/environment lock/model artifacts for complete retraining. | Reproduction/docs distinguish saved-output regeneration from empirical retraining. | Aligned limitation |

## Specific implementation decisions

1. Resampling and LightGBM changes preserve the observed numerical behavior; their downstream saved artifacts were regenerated.
2. Model naming, score interpretation, timing language, and metadata were corrected in prose/artifacts without changing score values.
3. Deep seed initialization was not silently fixed because doing so changes base predictions. It is retained as an explicit legacy behavior and a mandatory empirical-rerun correction.
4. The current test exports were not used to choose a replacement blend, threshold, or exploratory candidate.
