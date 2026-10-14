# Working paper and research record

**Validation-Selected Hybrid Occupancy Forecasting for Empty-Window Recommendations: An Offline Post-Bin Case Study**

**Junyu Chen** (The Storm King School) and **Chong Li** (Department of Electrical Engineering, Columbia University). Author names, order, and affiliations are transcribed from the supplied manuscript.

**Record version:** `research-record-v1`, October 14, 2026. This is the public record date, not a claim about an earlier publication or submission date.

[Read the paper](../../docs/occupancy-forecasting-working-paper.pdf) · [Research page](https://stevenchenjy.github.io/decision-aware-occupancy-forecasting/) · [Versioned release](https://github.com/stevenchenjy/decision-aware-occupancy-forecasting/releases/tag/research-record-v1) · [BibTeX](../../docs/citation.bib) · [CITATION.cff](../../CITATION.cff)

## Status and contribution

This working paper connects next-24-hour occupancy scores to recommendations for sustained empty intervals in a single-building, offline post-bin case study. A validation-selected blend combines a historical schedule, LightGBM, and a compact Transformer. The record connects the supplied manuscript to the saved predictions, analysis scripts, and the repository's scientific audit.

**Scientific audit verdict: requires empirical rerun.** This public research snapshot does not establish peer-review acceptance or a journal/conference publication. IEEE-style formatting identifies the document layout, not a venue or acceptance.

| Evidence scope | Reported result | Interpretation |
|---|---|---|
| 388,032 overlapping held-out forecast rows | Hybrid Empty AUPRC 0.8514; historical schedule 0.8497; LightGBM 0.8382 | Score discrimination on saved forecasts; paired contrasts cross zero. |
| 43 non-overlapping policy horizons | 259 recommended intervals, 0 observed camera-label conflicts, 14 label-safe windows | Observed labels in this test period; no prospective safety guarantee. |
| Processed HVAC-plus-lighting load | 490.1 kWh during hybrid recommendations subsequently labelled Empty | Offline load-proxy overlap, not measured energy savings or controllable capacity. |

The stored anchor `t` covers the completed input bin `[t, t + 15 min)` and becomes usable at `t + 15 min`. Source timestamp and imputation provenance remain unresolved. Deep-model construction preceded seed reset in the saved runs. Prospective operational, control, and energy claims require the work described in the [empirical rerun manifest](../audits/rerun_manifest.md).

## Which manuscript is being preserved

The [public authored PDF](../../docs/occupancy-forecasting-working-paper.pdf) is an unchanged copy of **Paper2.pdf** from the [user-specified Drive folder](https://drive.google.com/file/d/1e-E5qSp19_ASbkDfm-COwtmbHb0x29og/view), retrieved October 14, 2026. It has nine pages and SHA-256:

```text
9c4d28ba6abb11a5a6709c45d2b25302ee6284e2366963885dc5c0c3b82df425
```

The PDF metadata records a creation time of September 26, 2026. This is file provenance, not evidence of publication. The source Drive item was last modified October 5, 2026 (UTC).

The [existing anonymous PDF](../submission/occupancy_empty_window_ieee_post_bin_case_study.pdf), [LaTeX source](../manuscript/main.tex), and [earlier manuscript manifest](../audits/final_manuscript_manifest.md) remain a separate audit record. Their PDF hash is different. The authored Drive PDF is not claimed to have been rebuilt from the checked-in anonymous LaTeX. The two versions agree on the central results and evidence limits but differ in authorship and typesetting.

The supplied authored PDF still contains an anonymous-review declaration paragraph and a placeholder for a persistent archive URL. Those unfinished items are preserved as part of the supplied snapshot. Contributor roles, funding, competing interests, a manuscript reuse license, and any venue-specific declarations have not been inferred or completed. This record assigns no new reuse license.

## Follow the evidence

- [Reproduction instructions](../../REPRODUCING.md): regenerate downstream analysis from committed saved outputs. This is separate from retraining on provenance-tagged source streams.
- [Data and provenance](../../DATA.md): cleaned LBNL Building 59 release and the source-availability boundary.
- [Canonical forecast comparison](../../results/canonical_model_comparison.csv), [policy accounting](../../results/canonical_policy_10pct.csv), and [validation selection stability](../../results/validation_selection_stability.csv).
- [Final repository self-audit](../../reports/final_self_audit_2026-08-01.md) and [claim matrix](../audits/final_claim_matrix.md): authoritative limits on interpretation.
- [Machine-readable record](manifest.json) and [checksums](checksums.sha256): exact file identity and links between the supplied and existing manuscript artifacts.

## Cite and preserve a specific version

> Chen, J., & Li, C. (2026). *Validation-Selected Hybrid Occupancy Forecasting for Empty-Window Recommendations: An Offline Post-Bin Case Study*. Working paper, research-record-v1. https://github.com/stevenchenjy/decision-aware-occupancy-forecasting/releases/tag/research-record-v1

Use the release tag for a fixed research snapshot. The research page and default branch can evolve; a future revision should receive a new tag and manuscript hash. The root citation file exposes the manuscript as the preferred citation; its top-level software attribution identifies the repository maintainer rather than inferring code contributions for the paper's coauthor.

## Next dissemination steps

For a persistent scholarly archive, connect this repository in the author's Zenodo account, archive an eligible release with verified authorship and an explicitly chosen license, and add the issued DOI after verifying it. The [GitHub archive guide](https://docs.github.com/en/repositories/archiving-a-github-repository/referencing-and-citing-content) explains that workflow. A GitHub release and citation metadata do not themselves create a DOI.

The public research page includes a complete author-written abstract, bibliographic metadata, and a directly accessible searchable PDF following [Google Scholar's inclusion guidance](https://scholar.google.com/intl/en/scholar/inclusion.html). Search-engine or Scholar indexing is not established by deployment. Any formal preprint or venue submission remains a separate step, subject to the manuscript's scientific status and author declarations.
