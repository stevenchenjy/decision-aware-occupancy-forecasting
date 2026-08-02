# Experiment and Reproducibility Gap Register

> **Superseded workspace note.** The current authoritative next step is a
> provenance-tagged empirical rerun, with seed setting before model
> construction and new validation selection. Historical frozen
> decision/window candidates cannot be promoted after that retraining.

| Priority | Gap | Effect on paper | Recommended resolution |
|---:|---|---|---|
| P0 | No genuinely new untouched evaluation period for the exploratory challengers. | Prevents promotion of decision-aware/window-aware results. | Keep them secondary; execute the frozen protocol only after acquiring new data. |
| P0 | Opportunity uses realized HVAC+lighting load, not a controlled counterfactual. | Prevents savings, comfort, or control-effect claims. | Rename consistently as opportunity; add simulation/intervention only for a stronger operations paper. |
| P0 | Historical test-firewall provenance is incomplete: primary weights were originally hard-coded and later reconstructed through a declared validation search; all current test diagnostics are now inspected. | Current evidence is retrospective rather than fully confirmatory. | Be explicit in limitations and obtain one locked future period before a confirmatory claim. |
| P1 | Single building and short policy test window (43 days). | Limits external validity and rare-conflict inference. | Add buildings, seasons, and longer future data. |
| P1 | The all-overlap AUPRC headline and daily-block bootstrap have different estimands. | An interval around the daily-horizon AUPRC is not an interval around the 388,032-row headline AUPRC. | Label scopes separately and add blocked/horizon-aware paired inference if the overlap-level metric is central. |
| P1 | Zero observed conflicts cover 259 intervals but only 14 recommended windows. | Bootstrap conflict intervals are degenerate; finite-sample risk remains uncertain. | Report denominators and conservative bounds; validate on more future periods and consider calibration/conformal risk control. |
| P1 | Hybrid per-seed component predictions are absent. | Cannot distinguish seed variance from ensemble gain. | Save aligned per-seed prediction exports and report within-seed blends. |
| P1 | Rolling-origin outputs omit Transformer predictions. | Hybrid temporal robustness is incomplete. | Run matched rolling-origin retraining/evaluation for every component. |
| P1 | WiFi features have 81.57% missingness before post-import row-order forward-fill. | Source provenance and operational staleness are unresolved. | Report missingness; run calendar-only/history-only/sensor-group ablations and a maximum-staleness sensitivity analysis. |
| P1 | Source timezone is inferred as UTC then converted to Pacific, but the source metadata needs explicit confirmation. | Calendar features and reported local times depend on this provenance assumption. | Obtain and archive a source-author/official-metadata confirmation before final submission. |
| P1 | Raw Dryad data and trained checkpoints are absent locally. | Full end-to-end training is not verified in this workspace. | Download public raw data, checksum it, record environment, and rerun from a clean environment. |
| P2 | Dependencies use broad constraints rather than a lock file. | Exact environment portability is weaker. | Freeze a tested Python environment (e.g., lock file/container) and record package hashes. |
| P2 | Local Python is 3.13 while project documentation supports 3.10--3.12. | Full retraining may not be reproducible locally. | Use the documented environment before final reproduction. |
| P2 | No venue or page budget selected. | IEEE template and figure count cannot be frozen. | Select venue before prose drafting; replace generic IEEEtran scaffold with venue template. |
| P1 | Legacy illustrative-output path chooses its display model by held-out test AUPRC; one “false-positive” day has zero conflicts. | Example figures are not valid inferential/pedagogical manuscript evidence. | Exclude them now; later regenerate from a pre-specified model and deterministic, correctly labeled case-selection rule. |

## Minimum package for a cautious submission now

- all canonical tables and figures reproduced from saved inputs;
- a clear one-building case-study framing;
- explicit limitation and data-availability statements;
- a verified literature matrix and a venue-specific template;
- no revision of any selection decision after consulting current test diagnostics.
