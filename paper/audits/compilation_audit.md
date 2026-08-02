# Compilation and Visual Audit

> **Superseded by the final post-revision compilation record.** This 2026-07-29 build predates the timing, model-name, selection-stability, and evidence-boundary revisions. See [final_self_audit.md](final_self_audit.md).

**Audit date:** 2026-07-29  
**Verdict:** PASS for the generic anonymous IEEE-style draft; target-venue packaging remains an author action.

## Build record

| Item | Result |
|---|---|
| Engine | Tectonic 0.17.0 with automatic BibTeX |
| Command | `tectonic --keep-intermediates --keep-logs --outdir build main.tex` from `paper/manuscript/` |
| Output | `paper/submission/occupancy_empty_window_ieee_manuscript.pdf` |
| PDF | 8 letter-size pages, PDF 1.5, 349,751 bytes |
| SHA-256 | `c939db79c0bd2847aba7e852e398f50c4c9631f04711461f5a4ff1f797bc0992` |
| Bibliography | BibTeX completed; citation linkage independently checked as 24 cited keys / 24 entries / 0 unresolved / 0 orphaned |
| Render check | All 8 pages rendered at 200 dpi and visually inspected |

## Layout result

- The title, abstract, equations, six tables, two figures, appendix, and two-column bibliography render without clipping or overlap.
- The expanded comparison table and references now share a balanced final page; the former nearly empty final-column layout is removed.
- Figure 2 has explicit right-side annotation padding so its confidence-interval labels are not edge-clipped.

## Nonfatal local-toolchain notes

- Tectonic reports underfull boxes in narrow table cells and a 1.132-pt final-page `vbox` warning from bibliography balancing. The 200-dpi rendered pages show no clipping, overlap, or visible layout defect.
- Tectonic's XeTeX path reports legacy Times font-shape substitutions. This does not affect the inspected layout, but the final author build must use the exact TeX toolchain required by the selected IEEE venue and then pass the IEEE PDF Checker.
- No undefined control sequence, unresolved citation, unresolved reference, or overfull horizontal box was found in the final log.
