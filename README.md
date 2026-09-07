# Tensor Network Algorithms for Fluid Dynamics — QTADE School, Bilbao

Shared repository for the multi-hour lecture "Tensor networks algorithms for fluid dynamics",
presented at the QTADE school in Bilbao. This repo hosts everything for the lecture:
LaTeX notes, Quarto/reveal.js slides, companion Python notebooks, and a shared bibliography.

## Repository layout

```text
.
├── bibliography.bib        # SHARED bibliography — single source of truth (see below)
│
├── notes/                  # LaTeX lecture notes
│   ├── main.tex            # top-level document, \input's the section files
│   ├── preamble.tex        # shared packages/macros
│   ├── sections/           # one .tex file per section (edit here or in Overleaf)
│   └── figures/            # figures used in the notes
│
├── slides/                 # Quarto (reveal.js) slide deck
│   ├── slides.qmd
│   └── _quarto.yml
│
├── notebooks/               # Companion Python/Jupyter notebooks
│   ├── environment.yml      # conda/mamba environment for reproducibility
│   └── requirements.txt     # pip alternative
│
├── scripts/
│   └── sync_overleaf.sh     # push/pull this repo to/from the linked Overleaf project
│
└── .github/workflows/       # CI: compile notes to PDF, render slides, (optional) Overleaf sync
```

## Overleaf setup

[Overleaf Project](https://www.overleaf.com/8197722423jvcgthhrnbzp#da662e)

The whole repo is linked to a single Overleaf project (simplest option — one thing to sync,
one git remote, no subtree gymnastics). The tradeoff: Overleaf's file browser will show
`slides/`, `notebooks/`, `.github/`, etc. alongside `notes/` — you just leave those alone in
the Overleaf editor and work on them in a normal git client/IDE instead.

**One-time setup:**

1. In Overleaf, create a new project ("Blank Project" is fine) and rename it, e.g.
   "QTADE tensor networks — lecture".
2. Open the project → menu (top-left) → **Git** (requires an Overleaf plan with Git access —
   Overleaf's paid tiers, or a Pro account issued via your institution) → copy the git URL.
3. Point Overleaf at the right document: Menu → **Settings** → **Main document** →
   `notes/main.tex`.
4. In your local clone of this repo:

   ```bash
   git remote add overleaf https://git.overleaf.com/<your-project-id>
   ./scripts/sync_overleaf.sh push
   ```

**Day to day**, from the repo root:

```bash
./scripts/sync_overleaf.sh pull   # bring in edits made live in Overleaf
./scripts/sync_overleaf.sh push   # send local commits (e.g. after merging a PR) to Overleaf
```

Overleaf git projects use a fixed branch name (`master`) independent of whatever your GitHub
default branch is called — the script handles that mapping so you don't have to think about it.

Treat this repo (not Overleaf) as canonical for anything merged via a pull request; use Overleaf
mainly for live/collaborative editing sessions, then push back with the script above.

## Bibliography — single source of truth

`bibliography.bib` at the repo root is the only bibliography file. `notes/main.tex` pulls it
in as `\bibliography{../bibliography}`; `slides/_quarto.yml` as `bibliography: ../bibliography.bib`.
Add new references only to the root file — both the notes and the slides pick them up
automatically.

The slides cite with `nature.csl`: superscript numbers, numbered globally by order of first
appearance, so a source keeps the same number throughout the deck. Each citing slide also
carries a footnote line naming its sources, and the reference list at the end is split across
several slides. Both are generated — after adding, removing, or reordering any citation, run:

```bash
python3 scripts/gen_slide_refs.py
```

It rewrites the generated blocks in `slides/slides.qmd` in place (they are marked with
`<!-- BEGIN generated: ... -->` comments) and renumbers everything to match citeproc.

## Figures

Figures used in the notes live in `notes/figures/`. Slides reference the same files via a
relative path, e.g. `![](../notes/figures/my-figure.pdf)`, rather than duplicating images.

## Continuous integration

On every push, GitHub Actions:

- compiles `notes/main.tex` → `notes.pdf` (uploaded as a build artifact),
- renders `slides/slides.qmd` → reveal.js HTML (uploaded as a build artifact, and deployed to
  GitHub Pages from `main`, see `.github/workflows/build-slides.yml`).

The slides workflow does three things beyond a plain render:

1. **Regenerates the citation blocks** (`scripts/gen_slide_refs.py`) before rendering, so the
   published deck is correct even when an edit arrived through Overleaf, where nobody can run
   the script. If the committed file was stale, the run still succeeds but leaves a warning
   asking you to run the script locally and commit the result.
2. **Stages a single-file site.** `embed-resources: true` inlines fonts, MathJax, images and
   the reveal.js runtime, so `index.html` stands alone and only that file is deployed — slide
   sources are not published to Pages.
3. **Verifies the build** (`scripts/check_slides_build.py`) before publishing: that the deck is
   genuinely self-contained, and that in-text citation numbers, the per-slide footnote lines and
   the reference slides all agree. The run fails rather than deploying a broken deck.

You can run that check locally against your own render:

```bash
quarto render slides/slides.qmd
python3 scripts/check_slides_build.py slides/index.html
```

See `.github/workflows/` for details, and the "Setup" section below for the one-time repo
settings these require.

## One-time setup checklist

1. Create the GitHub repo and push this scaffold.
2. In the repo settings, enable **GitHub Pages** → source: "GitHub Actions" (only needed if you
   want the slides auto-published to a public URL).
3. Create an Overleaf project, get its git URL, and follow "Overleaf setup" above to link it.
4. Fill in `notebooks/environment.yml` / `requirements.txt` with the actual tensor-network /
   scientific-computing packages you use (left as placeholders here).
5. Decide on a license (not set yet — see `LICENSE.md` placeholder) and author list.

## Collaborators

- (add names / affiliations here)
