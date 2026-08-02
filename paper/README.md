# IEEE Paper Workspace

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
- [submission](submission) — final artifact only after the empirical rerun condition is satisfied.

## Rebuild

    python3 paper/scripts/generate_paper_figures.py
    cd paper/manuscript
    ../tools/tectonic-0.17.0/tectonic --keep-intermediates --keep-logs --outdir build main.tex

The saved-output rebuild does not retrain models. Follow the empirical rerun manifest before external release.
