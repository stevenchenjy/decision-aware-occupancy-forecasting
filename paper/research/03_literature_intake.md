# Literature Intake and Positioning Notes

> **Superseded positioning note.** The final manuscript is an offline,
> post-bin saved-output case study. Use the manuscript and final claim matrix
> for current wording; this note cannot support real-time, calibrated-risk,
> verified-control, or frozen-candidate claims.

**Last updated:** 2026-07-29  
**Verification rule:** every record below has a DOI or official proceedings
record. Metadata and publisher/official abstracts were reviewed; this is an
initial source corpus, not a claim that every full paper has been read in full.
Before an in-text citation carries a substantive claim, a human author should
read the cited full text and record the exact supported statement.

## Positioning in one sentence

This project is best positioned as an **empirical-conflict-cutoff, post-bin
empty-window recommendation evaluation with offline processed-load-proxy
accounting**.
It is neither an end-to-end decision-focused learning method nor a deployed
occupancy-based controller.

## Curated starting corpus

| Key | Verified source | Role in the paper | Reading status |
|---|---|---|---|
| `Luo2022` | Luo *et al.*, *Scientific Data*, 2022, DOI [10.1038/s41597-022-01257-x](https://doi.org/10.1038/s41597-022-01257-x) | Primary data provenance; the underlying three-year LBNL data release. | Metadata/abstract checked |
| `Hong2022` | Hong *et al.*, Dryad dataset, 2022, DOI [10.7941/D1N33Q](https://doi.org/10.7941/D1N33Q) | Cite the actual data package and availability path. | Official metadata checked |
| `Jin2021` | Jin *et al.*, *Energy and Buildings*, 2021, DOI [10.1016/j.enbuild.2021.111345](https://doi.org/10.1016/j.enbuild.2021.111345) | Foundational review of occupancy **forecasting**; supports application-specific time/spatial scales and robustness concerns. | Metadata/abstract checked |
| `CaballeroPena2024` | Caballero-Peña *et al.*, *Energy and Buildings*, 2024, DOI [10.1016/j.enbuild.2024.114230](https://doi.org/10.1016/j.enbuild.2024.114230) | Frames the connected data-acquisition, modeling, evaluation, and testing stages. | Metadata/abstract checked |
| `Li2024` | Li *et al.*, *Renewable and Sustainable Energy Reviews*, 2024, DOI [10.1016/j.rser.2024.114284](https://doi.org/10.1016/j.rser.2024.114284) | Current review for the broader occupancy-prediction landscape; not a source for a “first” claim. | Metadata/abstract checked |
| `Erickson2014` | Erickson *et al.*, *ACM TOSN*, 2014, DOI [10.1145/2594771](https://doi.org/10.1145/2594771) | Early occupancy-prediction-to-energy-management motivation. | DOI metadata checked |
| `LiDong2018` | Li and Dong, *Energy and Buildings*, 2018, DOI [10.1016/j.enbuild.2017.09.052](https://doi.org/10.1016/j.enbuild.2017.09.052) | Direct short-term commercial-building forecast comparison; motivates strong stochastic/ML baselines. | DOI metadata checked |
| `RyuMoon2016` | Ryu and Moon, *Building and Environment*, 2016, DOI [10.1016/j.buildenv.2016.06.039](https://doi.org/10.1016/j.buildenv.2016.06.039) | Prior environmental-sensor occupancy prediction; useful for feature-availability discussion. | Metadata/abstract checked |
| `Peng2018` | Peng *et al.*, *Applied Energy*, 2018, DOI [10.1016/j.apenergy.2017.12.002](https://doi.org/10.1016/j.apenergy.2017.12.002) | Closely related occupancy-prediction-based cooling control. Use to distinguish control outcomes from this project's offline proxy. | DOI metadata checked |
| `EsrafilianNajafabadi2022` | Esrafilian-Najafabadi and Haghighat, *Energy and Buildings*, 2022, DOI [10.1016/j.enbuild.2021.111808](https://doi.org/10.1016/j.enbuild.2021.111808) | Supports the premise that forecast accuracy alone need not represent HVAC control value. | DOI metadata checked |
| `Zhuang2022` | Zhuang *et al.*, *Building and Environment*, 2022, DOI [10.1016/j.buildenv.2022.109207](https://doi.org/10.1016/j.buildenv.2022.109207) | Nearby probabilistic/risk-aware ventilation work. It rules out an unsupported “first risk-aware” claim. | DOI metadata checked |
| `Wietzke2024` | Wietzke *et al.*, *Energy and Buildings*, 2024, DOI [10.1016/j.enbuild.2024.113968](https://doi.org/10.1016/j.enbuild.2024.113968) | Recent occupancy prediction coupled to an MPC setting; contrast the stronger control evidence it contains with ours. | Metadata/abstract checked |
| `Sun2023` | Sun *et al.*, *Building and Environment*, 2023, DOI [10.1016/j.buildenv.2023.110807](https://doi.org/10.1016/j.buildenv.2023.110807) | Recent Transformer occupancy-prediction comparator. | DOI metadata checked |
| `ElmachtoubGrigas2022` | Elmachtoub and Grigas, *Management Science*, 2022, DOI [10.1287/mnsc.2020.3922](https://doi.org/10.1287/mnsc.2020.3922) | Predict-then-optimize theory. Cite only to distinguish validation-based operating-policy selection from decision-loss training. | Metadata/abstract checked |
| `Wilder2019` | Wilder *et al.*, *AAAI*, 2019, DOI [10.1609/aaai.v33i01.33011658](https://doi.org/10.1609/aaai.v33i01.33011658) | Decision-focused learning background. The project does **not** implement this method. | Official abstract checked |
| `Cerqueira2020` | Cerqueira *et al.*, *Machine Learning*, 2020, DOI [10.1007/s10994-020-05910-7](https://doi.org/10.1007/s10994-020-05910-7) | Motivation for preserving time order and adding rolling temporal evaluation. | DOI metadata checked |
| `SaitoRehmsmeier2015` | Saito and Rehmsmeier, *PLOS ONE*, 2015, DOI [10.1371/journal.pone.0118432](https://doi.org/10.1371/journal.pone.0118432) | Justification for AUPRC alongside ROC-style discrimination metrics when the positive class is imbalanced. | DOI metadata checked |

## What this corpus says about the contribution

1. **The problem is established, not novel by itself.** Occupancy forecasting
   for building operation and control is an active and mature field.
2. **The manuscript's defensible contribution is evaluative.** It connects
   next-24-h Empty-class probability forecasts to a validation-selected policy
   with an empirical conflict cutoff and a stable-window requirement, then reports the
   resulting offline trade-off alongside forecast metrics.
3. **Related work has stronger control claims only when it evaluates a control
   system.** This repository does not have a counterfactual, energy simulator,
   comfort model, or intervention, so it must not inherit those claims.
4. **Do not overuse decision-focused terminology.** The code selects weights and
   thresholds using validation data; it does not train model parameters with a
   differentiable decision loss. “Decision-aware evaluation” or
   “risk-constrained operating-policy selection” is accurate; “decision-focused
   learning” is not.
5. **Do not claim priority without a systematic review.** The stable-window,
   risk-constrained combination may be distinctive, but the current literature
   intake is intentionally too small to prove a “first” claim.

## Immediate full-text reading queue

Read these before drafting the Introduction and Related Work, then record the
specific passages/claims that will be cited:

1. `Luo2022` and the Dryad metadata — data channels, timestamp provenance, and
   data-use citation.
2. `LiDong2018`, `Sun2023`, and `Jin2021` — fair baseline choices, forecast
   horizon/scale, and temporal validation expectations.
3. `Peng2018`, `EsrafilianNajafabadi2022`, `Zhuang2022`, and `Wietzke2024` —
   the boundary between forecast evaluation, risk-aware operation, and actual
   control/comfort/energy evidence.
4. `ElmachtoubGrigas2022` and `Wilder2019` — terminology guardrails for the
   decision-layer framing.

## Literature-search expansion plan

For a final Related Work section, perform a documented search in IEEE Xplore,
Scopus/Web of Science, and Google Scholar with the following concept blocks:

```text
("occupancy forecasting" OR "occupancy prediction") AND
("building energy" OR HVAC OR "demand flexibility") AND
(risk OR uncertainty OR "model predictive control" OR "stable window")
```

Screen for: office/commercial buildings; future prediction rather than detection
only; stated horizon and time split; baselines; decision/control outcome; and
availability of code/data. Record inclusion/exclusion and conflicts rather than
selecting only sources that support the intended contribution.
