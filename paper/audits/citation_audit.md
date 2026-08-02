# Citation and Reference Audit

> **Superseded for final release by [reference_audit_final.md](reference_audit_final.md).** This historical audit remains useful for metadata evidence, but its DLinear implementation wording was narrowed in the final manuscript.

**Audit date:** 2026-07-29  
**Target style:** IEEE numeric citations via `IEEEtran` and `IEEEtran.bst`  
**Verdict:** PASS for metadata, citation linkage, and manuscript scope.

## Linkage and metadata checks

| Check | Result |
|---|---:|
| In-text citation keys | 24 |
| Bibliography entries | 24 |
| Unresolved in-text keys | 0 |
| Orphan bibliography entries | 0 |
| DOI-bearing entries | 22 |
| DOI metadata verified by content negotiation | 22 |
| Official proceedings entries without DOI | 2 (`Ke2017`, `Vaswani2017`) |
| Self-citations | 0 |

All 17 original DOI records and the additions for building flexibility, operational HVAC evaluation, DLinear, and random forests were checked against DOI metadata. The two proceedings records use the official NeurIPS proceedings metadata. The final BibTeX pass succeeded under `IEEEtran.bst`.

## Corrections made

| Entry | Correction |
|---|---|
| `Hong2022` | Rendered as `Dryad Dataset, ver. 6` after DataCite metadata verification. |
| `Erickson2014` | Rendered with `Art. no. 42, 28 pp.` rather than an ambiguous page range. |
| Methods corpus | Added original-method references for LightGBM, random forests, Transformer, and DLinear. |
| Flexibility/control boundary | Added Chen, Junker, and Lin so the paper can distinguish flexibility terminology and field/system evidence from the present offline analysis. |

## Claim-faithfulness controls

- Reviews are used for literature framing, not priority claims.
- Zhuang et al. are cited to prevent a false ``first risk-aware'' claim.
- Wietzke et al. are described as simulation/MPC-related evidence, not a field deployment.
- Decision-focused learning citations are used only to distinguish the validation-selected policy from downstream-loss training.
- Chen and Junker support flexibility terminology only; neither is used to validate the paper's offline 490.1-kWh calculation.
- No citation is used to infer verified savings, comfort, deployment, or generalization.

## Remaining human-only check

A full Retraction Watch/Crossmark screen was not performed. The bibliography does not claim that all sources were retraction-screened. Authors should perform any venue- or institution-specific integrity scan immediately before submission.
