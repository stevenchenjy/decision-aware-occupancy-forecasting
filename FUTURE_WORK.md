# Required Next Research Phase

The existing saved-output phase is complete, but its final verdict is **requires empirical rerun**. Do not spend the current test set on further candidate selection.

| Priority | Requirement | Why it comes first |
|---:|---|---|
| 1 | Obtain source streams with observation-end timestamps and per-value imputation lineage | Establish whether inputs were actually available at a decision boundary |
| 2 | Declare left/right bin convention and store observation-end, issue, target-start, and target-end times | Remove the 00:00-label ambiguity |
| 3 | Set deep seeds before construction; lock code, data hashes, and packages | Make retraining reproducible |
| 4 | Retrain base models; select weights/threshold only on training/validation | Rebuild the empirical evidence without current-test tuning |
| 5 | Evaluate once on a later untouched period or independent building | Test temporal/external validity |
| 6 | Fit calibration/conformal method on validation if probability/risk claims are needed | Support bounded uncertainty claims |
| 7 | Add staleness/missingness sensitivity for Wi-Fi and load proxy | Test sensor/proxy robustness |
| 8 | Use simulation or intervention with comfort/equipment constraints | Test energy and control claims rather than opportunity overlap |

The previously frozen decision-aware/window-aware candidates may be evaluated once in the new protocol, but must not be promoted using their historical test diagnostics.
