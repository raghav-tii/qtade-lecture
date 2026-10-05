# Tensor Network Techniques for Differential Equations — QTADE School, Bilbao

Shared repository for the multi-hour lecture "Tensor network techniques for differential equations",
presented at the QTADE school in Bilbao. Slides: <https://raghav-tii.github.io/qtade-lecture/>.
This repo hosts everything for the lecture:
LaTeX notes, PDF slides (published on GitHub Pages), companion Python notebooks, and a shared bibliography.

## Repository layout

```text
.
├── bibliography.bib         # SHARED bibliography — single source of truth (see below)
├── bibliography-keymap.md   # how the three pre-merge .bib files map onto it
│
├── notes/                   # LaTeX lecture notes
│   ├── main.tex             # top-level document, \input's the section files
│   ├── preamble.tex         # shared packages/macros
│   ├── sections/            # one .tex file per part
│   └── figures/             # figures used in the notes
│
├── slides/                  # Slides as PDFs, published to GitHub Pages as-is
│   ├── part1.pdf … part4.pdf
│   └── index.html           # Pages landing page linking the four parts
│
├── notebooks/               # Companion Python/Jupyter notebooks — one per part
│   ├── qtade_tn.py          # the from-scratch NumPy toolkit (Parts I–II)
│   ├── qtade_quimb.py       # quimb layer (Parts III–IV)
│   ├── qtade_cfd.py         # Chorin projection entirely in tensor-train format
│   ├── qtade_dmd.py         # exact DMD, space-time trains, MPS-DMD
│   ├── test_qtade_*.py      # fast checks against dense reference implementations
│   ├── environment.yml      # conda/mamba environment for reproducibility
│   └── requirements.txt     # pip alternative
│
├── scripts/
│   └── rekey.py             # one-shot audit trail for the 2026 bibliography merge
│
└── .github/workflows/       # CI: compile notes to PDF, publish slides
```

## Course structure

Four 90-minute parts:

- **Part I** — Representing fields and operators: tensors and Penrose notation, MPS/TT via
  SVD, quantics tensor trains, the heat equation with explicit time stepping.
- **Part II** — Linear algebraic routines: implicit time stepping, encoding boundary and
  initial conditions, open problems.
- **Part III** — The forward problem: time evolution of the Navier–Stokes equations.
- **Part IV** — The inverse problem: data-driven methods.

Each part has one notebook that follows its slides in order, with exercises (and their
solutions) placed where the concept is introduced. **Every quantitative claim in the
notes is measured in the notebooks, on a laptop** — if a number looks wrong, rerun the
cell and tell us.

## Bibliography — single source of truth

`bibliography.bib` at the repo root is the only bibliography file. `notes/main.tex` pulls it
in via `\addbibresource{../bibliography.bib}`. Add new references only to the root file.

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

## Figures

Figures used in the notes live in `notes/figures/`.

## Slides and GitHub Pages

The slides are the PDFs in `slides/` (`part1.pdf` … `part4.pdf`). To update a part, replace
its PDF and push. On pushes to `main` that touch `slides/`,
or to `notes/` / `bibliography.bib`, `.github/workflows/build-slides.yml` compiles the notes
and publishes the slide PDFs, the `index.html` landing page and `notes.pdf` to GitHub Pages.

## Continuous integration

On every push, GitHub Actions compiles `notes/main.tex` → `notes.pdf` (uploaded as a build
artifact) and, on `main`, publishes the slides and the notes PDF to GitHub Pages (see above).

## One-time setup checklist

1. Create the GitHub repo and push this scaffold.
2. In the repo settings, enable **GitHub Pages** → source: "GitHub Actions" (only needed if you
   want the slides published to a public URL).
3. Decide on a license (not set yet — see `LICENSE.md` placeholder) and author list.

## Local builds

```bash
# notes  (LuaLaTeX + biber)
latexmk -lualatex notes/main.tex

# notebooks: the module checks are the fastest install smoke test
cd notebooks && python3 test_qtade_tn.py && python3 test_qtade_quimb.py
```

## Collaborators

- (add names / affiliations here)
