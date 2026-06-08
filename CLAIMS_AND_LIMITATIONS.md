# Claims And Limitations

This document defines what the current repository supports and what it does not support. Use it when writing slides, emails, abstracts, or paper drafts.

## Supported Claims

The current repository supports these claims:

- The project evaluates day-ahead occupancy forecasting for LBNL Building 59 selected south zones.
- Occupancy streams are aligned to 15-minute intervals and converted to local Pacific time before generating calendar features.
- Empty is evaluated as the positive class for recommendation-oriented metrics.
- Historical Average, LightGBM, Random Forest, Transformer, and DLinear are evaluated on a chronological train/validation/test split.
- The pipeline uses validation-selected Empty probability thresholds and held-out test evaluation.
- The decision layer evaluates stable empty-window recommendations under occupancy-conflict constraints.
- The 10% validation-selected LightGBM policy reports a 4.15% test occupancy-conflict rate and 493.9 kWh safe shiftable-load opportunity on test daily schedules.
- Safe shiftable-load opportunity is computed only for recommended intervals that were actually empty.
- Default opportunity uses `hvac_S + lig_S` as a proxy controllable load and applies `kWh = kW * 0.25` for each 15-minute interval.
- Leakage checks indicate chronological splitting, 24.25-hour split gaps, train-only Historical Average, shifted rolling features, causal forward-fill, future-sensor exclusion, and load-variable exclusion from model inputs.
- Reported results apply to the recorded LBNL Building 59 selected-zone data and the documented experimental setup.

Preferred wording:

- "decision-aware evaluation framework"
- "risk-constrained recommendation post-processing"
- "offline safe shiftable-load opportunity"
- "occupancy-conflict rate"
- "LBNL Building 59 selected south zones"

## Unsupported Claims

Do not claim the following from the current repository:

- Verified energy savings.
- Deployed building-control performance.
- Real BMS intervention results.
- Occupant comfort preservation.
- Thermal comfort compliance.
- Carbon emissions reduction.
- A learned decision-aware loss or decision-aware training objective.
- Reinforcement learning scheduler performance.
- Generalization to all buildings, all zones, or all seasons.
- Cross-building validation.
- Causal effect of recommendation on building energy consumption.
- Production readiness, monitoring, or real-time control reliability.

Avoid wording such as:

- "verified savings"
- "proven deployment benefits"
- "decision-aware learning"
- "generalizes across buildings"
- "safe HVAC control"
- "occupant comfort guaranteed"

Use this instead:

- "offline opportunity estimate"
- "evaluation on held-out LBNL Building 59 selected-zone schedules"
- "decision-aware threshold evaluation"
- "safe opportunity under recorded occupancy labels"
- "future work should evaluate counterfactual savings and deployment constraints"

## Current Limitations

- Single-building selected-zone scope.
- Main recommendation test set contains 43 non-overlapping daily schedules.
- Model-level metrics use overlapping rolling forecast intervals.
- The raw timestamp timezone is not explicitly stated in the source documentation; UTC-to-Pacific conversion is supported by solar-radiation timing.
- Energy opportunity uses realized recorded loads and is not counterfactual savings.
- No thermal-comfort model, occupant-response model, or BMS intervention data is included.
- Transformer and DLinear baselines are exploratory and lightly tuned.
- Threshold policies are selected on validation data, but risk estimates remain fragile because validation/test daily blocks are limited.
- Raw data is not committed, so full reruns require external Dryad data setup.

## Future Work

Future work may include:

- True decision-aware training objective with false-empty and missed-opportunity penalties.
- Calibrated uncertainty or conformal risk control for threshold selection.
- Cross-zone and cross-building validation.
- Counterfactual energy simulation using EnergyPlus, Sinergym, or a comparable simulator.
- Thermal-comfort constraints and occupant-response modeling.
- Carbon-intensity-aware opportunity estimation.
- Real deployment study with BMS integration and monitoring.
- Fairly tuned advanced forecasting baselines such as TFT or PatchTST.

These items are not required for the current professor-review package, but they are important for stronger paper or deployment claims.
