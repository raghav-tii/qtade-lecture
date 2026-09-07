#!/usr/bin/env python3
"""Sanity-check a rendered slide deck before it is published.

Guards the things that break quietly: a deck that is no longer self-contained
(so GitHub Pages would serve a page with missing maths, fonts or images), and
citation numbering that has drifted out of sync between the in-text markers,
the per-slide footnote lines and the reference slides.

    python3 scripts/check_slides_build.py _site/index.html

Exits non-zero, listing every failure, if anything is wrong.
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
QMD = ROOT / "slides" / "slides.qmd"

failures = []
notes = []


def check(ok: bool, label: str, detail: str = "") -> None:
    (notes if ok else failures).append(f"{label}{': ' + detail if detail else ''}")


def main() -> int:
    html_path = Path(sys.argv[1] if len(sys.argv) > 1 else ROOT / "slides" / "index.html")
    if not html_path.exists():
        print(f"FAIL: rendered deck not found at {html_path}")
        return 1

    h = html_path.read_text(encoding="utf-8")
    src = QMD.read_text(encoding="utf-8")

    # --- the deck must stand alone, since Pages serves only this file --------
    stray = set()
    for m in re.finditer(r'(?:src|href)="([^"]{1,300})"', h):
        u = m.group(1)
        if u.startswith(("data:", "#", "http://", "https://", "mailto:", "${", "'")):
            continue
        stray.add(u)
    check(not stray, "self-contained (no external file refs)", ", ".join(sorted(stray)[:5]))
    check("<script src=\"https://" not in h, "no CDN <script src> at runtime")
    check("MathJax" in h, "MathJax inlined")
    check(len(h) > 500_000, "deck size plausible", f"{len(h)/1e6:.1f} MB")

    n_slides = h.count("<h2")
    check(n_slides > 50, "slide count plausible", f"{n_slides} h2 slides")

    # --- citation numbering -------------------------------------------------
    rendered = {}
    for m in re.finditer(r'<span class="citation" data-cites="([^"]+)">(.*?)</span>', h, re.S):
        inner = re.sub(r"<[^>]+>", "", m.group(2))
        for n in re.findall(r"\d+", inner):
            rendered.setdefault(m.group(1), set()).add(int(n))

    check(bool(rendered), "citations present", f"{len(rendered)} distinct sources")
    unstable = {k: sorted(v) for k, v in rendered.items() if len(v) != 1}
    check(not unstable, "every source keeps one number globally", str(unstable))
    citeproc = {k: next(iter(v)) for k, v in rendered.items() if len(v) == 1}

    # --- per-slide footnote lines match what citeproc actually numbered ------
    mismatched = []
    for slide in re.split(r"\n(?=## )", src):
        cited = []
        for grp in re.findall(r"\[([^\]\[]*@[^\]\[]*)\]", slide):
            for k in re.findall(r"@([A-Za-z][\w:-]*)", grp):
                if k not in cited:
                    cited.append(k)
        fn = re.search(r"::: slide-refs\n(.+?)\n:::", slide, re.S)
        got = [int(x) for x in re.findall(r'ref-n">(\d+)</span>', fn.group(1))] if fn else []
        want = sorted(citeproc[k] for k in cited if k in citeproc)
        if got != want:
            mismatched.append(f"{slide.splitlines()[0][3:]} (footnote {got} vs citeproc {want})")
    check(not mismatched, "slide footnotes match in-text numbers", "; ".join(mismatched[:3]))

    # --- reference slides cover every cited number --------------------------
    refs = {int(n) for n in re.findall(r"^(\d+)\. [A-Z]", src, re.M)}
    check(bool(refs), "reference slides present", f"{len(refs)} entries")
    check(sorted(refs) == list(range(1, len(refs) + 1)), "reference numbering contiguous")
    missing = sorted(set(citeproc.values()) - refs)
    check(not missing, "every cited number appears in the reference list", str(missing))

    # --- the citation styling actually shipped ------------------------------
    check('content: "["' in h and 'content: "]"' in h, "bracketed citation markers styled")
    check("#107895" in h, "citation accent colour shipped")
    check(".slide-refs" in h, "slide footnote styling shipped")

    for n in notes:
        print(f"  ok   {n}")
    for f in failures:
        print(f"  FAIL {f}")
    print(f"\n{len(notes)} passed, {len(failures)} failed")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
