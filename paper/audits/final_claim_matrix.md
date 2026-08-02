# Final Claim Matrix

Only the formulations below are authorized by the committed evidence. “Requires rerun” means wording alone cannot establish the claim.

| Claim | Exact allowed wording | Evidence | Scope / qualification | Status |
|---|---|---|---|---|
| Source/data | “Cleaned Building 59 selected south-zone release, 26,413 local-time 15-min rows.” | 'results/data_summary.csv'; Luo2022; Hong2022 | Cleaned release, not original raw acquisition data. | Supported |
| Timing | “A label t denotes completed bin [t,t+15 min); effective availability is t+15 min.” | 'src/lbnl_pipeline.py'; 'results/forecast_time_semantics.csv'; tests | Applies after import; source observation-end provenance unresolved. | Supported wording |
| Forecast scope | “Primary AUPRC 0.8514 across 388,032 overlapping test rows from 4,042 anchors.” | 'results/canonical_model_comparison.csv'; prediction export | Not a 43-horizon policy metric. | Supported |
| Policy scope | “Across 43 midnight-labelled horizons with effective 00:15 boundary, primary fixed rule recommends 259 intervals.” | 'results/canonical_policy_10pct.csv'; timing artifact | Later camera labels assess the recommendation. | Supported |
| Camera-label outcome | “All 259 recommended intervals and 14 windows were subsequently camera-label-empty.” | 'results/canonical_policy_10pct.csv' | Does not establish physical absence or future safety. | Supported |
| Opportunity | “490.1 kWh offline processed HVAC-plus-lighting load-proxy overlap.” | 'results/canonical_policy_10pct.csv'; 'src/hybrid_analysis.py' | Not energy saving, capacity, controllability, or counterfactual effect. | Supported |
| LightGBM comparison | “493.9 kWh proxy opportunity with 11/265 camera-label conflicts.” | 'results/canonical_policy_10pct.csv' | Fixed historical policy result. | Supported |
| Model ranking | “Primary nominal point AUPRC is slightly above Historical and LightGBM.” | canonical metrics / bootstrap | Paired intervals cross zero; not decisive superiority. | Supported with qualifier |
| Weight selection | “0.15/0.60/0.25 is the nominal maximum on declared validation grid.” | 'results/hybrid_primary_weight_search.csv' | Rank-1/rank-2 gap 0.000032; nonunique stability. | Supported with qualifier |
| Threshold selection | “0.875 is the nominal validation-selected threshold under empirical conflict cutoff.” | selected policy CSV; threshold sweep | Not a probability/risk guarantee; stability varies. | Supported with qualifier |
| Calibration | “Brier 0.0928, log loss 0.2984, ECE 0.0253 are score diagnostics.” | 'results/hybrid_calibration_summary.csv' | No fitted calibrator. | Supported |
| Model names | “Compact Transformer encoder” / “direct linear occupancy baseline.” | source code architecture | Legacy CSV keys remain Original Transformer/DLinear. | Supported |
| Post-import handling | “Forward fill is row-order-only after import.” | source code / feature policy | Does not establish source-causal imputation or availability. | Supported with qualifier |
| Exploratory searches | “Exploratory historical diagnostics / frozen future challengers.” | search code/results/reports | Cannot replace canonical result using current test. | Supported |
| Energy savings | No affirmative claim allowed. | No counterfactual simulation/intervention. | Requires empirical control/simulation evidence. | Requires rerun/new evaluation |
| Real-time midnight issuance | No affirmative claim allowed. | Left-labelled bins and source provenance gap. | Requires raw timestamp/provenance rerun. | Requires empirical rerun |
| Controlled deep seeding | No affirmative claim allowed. | construction precedes seed reset. | Requires fixed code and all-model rerun. | Requires empirical rerun |
| Generalization | No affirmative claim allowed. | One building/selected zones/short policy period. | Requires later period/new building. | Requires new independent evaluation |
