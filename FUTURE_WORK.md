# Future Work

The scriptable pipeline, hybrid integration, daily-block uncertainty, calibration diagnostics, and presentation figures are now implemented. Remaining priorities are:

| Priority | Improvement | Missing requirement | Benefit |
|---:|---|---|---|
| 1 | Hybrid multiple-seed robustness | Save aligned validation/test component predictions for every seed, then blend within seed | Separates ensemble gain from seed luck |
| 2 | Hybrid rolling-origin validation | Retrain Transformer and tabular components on matched rolling folds | Tests temporal stability of the complete primary model |
| 3 | Nested or pre-registered ensemble selection | Define architecture and weight grid before final test access; ideally use nested temporal validation | Removes residual researcher-degrees-of-freedom concern |
| 4 | Calibrated/conformal risk control | Fit calibration or conformal method on validation only | Gives more defensible finite-sample risk statements |
| 5 | Longer and cross-building evaluation | Additional zones, buildings, seasons, and years | Tests external validity and rare conflicts |
| 6 | Counterfactual energy evaluation | EnergyPlus/Sinergym model or intervention data | Converts opportunity into defensible savings estimates |
| 7 | Comfort and occupant-response constraints | Setpoint response, PMV/PPD, feedback, and control limits | Evaluates operational acceptability |
| 8 | True decision-aware training | Predeclared false-empty/missed-opportunity loss and matched tuning budget | Aligns model training with the policy objective |
| 9 | Model serialization and inference contract | Versioned weights, feature schema, environment, and monitoring plan | Supports repeatable deployment research |
| 10 | Test-set quarantine workflow | Immutable test artifact and automated selection audit | Prevents accidental test-guided iteration |

The immediate professor-facing next step should be hybrid rolling-origin and per-seed evidence, not further test-set candidate search.
