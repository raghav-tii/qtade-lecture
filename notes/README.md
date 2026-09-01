# `notes/` — LaTeX lecture notes

## Files

- `main.tex` — top-level document; sets the document class, includes `preamble.tex`, and
  `\input`s each file under `sections/`.
- `preamble.tex` — shared packages, macros, theorem environments, tensor-network TikZ macros, etc.
- `sections/` — one `.tex` file per section of the notes. Add new sections here and `\input`
  them from `main.tex`.
- `figures/` — figures used in the notes.

The bibliography is shared with the slides and lives at the repo root: `../bibliography.bib`
(see the root `README.md`).

## Building locally

Any standard LaTeX toolchain works, e.g.:

```bash
cd notes
latexmk -pdf main.tex
```

(`latexmk` will pick up `../bibliography.bib` via the `\bibliography{../bibliography}` in
`main.tex` — no extra configuration needed.)

CI does this automatically on every push (see `.github/workflows/build-notes.yml`).

## Editing via Overleaf

This whole repository is linked to a single Overleaf project — see the root `README.md` for
setup and the push/pull workflow. Overleaf will show every file in the repo (slides, notebooks,
CI config, etc.), not just `notes/`; that's an accepted tradeoff for keeping a single sync
target. Just point Overleaf's "Main document" setting at `notes/main.tex` (Overleaf → Menu →
Settings → Main document) so it compiles the right file.
