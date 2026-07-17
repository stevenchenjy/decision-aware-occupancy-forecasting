# Next Phase Recommendation

## Material Passport

- Origin Skill: academic-research-suite / experiment-agent
- Origin Mode: plan/validate
- Verification Status: ANALYZED
- Recommendation Date: 2026-07-17
- Depends On: `reports/future_untouched_evaluation_protocol.md`

## Recommended next phase

Run a **one-shot, frozen-candidate evaluation on a genuinely untouched chronological period**. Do not perform another search on the current validation or test exports.

The window-aware objective and candidate freeze have already been completed. Repeating or enlarging either search would add optimization against an already-inspected sample. The next defensible uncertainty reduction comes from new temporal evidence.

## Research question

On a new chronological period that was not inspected during training, model selection, policy selection, diagnostics, or example selection, does the frozen window-aware challenger increase safe load-proxy opportunity relative to the canonical primary while satisfying every pre-specified forecasting, interval-safety, window-safety, coverage, influence, and uncertainty gate?

## Why this is the correct next step

- The canonical and exploratory weights and thresholds are already fixed.
- The current test period has been used for fixed-candidate evaluation and retrospective window diagnostics; it cannot confirm another adaptation.
- The repository already exhausted the defensible no-raw-data optimization supported by its two saved prediction exports.
- A new period tests temporal transportability and the operational window constraint directly, rather than rewarding another objective choice on the same sample.

## Exact inputs required

Before opening outcomes, lock and hash:

1. A new chronological period with complete, non-overlapping midnight-anchored 96-step horizons.
2. Aligned rolling probability exports for Historical Average/Seasonal, LightGBM, and Original Transformer, using the already-trained/frozen model definitions and the same probability semantics.
3. `actual_occupied` and `actual_empty_positive` labels aligned by anchor time, target time, and horizon step.
4. Timestamp-aligned `hvac_S` and `lig_S` streams, or an explicitly versioned equivalent load proxy.
5. Period boundaries, timezone, missingness report, feature-availability policy, and provenance hashes.
6. The frozen candidate registry from `reports/future_untouched_evaluation_protocol.md` and `results/window_aware_selected_candidates.csv`.
7. Sufficient day identifiers to support paired day-level metrics, leave-one-day-out influence checks, and daily-block uncertainty.

The current repository contains no serialized fitted models. Therefore, without a collaborator-provided saved-output bundle, producing item 2 requires reconstructing the prediction pipeline and access to raw/new-period features.

## What can be completed without raw data

Already complete without raw data:

- validation-only joint and window-aware searches;
- frozen candidate weights, thresholds, selection rules, and promotion gates;
- current-period retrospective diagnostics;
- the future evaluation protocol;
- an input schema, hashing manifest design, evaluation code skeleton, and synthetic-fixture tests.

The actual next-phase empirical evaluation can also avoid Dryad specifically if a collaborator supplies a genuinely new, locked saved-output package with aligned component probabilities, labels, and load streams. It cannot be executed from the files currently in this repository alone.

## What remains blocked

- Acquiring a genuinely untouched period.
- Generating frozen base-model probabilities for that period without saved model checkpoints.
- Hybrid rolling-origin validation, because saved fold-level Transformer probabilities are absent.
- Hybrid per-seed analysis, because aligned per-seed component probabilities are absent.
- Full retraining and raw-pipeline verification, because the raw package is absent and the trained model objects are not committed.
- Any claim of measured savings, comfort preservation, causal effect, or guaranteed future safety.

## Success criteria

Use the gates already fixed in `reports/future_untouched_evaluation_protocol.md`. The primary window-aware challenger is eligible for promotion only if all hold:

1. Safe opportunity is at least 10% higher than canonical and exceeds the duration-scaled absolute threshold of `1.16 kWh × evaluation days`.
2. Interval conflict rate is `<=10%`.
3. Fully safe window rate is `>=85%`.
4. Empty AUPRC is at least 99% of canonical on the same new period.
5. Coverage is at least 80% of canonical and at least 2% absolute, with at least 10 recommended windows.
6. The safe-opportunity gain remains positive after removing each of the two highest-load gain days.
7. The lower bound of the paired daily-block 95% interval for the opportunity difference is above zero.

Report all gates even if an early gate fails. Retain the canonical primary unless every gate passes.

## Stop conditions

Stop without evaluation or promotion if any of the following occurs:

- any date, label, load outcome, qualitative example, or candidate outcome from the proposed period was previously inspected;
- the period overlaps existing validation/test dates or a training-selection period;
- prediction keys, labels, timezone, or load timestamps do not align exactly;
- any candidate weight, threshold, minimum-window rule, metric definition, tie-break, or gate is changed after outcomes are opened;
- fewer than 10 complete recommended windows are available for the challenger;
- a requested analysis would rank or retune candidates using the existing current test;
- the required probability export cannot be generated without retraining and raw/new-period data remain unavailable.

If a gate fails after valid evaluation, publish the failure and stop promotion; do not tune a replacement on that period.

## Files that would be created

Only after a new input package is locked:

- `reports/untouched_evaluation_input_audit.md`
- `results/untouched_input_manifest.csv`
- `results/untouched_frozen_candidate_metrics.csv`
- `results/untouched_daily_paired_metrics.csv`
- `results/untouched_day_influence.csv`
- `results/untouched_daily_block_uncertainty.csv`
- `results/untouched_promotion_gates.csv`
- `figures/untouched_candidate_comparison.png`
- `figures/untouched_daily_opportunity_difference.png`
- `reports/untouched_evaluation_report.md`
- tests that reject overlapping dates, changed candidate definitions, test-ranked selection, and incomplete gate reporting

No file should be named or described as an untouched result until the data-firewall audit passes.

