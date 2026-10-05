# Tensor Network Algorithms for Fluid Dynamics — QTADE School, Bilbao

Shared repository for the multi-hour lecture "Tensor networks algorithms for fluid dynamics",
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
│   ├── sections/            # one .tex file per part (edit here or in Overleaf)
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
│   ├── rekey.py             # one-shot audit trail for the 2026 bibliography merge
│   └── sync_overleaf.sh     # push/pull this repo to/from the linked Overleaf project
│
└── .github/workflows/       # CI: compile notes to PDF, publish slides, (optional) Overleaf sync
```

## Course structure

Four 90-minute parts. Parts I and II build the tensor-network toolkit *from inside a PDE
solver* — every notion arrives when a numerical method needs it. Parts III and IV spend
that toolkit on the forward and inverse problems of CFD, and map the surrounding
literature.

Each part has one notebook that follows its slides in order, with exercises (and their
solutions) placed where the concept is introduced. **Every quantitative claim in the slides
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
`.github/workflows/build-slides.yml` publishes the `slides/` folder — the PDFs plus the
`index.html` landing page — to GitHub Pages.

## Continuous integration

On every push, GitHub Actions compiles `notes/main.tex` → `notes.pdf` (uploaded as a build
artifact) and, on `main`, publishes the slides to GitHub Pages (see above).

## One-time setup checklist

1. Create the GitHub repo and push this scaffold.
2. In the repo settings, enable **GitHub Pages** → source: "GitHub Actions" (only needed if you
   want the slides published to a public URL).
3. Create an Overleaf project, get its git URL, and follow "Overleaf setup" above to link it.
4. Decide on a license (not set yet — see `LICENSE.md` placeholder) and author list.

## Local builds

```bash
# notes  (LuaLaTeX + biber)
latexmk -lualatex notes/main.tex

# notebooks: the module checks are the fastest install smoke test
cd notebooks && python3 test_qtade_tn.py && python3 test_qtade_quimb.py
```

## Collaborators

- (add names / affiliations here)
