# Tensor Network Algorithms for Fluid Dynamics — QTADE School, Bilbao

Shared repository for the multi-hour lecture "Tensor networks algorithms for fluid dynamics",
presented at the QTADE school in Bilbao. This repo hosts everything for the lecture:
LaTeX notes, Quarto/reveal.js slides, companion Python notebooks, and a shared bibliography.

## Repository layout

```text
.
├── bibliography.bib         # SHARED bibliography — single source of truth (see below)
├── bibliography-keymap.md   # how the three pre-merge .bib files map onto it
│
├── notes/                   # LaTeX lecture notes
│   ├── main.tex             # top-level document, \input's the section files
│   ├── preamble.tex         # shared packages/macros
│   ├── sections/            # one .tex file per part (edit here or in Overleaf)
│   └── figures/             # figures used in the notes
│
├── slides/                  # Quarto (reveal.js) slide deck
│   ├── slides.qmd
│   ├── styles.css           # incl. the .q / .breaks / .lab / .hero teaching blocks
│   └── _quarto.yml
│
├── notebooks/               # Companion Python/Jupyter notebooks — two per part
│   ├── qtade_tn.py          # the from-scratch NumPy toolkit (Parts I–II)
│   ├── qtade_quimb.py       # quimb layer (Parts III–IV)
│   ├── qtade_cfd.py         # Chorin projection entirely in tensor-train format
│   ├── qtade_dmd.py         # exact DMD, space-time trains, MPS-DMD
│   ├── test_qtade_*.py      # fast checks against dense reference implementations
│   ├── environment.yml      # conda/mamba environment for reproducibility
│   └── requirements.txt     # pip alternative
│
├── scripts/
│   ├── gen_slide_refs.py    # regenerate slide footnotes + reference slides
│   ├── check_slides_build.py# verify the rendered deck before it is published
│   ├── rekey.py             # one-shot audit trail for the 2026 bibliography merge
│   └── sync_overleaf.sh     # push/pull this repo to/from the linked Overleaf project
│
└── .github/workflows/       # CI: compile notes to PDF, render slides, (optional) Overleaf sync
```

## Course structure

Four 90-minute parts. Parts I and II build the tensor-network toolkit *from inside a PDE
solver* — every notion arrives when a numerical method needs it. Parts III and IV spend
that toolkit on the forward and inverse problems of CFD, and map the surrounding
literature.

Each part has a walkthrough notebook (follows the slides cell by cell) and an exercise
notebook (~30 minutes, solutions at the bottom). **Every quantitative claim in the slides
and notes is measured in the notebooks, on a laptop** — if a number looks wrong, rerun the
cell and tell us.

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
in via `\addbibresource{../bibliography.bib}`; `slides/_quarto.yml` as
`bibliography: ../bibliography.bib`. Add new references only to the root file — both the
notes and the slides pick them up automatically.

Keys are **JabRef style**: `Surname` + `Year`, disambiguated `a`, `b`, `c`. JabRef
regenerates them with *Quality → Generate BibTeX key*, so they stay stable if the file is
edited there. Entries are grouped by their role in the course, in the order the course
uses them, with a one-line comment above each saying what it is cited *for* — that habit
is what keeps a 150-entry file navigable. Abstracts, `file`, `keywords` and `urldate`
fields are deliberately stripped: they break both citation processors and no one reads
them.

`bibliography-keymap.md` records how the three pre-merge files (the old root
`bibliography.bib`, `references.bib`, `master_database.bib`) map onto the merged one,
which duplicates were collapsed, and what was added.

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
4. Decide on a license (not set yet — see `LICENSE.md` placeholder) and author list.

## Local builds

```bash
# notes  (LuaLaTeX + biber)
latexmk -lualatex notes/main.tex

# slides (Quarto), then verify before publishing
quarto render slides/slides.qmd
python3 scripts/check_slides_build.py slides/index.html

# notebooks: the module checks are the fastest install smoke test
cd notebooks && python3 test_qtade_tn.py && python3 test_qtade_quimb.py
```

## Collaborators

- (add names / affiliations here)
