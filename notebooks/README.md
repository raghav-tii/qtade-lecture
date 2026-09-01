# Notebooks

Companion Jupyter notebooks for the lecture (demos, numerical experiments, figure generation
for `notes/figures/`).

## Setup

```bash
conda env create -f environment.yml   # or: pip install -r requirements.txt
conda activate qtade-tn-fluids
```

## Convention: strip output before committing

Notebook outputs (especially plots/large arrays) bloat git history and cause noisy diffs.
This repo ships an `nbstripout` config; enable it once per clone:

```bash
pip install nbstripout   # already in environment.yml/requirements.txt
nbstripout --install
```

After that, `git add`/`git commit` automatically strips outputs from `.ipynb` files — no
manual step needed. If a notebook's output *is* the point (e.g. a figure you want visible on
GitHub), export it as an image into `../notes/figures/` instead of relying on the committed
output cell.

## Naming

One notebook per section/topic, numbered to match `notes/sections/`, e.g.
`02-tensor-network-basics.ipynb`, so it's easy to find the notebook backing a given part of
the notes/slides.
