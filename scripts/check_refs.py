"""Check the notes' cross-references without a TeX install.

Fails if a label is defined twice, if a \\ref/\\cref/\\eqref target is never
defined, or if a \\begin/\\end pair is unbalanced in any section file.
Run from the repo root: python scripts/check_refs.py
"""
import re
import sys
from collections import Counter
from pathlib import Path

NOTES = Path(__file__).resolve().parent.parent / "notes"
inputs = re.findall(r"^\\input\{(sections/[^}]+)\}", (NOTES / "main.tex").read_text(), re.M)
files = [NOTES / "main.tex"] + [NOTES / f"{i}.tex" for i in inputs if (NOTES / f"{i}.tex").exists()]


def strip_comments(s):
    return re.sub(r"(?<!\\)%.*", "", s)


labels, refs, errors = Counter(), set(), []
for f in files:
    src = strip_comments(f.read_text())
    labels.update(re.findall(r"\\label\{([^}]+)\}", src))
    for group in re.findall(r"\\(?:[cC]ref|ref|eqref|autoref|hyperref)\{([^}]+)\}|\\hyperref\[([^\]]+)\]", src):
        for g in group:
            refs.update(k.strip() for k in g.split(",") if k.strip())
    stack = []
    for m in re.finditer(r"\\(begin|end)\{([^}]+)\}", src):
        kind, env = m.groups()
        if kind == "begin":
            stack.append(env)
        elif not stack or stack.pop() != env:
            errors.append(f"{f.name}: unbalanced \\end{{{env}}}")
    errors += [f"{f.name}: unclosed \\begin{{{e}}}" for e in stack]

errors += [f"label defined {n}x: {k}" for k, n in labels.items() if n > 1]
errors += [f"undefined ref: {r}" for r in sorted(refs - set(labels))]
print("\n".join(errors) or f"ok: {len(files)} files, {len(labels)} labels, {len(refs)} refs")
sys.exit(bool(errors))
