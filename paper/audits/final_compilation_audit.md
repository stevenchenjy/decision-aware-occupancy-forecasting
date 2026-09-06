# Final Compilation and Visual Audit

**Audit date:** 2026-09-04 (float-placement fix; earlier scientific checks retained below)
**Manuscript status:** compiled IEEE-style anonymous case-study draft; external submission remains blocked by the empirical-rerun condition in the final self-audit.

## Build record

| Item | Result |
|---|---|
| Source | `paper/manuscript/main.tex` |
| Compiler | bundled Tectonic 0.17.0 |
| Command | `paper/tools/tectonic-0.17.0/tectonic --keep-intermediates --keep-logs --outdir build main.tex` from `paper/manuscript` |
| Exit status | 0 |
| Output | `paper/submission/occupancy_empty_window_ieee_post_bin_case_study.pdf` |
| PDF SHA-256 | `9d3f312eb6df6d7411a8caeb69c7d19cf1c8762de06dc1168007fe49a4888c3d` |
| Pages / paper size | 9 / US Letter (612 x 792 pt) |
| PDF copy check | byte-identical to `paper/manuscript/build/main.pdf` |

## Automated checks

- Full regression suite: `python3 -m pytest -q` completed with **46 passed in 16.70 s**.
- The final log contains no unresolved citation, reference, or undefined-reference warning.
- Citation linkage is 24 in-text keys, 24 BibTeX entries, zero unresolved, and zero orphaned; see `reference_audit_final.md`.
- The final figures were regenerated from canonical saved-output CSVs. The validation-selection stability artifact was generated from validation/processed inputs only.

## Visual inspection

### 2026-09-04 float-placement correction

Added `placeins` and `\FloatBarrier` immediately after the appendix input in
`main.tex`, preventing Table VII from floating past the declarations and
bibliography. No prose, results, figures, or citations were changed. Tectonic
completed successfully; the output remains nine pages. Pages 8 and 9 were
rendered at 140 dpi and visually inspected. Table VII is complete at the top of
page 9, followed by declarations and References, with no overlap or clipping in
the corrected table. The barrier leaves unused space in page 8's right column.
The table's final row ends at 168.20 pt from the top of page 9; References starts
at 376.97 pt. No overfull boxes or unresolved citation/reference warnings were
found. Tectonic still substitutes unavailable TU Times/Courier font shapes, so
this is not a verification of Overleaf/pdfLaTeX typography or exact pagination.
The fixed Overleaf ZIP includes the same source and all compilation assets.
Earlier regression/scientific checks below were not rerun for this layout-only fix.

### Earlier visual-review record (not a new full-document certification)

The final PDF was rendered at 180 dpi from the byte-identical manuscript build. All nine pages were reviewed, including the title/abstract page, table-and-figure-heavy result pages, appendix, data-availability block, and bibliography. No clipped text, overlap, missing figure, or unreadable table was observed. The indicator in Section~III-C was changed from `\mathbb{1}`---which had embedded as the unrelated glyph `⊮`---to `\mathbf{1}`. A character-level scan of the final PDF found no remaining `⊮`, replacement, private-use, or square-box glyphs.

Tectonic reports underfull box warnings, chiefly in narrow table cells and float-balanced pages. The rendered pages show no visible clipping or layout defect. There are no overfull horizontal boxes or unresolved-reference warnings.

## Release interpretation

This is a technically complete, visually checked IEEE-style manuscript build. It is **not** cleared for a prospective operational or energy-savings submission: raw/provenance-tagged input streams, corrected deep-model initialization, a locked environment, full retraining, and a later untouched evaluation remain mandatory. See `final_self_audit.md` and `rerun_manifest.md`.
