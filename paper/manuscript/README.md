# Manuscript Build Notes

'main.tex' is a generic IEEE conference-format manuscript with an anonymous author block. It is an evidence-bounded offline post-bin case-study draft; the final scientific audit verdict is **requires empirical rerun** for prospective operational claims. Compile from this directory so that section, table, figure, and bibliography paths resolve consistently.

```bash
../tools/tectonic-0.17.0/tectonic --keep-intermediates --keep-logs --outdir build main.tex
pdfinfo build/main.pdf
mkdir -p build/rendered
pdftoppm -png -r 200 build/main.pdf build/rendered/page
```

Tectonic runs BibTeX automatically. A full TeX Live build using 'latexmk' is also acceptable after replacing the exact target-venue template. Do not submit with the anonymous placeholder block, generic conference class, or pending data/code archival placeholder. More importantly, do not represent this draft as prospective operational evidence before completing [../audits/rerun_manifest.md](../audits/rerun_manifest.md).

The document uses:

- `sections/` for paper body;
- `tables/` for static canonical tables;
- `figures/` for source-frozen PNGs;
- `appendices/` for status-controlled extended material; and
- `references.bib` for DOI/proceedings-verified references.
