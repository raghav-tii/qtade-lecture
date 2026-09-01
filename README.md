# Tensor Network Algorithms for Fluid Dynamics — QTADE School, Bilbao

Shared repository for the multi-hour lecture "Tensor networks algorithms for fluid dynamics",
presented at the QTADE school in Bilbao. This repo hosts everything for the lecture:
LaTeX notes, Quarto/reveal.js slides, companion Python notebooks, and a shared bibliography.

## Repository layout

```
.
├── notes/                 # LaTeX lecture notes — this folder is the Overleaf project
│   ├── main.tex           # top-level document, \input's the section files
│   ├── preamble.tex       # shared packages/macros
│   ├── sections/          # one .tex file per section (edit here or in Overleaf)
│   ├── figures/           # figures used in the notes (source of truth for all figures)
│   └── bibliography.bib   # SHARED bibliography — single source of truth (see below)
│
├── slides/                 # Quarto (reveal.js) slide deck
│   ├── slides.qmd
│   ├── _quarto.yml
│   └── bibliography.bib -> ../notes/bibliography.bib   # symlink, do not duplicate
│
├── notebooks/              # Companion Python/Jupyter notebooks
│   ├── environment.yml     # conda/mamba environment for reproducibility
│   └── requirements.txt    # pip alternative
│
├── scripts/
│   └── sync_overleaf.sh    # push/pull the notes/ subtree to/from an Overleaf project via git
│
└── .github/workflows/      # CI: compile notes to PDF, render slides, (optional) Overleaf sync
```

## Why `notes/` is its own Overleaf project (not the whole repo)

Overleaf's Git integration clones an entire repository into an Overleaf project — it has no
built-in "sync only this subfolder" option. To keep Overleaf's editor clean (i.e. not show
slides, notebooks, `.github/`, etc.) we treat `notes/` as an independent unit synced via
[`git subtree`](https://www.atlassian.com/git/tutorials/git-subtree):

- Overleaf gives every project a private git URL (Project → Menu → Git).
- We add that URL as a git remote (e.g. `overleaf`) and push/pull *only* the `notes/`
  subdirectory to/from it with `git subtree`, without ever cloning the whole repo into
  Overleaf.
- `scripts/sync_overleaf.sh` wraps the exact commands so nobody has to remember the
  `git subtree` syntax.

This means: edit LaTeX either directly in this repo (any editor) *or* live in Overleaf —
just remember to sync (push/pull) through the script so the two don't drift apart. See
`notes/README.md` for the step-by-step.

## Bibliography — single source of truth

`notes/bibliography.bib` is the only real bibliography file in the repo. `slides/bibliography.bib`
is a **symlink** to it, so citations in the slides and in the notes always stay in sync. Add new
references to `notes/bibliography.bib` only.

(Symlinks survive normal git operations and the `git subtree` push/pull used for Overleaf, since
the symlink lives in `slides/`, which is never subtree-split. Overleaf itself only ever sees the
real file, because it only receives the `notes/` subtree.)

## Figures

All figures live in `notes/figures/` (so they travel with the Overleaf-synced subtree and are
available for `\includegraphics` there). Slides reference the same files via a relative path,
e.g. `![](../notes/figures/my-figure.pdf)`, rather than duplicating images.

## Continuous integration

On every push, GitHub Actions:
- compiles `notes/main.tex` → `notes.pdf` (uploaded as a build artifact),
- renders `slides/slides.qmd` → reveal.js HTML (uploaded as a build artifact, and deployed to
  GitHub Pages from `main`, see `.github/workflows/build-slides.yml`).

See `.github/workflows/` for details, and the "Setup" section below for the one-time repo
settings these require.

## One-time setup checklist

1. Create the GitHub repo and push this scaffold.
2. In the repo settings, enable **GitHub Pages** → source: "GitHub Actions" (only needed if you
   want the slides auto-published to a public URL).
3. Create an Overleaf project, get its git URL, and follow `notes/README.md` to link it.
4. Fill in `notebooks/environment.yml` / `requirements.txt` with the actual tensor-network /
   scientific-computing packages you use (left as placeholders here).
5. Decide on a license (not set yet — see `LICENSE` placeholder) and author list.

## Collaborators

- (add names / affiliations here)
