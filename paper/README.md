# IEEE Paper Workspace

## Public working-paper record

The [authored working paper](../docs/occupancy-forecasting-working-paper.pdf) supplied from Drive is now preserved in a separate [public research record](research-record/README.md), with a [research page](https://stevenchenjy.github.io/decision-aware-occupancy-forecasting/), citation metadata, provenance, and a versioned release. That PDF is an unchanged supplied artifact, not a rebuild of the anonymous source below. Its unfinished declaration and archive text is documented in the research record.

Public preservation of this offline research draft does not change the scientific verdict or establish a formal venue publication. The empirical requirements below continue to apply to prospective operational claims and any submission seeking those claims.

## Status

**Scientific verdict: requires empirical rerun.** The manuscript is structurally complete as an IEEE-style, offline post-bin case-study draft, but it is not cleared for submission as a prospective operational method.

The central contribution is a validation-selected saved-output evaluation that separates 388,032 overlapping forecast rows from 43 non-overlapping policy horizons and reports offline processed-load-proxy opportunity rather than energy savings. A midnight-labelled anchor is the completed '[00:00,00:15)' input bin, with effective availability at 00:15. The source is a cleaned release with unresolved raw timestamp/imputation provenance.

See [audits/final_self_audit.md](audits/final_self_audit.md), [audits/final_claim_matrix.md](audits/final_claim_matrix.md), and [audits/rerun_manifest.md](audits/rerun_manifest.md).

## Layout

- [manuscript/main.tex](manuscript/main.tex) — full IEEE-style source.
- [manuscript/sections](manuscript/sections) and [manuscript/tables](manuscript/tables) — evidence-bounded text and static tables.
- [manuscript/figures](manuscript/figures) — canonical-source figures.
- [audits](audits) — final integrity, citation, claim, rerun, and compile records.
- [scripts/generate_paper_figures.py](scripts/generate_paper_figures.py) — figure generator from canonical saved outputs.
- [submission](submission) — existing anonymous audit PDF and handoff; prospective operational submission remains on hold.
- [research-record](research-record) — supplied authored PDF provenance and public version history.

## Rebuild

    python3 paper/scripts/generate_paper_figures.py
    cd paper/manuscript
    ../tools/tectonic-0.17.0/tectonic --keep-intermediates --keep-logs --outdir build main.tex

The saved-output rebuild does not retrain models. Follow the empirical rerun manifest before upgrading the evidence verdict or releasing prospective operational claims. The separately identified public working-paper snapshot preserves the current evidence limits.
