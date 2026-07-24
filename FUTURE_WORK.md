# Future Work

The scriptable pipeline, hybrid integration, daily-block uncertainty, calibration diagnostics, and presentation figures are now implemented. Remaining priorities are:

The current no-additional-data phase is complete: the joint weight-threshold
surface, window-aware constraints, candidate freeze, retrospective diagnostics,
reproduction commands, claim boundaries, and future evaluation protocol are all
documented. Items below that require new predictions, raw data, or an untouched
period are deliberately deferred rather than approximated from the already-inspected
validation/test exports.

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

For the current professor-facing package, present the canonical result first and
the decision-aware/window-aware work as an exploratory appendix. If additional
data work resumes later, the first empirical priority is the frozen one-shot
evaluation protocol, followed by matched rolling-origin and per-seed evidence—not
further candidate search on the current test set.
