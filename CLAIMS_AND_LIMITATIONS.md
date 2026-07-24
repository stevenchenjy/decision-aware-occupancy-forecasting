# Claims and Limitations

Use this document when preparing slides, emails, abstracts, or manuscripts.

## Supported claims

- The project evaluates 24-hour-ahead occupancy forecasts for LBNL Building 59 selected south zones at 15-minute resolution.
- Raw timestamps are interpreted as UTC and converted to Pacific time before calendar features are created.
- Empty is the positive class for recommendation-oriented metrics.
- Historical Average uses training labels only and represents a strong recurring weekday/time-slot schedule prior.
- Original models and all hybrids use the same chronological validation/test prediction rows and target definition.
- Seasonal-Transformer weights are selected by validation Empty AUPRC on a 0.01 grid.
- Primary Seasonal-GBDT-Transformer weights are selected by validation Empty AUPRC on a 0.05 simplex grid.
- Risk-policy thresholds are selected on validation midnight horizons and evaluated on held-out test midnight horizons.
- The primary hybrid reports test Empty AUPRC `0.8514`, 490.1 kWh safe opportunity, and zero observed conflicts among 259 recommended intervals across 43 test days.
- LightGBM reports 493.9 kWh safe opportunity and 4.15% test conflict under its validation-selected 10% policy.
- The primary hybrid and LightGBM have nearly equal safe-opportunity point estimates; their paired daily-block difference interval includes zero.
- The primary hybrid's AUPRC point estimate is slightly above Historical Average and LightGBM, but paired daily-block difference intervals include zero.
- Safe opportunity counts only recommended intervals that were actually empty and uses recorded `hvac_S + lig_S` load.
- The exploratory joint search evaluated 8,547 weight-threshold pairs on validation and selected candidates by safe opportunity under explicit conflict, coverage, stable-window, and optional AUPRC-floor constraints.
- After validation-only selection, the unconstrained and 99%-AUPRC-floor candidates produced current-test safe-opportunity point estimates of 623.5 and 650.4 kWh, with observed interval conflict rates of 2.98% and 3.09%, respectively.
- These decision-aware current-test results are descriptive fixed-candidate evaluations, not evidence sufficient to replace the canonical primary.

Preferred thesis wording:

> Strong recurring occupancy schedules explain the performance of Historical Average. A validation-selected probability hybrid combines that schedule prior with nonlinear tabular and temporal-sequence forecasts. In this held-out period its AUPRC point estimate is slightly higher than the schedule baseline, and its 10% policy identifies nearly the same safe opportunity as LightGBM with zero observed conflicts. The small model-level differences are uncertain, and zero observed conflict is not a universal guarantee.

## Model-status boundaries

- Original models: Historical Average, LightGBM, Random Forest, original Transformer, and DLinear.
- Validated intermediate: Seasonal-Transformer Blend (`Historical=0.54`, `Transformer=0.46`).
- Primary: Hybrid Seasonal-GBDT-Transformer (`Historical=0.15`, `LightGBM=0.60`, `Transformer=0.25`).
- Supplementary only: Exploratory Hybrid Balanced Tree-Deep (`Historical=0.20`, `LightGBM=0.50`, `Random Forest=0.10`, `Transformer=0.20`).
- Exploratory decision-aware: joint-search candidates `0.65/0.05/0.30 @ 0.775` and `0.35/0.35/0.30 @ 0.800`.
- Frozen future challenger: window-aware `0.40/0.40/0.20 @ 0.850`; eligible for future one-shot evaluation, not current promotion.
- The exploratory balanced model must not be described as the selected best model merely because its test AUPRC is `0.8554`.

## Unsupported claims

Do not claim:

- verified or causal energy savings,
- deployed BMS/controller performance,
- guaranteed zero occupancy conflict,
- comfort preservation or thermal-comfort compliance,
- carbon-emission reductions,
- a learned decision-aware loss,
- replacement of the canonical primary based on the already-inspected decision-aware or window-aware current-test diagnostics,
- fresh or independent confirmation of the exploratory joint/window-aware candidates,
- reinforcement-learning scheduler performance,
- generalization to other buildings, zones, seasons, or years,
- statistically decisive AUPRC superiority over Historical Average or LightGBM,
- hybrid robustness equal to LightGBM across seeds or rolling origins,
- production readiness.

## Key limitations

- One building and selected zones.
- Thirty-nine validation and 43 test non-overlapping daily policy horizons.
- Model-level metrics use overlapping forecasts, reducing effective sample size.
- Hybrid-specific per-seed predictions were not saved.
- Rolling-origin outputs omit Transformer predictions, preventing hybrid rolling-origin reconstruction.
- The primary blend search is now declared, but it was reconstructed after the staged script hard-coded the same weights.
- The exploratory shortlist was not documented before test inspection.
- Zero-conflict resampling is degenerate because every observed primary-hybrid block has zero conflicts; unseen conflicts cannot be generated by bootstrap.
- Raw source data are external, so full end-to-end retraining was not performed during integration.
- Opportunity uses realized recorded load, not a counterfactual load response.
- The joint search considered 8,547 validation pairs, so its exploratory candidates are exposed to selection optimism.
- No additional untouched period is currently available; data-dependent promotion, per-seed hybrid evidence, and full-hybrid rolling-origin evidence are intentionally deferred.

## Recommended language

Use:

- “validation-selected probability hybrid”
- “offline safe shiftable-load opportunity”
- “zero observed test conflicts in this period”
- “point estimate slightly above; uncertainty intervals overlap”
- “test-ranked exploratory candidate”
- “validation-selected exploratory decision-aware candidate”
- “retrospective current-test diagnostic”

Avoid:

- “guaranteed safe”
- “verified savings”
- “decisively better”
- “best model” when referring to the test-ranked balanced candidate
- “new primary” or “validated replacement” for a decision-aware/window-aware challenger
- “calibrated” unless referring only to the reported diagnostics; no recalibration was applied
