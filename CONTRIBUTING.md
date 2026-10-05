# Contributing / working conventions

## LaTeX notes (`notes/`)

- Edit either in this repo directly, or live in Overleaf — then sync with
  `./scripts/sync_overleaf.sh push` / `pull` (see `notes/README.md`).
- Add new sections as new files under `notes/sections/` and `\input` them from `main.tex`.
- Add references only to `bibliography.bib` at the repo root .
- Put every figure used in the notes under `notes/figures/`.

## Slides (`slides/`)

- The slides are PDFs (`slides/part1.pdf` … `part4.pdf`), exported from the authors' sources.
  Replace the PDF to update a part; pushing to `main` republishes GitHub Pages.

## Notebooks (`notebooks/`)

- Run `nbstripout --install` once per clone so committed notebooks never carry output cells
  (see `notebooks/README.md`).
- Name notebooks to match the section they support, e.g. `02-linear-algebra.ipynb` (one notebook per part).
- If a notebook produces a figure meant for the notes/slides, export it into
  `notes/figures/` rather than relying on the notebook's rendered output.

## General

- Small edits: commit directly. Larger restructuring: open a pull request so collaborators can
  review before it's merged (and, if relevant, pushed to Overleaf).
- Keep `main` deployable: CI compiles the notes on every push — a red
  build means something doesn't compile/render for everyone else either.
