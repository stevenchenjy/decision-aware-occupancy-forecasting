# Final Compilation and Visual Audit

**Audit date:** 2026-08-01  
**Manuscript status:** compiled IEEE-style anonymous case-study draft; external submission remains blocked by the empirical-rerun condition in the final self-audit.

## Build record

| Item | Result |
|---|---|
| Source | `paper/manuscript/main.tex` |
| Compiler | bundled Tectonic 0.17.0 |
| Command | `paper/tools/tectonic-0.17.0/tectonic --keep-intermediates --keep-logs --outdir build main.tex` from `paper/manuscript` |
| Exit status | 0 |
| Output | `paper/submission/occupancy_empty_window_ieee_post_bin_case_study.pdf` |
| PDF SHA-256 | `74ad6cbf7c9ad7f408ebcc7b4ffe08d694df425e651e7315fb48308b2bf35da2` |
| Pages / paper size | 9 / US Letter (612 x 792 pt) |
| PDF copy check | byte-identical to `paper/manuscript/build/main.pdf` |

## Automated checks

- Full regression suite: `python3 -m pytest -q` completed with **46 passed in 21.66 s**.
- The final log contains no unresolved citation, reference, or undefined-reference warning.
- Citation linkage is 24 in-text keys, 24 BibTeX entries, zero unresolved, and zero orphaned; see `reference_audit_final.md`.
- The final figures were regenerated from canonical saved-output CSVs. The validation-selection stability artifact was generated from validation/processed inputs only.

## Visual inspection

The final PDF was rendered at 150 dpi from the delivered submission copy. All nine pages were reviewed, including the title/abstract page, table-and-figure-heavy result page, appendix, data-availability block, and bibliography. No clipped text, overlap, missing figure, unreadable table, or broken glyph was observed.

Tectonic reports two output-routine vertical-box notices (19.83 pt and 0.66 pt) and font-shape substitutions for Times-like fonts. The rendered pages show no visible clipping or layout defect. There are no overfull horizontal boxes or unresolved-reference warnings.

## Release interpretation

This is a technically complete, visually checked IEEE-style manuscript build. It is **not** cleared for a prospective operational or energy-savings submission: raw/provenance-tagged input streams, corrected deep-model initialization, a locked environment, full retraining, and a later untouched evaluation remain mandatory. See `final_self_audit.md` and `rerun_manifest.md`.
