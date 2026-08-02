# Final Reference Audit

**Audit date:** 2026-08-01  
**Verdict:** metadata/linkage pass; two model-description contexts corrected.

## Linkage result

| Check | Result |
|---|---:|
| Unique in-text citation keys | 24 |
| Bibliography entries | 24 |
| Unresolved keys | 0 |
| Orphan entries | 0 |
| DOI-bearing entries verified through Crossref | 22 / 22 |
| Dataset record verified through Dryad/DataCite | 1 / 1 |
| Non-DOI proceedings verified through official records | 2 / 2 |
| Metadata corrections required | 0 |

## Claim-faithfulness changes

| Citation | Prior risk | Final disposition |
|---|---|---|
| Zeng2023 | Legacy label 'DLinear' could imply the implemented model reproduces decomposition-based DLinear. | Paper explicitly calls implementation a direct linear occupancy baseline and cites Zeng et al. only as related context for linear time-series baselines. |
| Vaswani2017 | 'Original Transformer' table label could imply a full encoder-decoder reproduction. | Paper calls it a compact encoder-only Transformer and uses Vaswani et al. as architectural background. |
| Luo2022 / Hong2022 | Source might be read as raw/prospectively causal data. | Paper identifies cleaned release and warns that source imputation/timestamp provenance are unresolved. |
| Control/flexibility studies | Could be used to infer intervention efficacy for the current calculation. | All contexts distinguish this offline proxy from simulation, field control, savings, and comfort evidence. |

## Verified reference inventory

| Key | Verification outcome |
|---|---|
| Luo2022 | Verified; Scientific Data dataset article and cleaning context. |
| Hong2022 | Verified; Dryad Dataset, version 6. |
| Jin2021; CaballeroPena2024; Li2024 | Verified; occupancy/review context. |
| Erickson2014; LiDong2018; RyuMoon2016; Sun2023 | Verified; occupancy modeling context. |
| Ke2017; Breiman2001; Vaswani2017; Zeng2023 | Verified; model-method context, with narrowed implementation claims above. |
| Chen2018; Junker2018; Peng2018; EsrafilianNajafabadi2022; Zhuang2022; Wietzke2024; Lin2023 | Verified; flexibility/control context, not internal result validation. |
| Wilder2019; ElmachtoubGrigas2022 | Verified; decision-focused-learning contrast. |
| Cerqueira2020 | Verified; temporal evaluation context. |
| SaitoRehmsmeier2015 | Verified; precision-recall metric context. |

## Remaining pre-submission reference action

No Crossmark or Retraction Watch screen was performed in this repository audit. Before external submission, authors should perform the venue/institution-required integrity screen and recheck the final bibliography against the venue’s template.
