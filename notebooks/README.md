# Notebooks

Companion notebooks for the lecture. Two per part: a **walkthrough** that follows the
slides cell by cell, and an **exercise** set of roughly thirty minutes with solutions at
the bottom.

| notebook | pairs with |
|---|---|
| `01-walkthrough-representations.ipynb` | Part I slides / `notes/sections/01-*` |
| `01-exercises-representations.ipynb` | Part I hands-on |
| `02-walkthrough-linear-algebra.ipynb` | Part II |
| `02-exercises-linear-algebra.ipynb` | Part II hands-on |
| `03-walkthrough-forward-problem.ipynb` | Part III |
| `03-exercises-forward-problem.ipynb` | Part III hands-on |
| `04-walkthrough-inverse-problem.ipynb` | Part IV |
| `04-exercises-inverse-problem.ipynb` | Part IV hands-on |

Everything runs on a laptop. The heaviest cell is a 40-step flow solve in
`03-walkthrough`, which takes about a minute.

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
