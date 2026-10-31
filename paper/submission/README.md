# Submission Handoff Status

The [public research record](../research-record/README.md) now preserves a separate authored manuscript supplied from Drive. The PDF in this directory remains the earlier anonymous audit build. Public preservation of a working draft does not satisfy the empirical requirements below or constitute a venue submission.

## Author-reported venue status

Junyu Chen reports that the manuscript has been submitted to ACM BuildSys and a decision is pending (October 30, 2026). No acceptance is claimed. The year, track, and submission receipt have not been established in this repository. The scientific limits and prospective-rerun requirements below remain unchanged.

## Scientific release status

**Hold external submission as a prospective operational paper. Verdict: requires empirical rerun.**

The final generic IEEE-style, evidence-bounded offline post-bin case-study PDF is `occupancy_empty_window_ieee_post_bin_case_study.pdf`. The older `occupancy_empty_window_ieee_manuscript.pdf` is historical and cannot override the scientific blockers.

## Completed audit work

- Canonical saved-output calculations were regenerated and independently reconciled.
- Timing convention, score terminology, model labels, scope separation, figures, tables, citations, and supporting documents were corrected.
- Validation-only stability diagnostics were added.
- Canonical and exploratory-search tests were rerun after code corrections.

## Blocking empirical work before release

1. Obtain raw/provenance-tagged streams, observation-end timestamps, source timezone confirmation, and imputation lineage.
2. Declare/test bin timing; preserve observation-end, issue, and target interval fields.
3. Correct deep-model seed initialization before construction and lock data/software/hardware environment.
4. Fully retrain and select without using the historical test exports.
5. Evaluate the frozen protocol once on a later untouched period or independent building.
6. Add simulation/intervention evidence before any energy/control claim.

The exact next step is in [../audits/rerun_manifest.md](../audits/rerun_manifest.md). After that rerun, rebuild with the venue template, insert author/archive metadata, perform the venue PDF check, and update the manifest.
