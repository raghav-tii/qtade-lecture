# `notes/` — LaTeX lecture notes

## Files

- `main.tex` — top-level document; sets the document class, includes `preamble.tex`, sets the
  title-page metadata, and `\input`s each file under `sections/`.
- `lecturenotes.cls` — the [`lecturenotes`](https://vhbelvadi.github.io/LaTeX-lecture-notes-class/)
  document class (v3.2), vendored here so the build is self-contained (no local TeX tree install
  needed). It provides the title page, header/footer styling, and theorem-like environments
  (`theorem`, `lemma`, `proposition`, `corollary`, `definition`, `example`, `remark`, `exercise`,
  `claim`, `conjecture`, `fact`, `problem`, `notation`) — don't redefine those in `preamble.tex`.
  **It requires LuaLaTeX** (it uses `unicode-math` + the `kpfonts-otf` OpenType fonts, and drops
  `inputenc`/`fontenc` support).
- `preamble.tex` — extra packages and macros not already provided by the class (`graphicx`,
  `cleveref`, `natbib`, tikz libraries, tensor-network notation macros).
- `sections/` — one `.tex` file per section of the notes, mirroring the four-part agenda in
  `slides/slides.qmd`. Add new sections here and `\input` them from `main.tex`.
- `figures/` — figures used in the notes.

The bibliography is shared with the slides and lives at the repo root: `../bibliography.bib`
(see the root `README.md`).

## Building locally

This document requires **LuaLaTeX** (not pdfLaTeX):

```bash
cd notes
latexmk -lualatex main.tex
```

(`latexmk` will pick up `../bibliography.bib` via the `\bibliography{../bibliography}` in
`main.tex` — no extra configuration needed.)

CI does this automatically on every push (see `.github/workflows/build-notes.yml`, which passes
`latexmk_use_lualatex: true`).

## Editing via Overleaf

This whole repository is linked to a single Overleaf project — see the root `README.md` for
setup and the push/pull workflow. Overleaf will show every file in the repo (slides, notebooks,
CI config, etc.), not just `notes/`; that's an accepted tradeoff for keeping a single sync
target. Just point Overleaf's "Main document" setting at `notes/main.tex` (Overleaf → Menu →
Settings → Main document) so it compiles the right file. Also set the "Compiler" setting to
**LuaLaTeX** (Overleaf → Menu → Settings → Compiler) — required by `lecturenotes.cls`.
