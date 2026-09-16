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
    # The expected numbering is the one citeproc produces with nature.csl:
    # order of first appearance in the source. Derive it here independently of
    # gen_slide_refs.py, then check that every rendered span carries exactly the
    # numbers its keys own. Comparing sets (not sequences) is deliberate: the
    # CSL sorts within a span and collapses runs of three or more into a range.
    cite_re = re.compile(r"\[([^\]\[]*@[^\]\[]*)\]")
    key_re = re.compile(r"@([A-Za-z][\w:.#$%&+?<>~/-]*)")
    order = []
    for grp in cite_re.findall(src):
        for k in key_re.findall(grp):
            if k not in order:
                order.append(k)
    citeproc = {k: i + 1 for i, k in enumerate(order)}

    def span_numbers(text: str) -> set:
        """Numbers a rendered span carries, expanding collapsed ranges."""
        out, plain = set(), re.sub(r"<[^>]+>", "", text)
        for chunk in re.split(r"[,;\s]+", plain):
            rng = re.match(r"^(\d+)[‐-―-](\d+)$", chunk.strip())
            if rng:
                out |= set(range(int(rng.group(1)), int(rng.group(2)) + 1))
            elif chunk.strip().isdigit():
                out.add(int(chunk.strip()))
        return out

    seen = set()
    for m in re.finditer(r'<span class="citation" data-cites="([^"]+)">(.*?)</span>', h, re.S):
        keys = m.group(1).split()
        nums = span_numbers(m.group(2))
        seen.update(keys)
        unknown = [k for k in keys if k not in citeproc]
        if unknown:
            failures.append(f"citation span cites keys absent from the source: {unknown}")
            continue
        want = {citeproc[k] for k in keys}
        if nums != want:
            failures.append(f"citation {keys}: rendered {sorted(nums)}, expected {sorted(want)}")

    check(bool(seen), "citations present", f"{len(seen)} distinct sources")
    check(seen == set(citeproc), "every cited key rendered",
          str(sorted(set(citeproc) ^ seen)))

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

    # --- figures survived the render ----------------------------------------
    imgs = re.findall(r'<img\b[^>]*?(?:data-)?src="data:image/', h)
    check(len(imgs) >= 3, "images embedded", f"{len(imgs)} found")
    # The repo QR must survive the render. Match on the source image rather than
    # on a slide title, so renaming the opening slide does not break the check.
    check("figures/qr-code.png" in src, "repo QR referenced in the deck")
    # A stretched figure sizes itself from the slide's leftover height, so a
    # full-height section collapses it. Ensure the CSS still exempts them.
    check(":not(:has(.r-stretch))" in h,
          "full-height rule still exempts stretched figures")

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
