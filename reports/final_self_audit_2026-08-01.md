# Final Repository Self-Audit — 2026-08-01

**Verdict: requires empirical rerun.**

This report is the repository-level entry point for the final audit. The complete auditable record is [paper/audits/final_self_audit.md](../paper/audits/final_self_audit.md).

## Bottom line

The saved results regenerate consistently and now align with the manuscript and documents as an **offline, post-bin** analysis. A left-labelled 00:00 anchor aggregates the completed '[00:00,00:15)' input bin and is treated as effectively available at 00:15. The canonical AUPRC 0.8514 is computed over 388,032 overlapping forecast rows; the 43 horizons apply only to fixed policy accounting. The 490.1 kWh quantity is a processed load-proxy overlap, not energy savings.

The key empirical blockers are source-side imputation/timestamp provenance and deep-model seed initialization. See the [rerun manifest](../paper/audits/rerun_manifest.md) for the exact controlled next experiment and [final claim matrix](../paper/audits/final_claim_matrix.md) for allowable wording.

Earlier reports remain historical records. Where they call the procedure causal, leakage-safe end-to-end, midnight-issued, or submission-ready, this report and the final self-audit supersede that wording.
