# Notebooks

Companion notebooks for the lecture: **one per part**, following that part's slides
(`../slides/partN.pdf`) in order. Exercises sit where the concept is introduced, each
followed directly by its solution.

| notebook | pairs with |
|---|---|
| `01-representations.ipynb` | Part I slides / `notes/sections/01-*` |
| `01-heat-equation-qtmps-quimb.ipynb` | Part I — 1D/2D heat equation in `quimb` (referenced from the slides) |
| `02-linear-algebra.ipynb` | Part II |
| `03-forward-problem.ipynb` | Part III |
| `04-inverse-problem.ipynb` | Part IV |

Everything runs on a laptop; each notebook finishes in a few minutes.

## The modules

Parts I and II build everything from scratch, because the mechanics are the point.
Parts III and IV move to `quimb` for representation and compression, and keep the Part II
solver — **no tensor-network library ships a linear solver for `A x = b`**, since the
quantum-physics use case wants ground states instead. That seam is a lesson, not an
oversight.

| module | what it is | used by |
|---|---|---|
| `qtade_tn.py` | ~700 lines of NumPy: TT-SVD, rounding, canonical forms, MPOs, quantics operators, TT-cross with maxvol, ALS and two-site DMRG solvers | Parts I–II, and the solver everywhere |
| `qtade_quimb.py` | thin layer on `quimb`: conversions, bit-ordering helpers, 2-D operators, Hadamard products, compressed readout | Parts III–IV |
| `qtade_cfd.py` | Chorin projection with every field a quantics train | Part III |
| `qtade_dmd.py` | exact DMD, space-time trains, MPS-DMD | Part IV |

`qtade_tn.py` is meant to be *read*. Each function is the shortest honest implementation
of one idea from the lecture, and several things are deliberately naive so that the cost
of the naive version is visible.

## Setup

```bash
conda env create -f environment.yml   # or: pip install -r requirements.txt
conda activate qtade-tn-fluids
```

## Checks

The two module test suites run in a few seconds and are the fastest way to confirm an
install works:

```bash
python3 test_qtade_tn.py
python3 test_qtade_quimb.py
```

They are also the fastest way to find out whether a change you made to `qtade_tn.py`
broke something — the quantics shift operator, the Laplacian, the cross interpolation and
both solvers are all checked against dense reference implementations.

## Convention: strip output before committing

Notebook outputs bloat git history and cause noisy diffs. This repo ships an `nbstripout`
config; enable it once per clone:

```bash
pip install nbstripout
nbstripout --install
```

If a notebook's output *is* the point (a figure you want visible on GitHub), export it as
an image into `../notes/figures/` instead of relying on the committed output cell.
