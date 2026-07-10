# Validity Checklist

- [x] Raw UTC timestamps are converted to Pacific Time before generating hour/day features.
  - Raw LBNL timestamps are parsed as UTC and converted to `America/Los_Angeles`. Solar radiation peaks support this assumption.
- [x] Raw label semantics are confirmed: occupied = 1.
  - `occupied=1` is created when the maximum south-zone occupancy count in a 15-minute bin is greater than 0.
- [x] Empty-class evaluation uses Empty = 1.
  - Evaluation flips labels with `empty = 1 - occupied`; AUPRC, AUROC, F1, precision, and recall are reported for Empty.
- [x] Historical Average uses training split only.
  - Slot averages are computed from timestamps before the training boundary.
- [x] Historical Average never uses validation or test labels.
  - Validation/test labels are used only for threshold selection/evaluation.
- [x] Rolling features use shift-before-rolling: arr[anchor-window:anchor].
  - Rolling occupancy/count features exclude the current target and all future labels.
- [x] Missing values use causal ffill + 0.0.
  - Sensor/load missing values are forward-filled from past observations only; leading gaps use 0.0.
- [x] No interpolate or bfill is used.
  - A text search over notebook and result files finds no `interpolate` or `bfill` calls.
- [x] No future sensor values are used as prediction inputs.
  - Known future inputs are calendar/time features only.
- [x] HVAC, lighting, MELs, and total load are not used as model inputs.
  - These variables are excluded from the tabular/deep feature sets.
- [x] Load variables are used only for energy opportunity estimation.
  - Default opportunity uses `hvac_S + lig_S`; sensitivity scenarios are clearly labeled.
- [x] Train/validation/test split is chronological.
  - Splits follow local-time weekly boundaries.
- [x] There is at least a 24-hour gap between train/validation/test splits.
  - The measured train-validation and validation-test gaps are both 24.25 hours.
- [x] Thresholds are selected on validation set only.
  - Risk-constrained thresholds are chosen from validation daily threshold sweeps.
- [x] Test set is used only for final evaluation.
  - Test metrics are computed after fixed validation-selected thresholds are applied.

## Remaining Assumptions And Limitations

- The source documentation does not explicitly state timestamp timezone. The pipeline assumes raw timestamps are UTC because the solar-radiation peak becomes physically plausible after UTC-to-Pacific conversion.
- Safe shiftable-load opportunity is not verified energy savings. No counterfactual control model, simulator, or intervention data is available.
- Occupancy conflict rate is not a full thermal comfort metric. PMV/PPD, setpoint response, occupant feedback, and comfort constraints are not modeled.
- Results are limited to LBNL Building 59 selected south zones. Cross-zone validation is included, but cross-building generalization is not claimed.
- Threshold policies are offline recommendations. A full RL scheduler is not implemented because no simulator or counterfactual energy response model is available.
