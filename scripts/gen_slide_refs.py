#!/usr/bin/env python3
"""Regenerate per-slide citation footnotes and the multi-slide reference list.

Citations in slides.qmd stay as normal Quarto `[@key]` markers, rendered by
citeproc with nature.csl as globally-numbered superscripts. This script mirrors
citeproc's numbering (order of first appearance) so that each slide can carry a
footnote line naming the sources it cites, and so the reference slides at the
end can be split across several slides while staying in numeric order.

Idempotent: strips its own previous output before regenerating. Run from the
repo root after adding or moving any citation:

    python3 scripts/gen_slide_refs.py
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BIB = ROOT / "bibliography.bib"
QMD = ROOT / "slides" / "slides.qmd"

REFS_PER_SLIDE = 8
BEGIN = "<!-- BEGIN generated: slide refs -->"
END = "<!-- END generated: slide refs -->"
BIB_BEGIN = "<!-- BEGIN generated: bibliography -->"

ACCENTS = {
    r"{\"o}": "ö", r"{\"u}": "ü", r"{\"a}": "ä",
    r"{\'a}": "á", r"{\'e}": "é", r"{\'i}": "í", r"{\'o}": "ó", r"{\'u}": "ú",
    r"{\~n}": "ñ", r"{\~a}": "ã", r"{\c c}": "ç",
}


def delatex(s: str) -> str:
    for k, v in ACCENTS.items():
        s = s.replace(k, v)
    s = s.replace("--", "–")
    # drop brace protection, but keep $...$ math intact
    return re.sub(r"[{}]", "", s).strip()


def parse_bib(text: str) -> dict:
    """Very small bibtex reader: enough for this repo's uniform entries."""
    entries = {}
    for m in re.finditer(r"@\w+\s*\{\s*([^,]+),(.*?)\n\}", text, re.S):
        key, body = m.group(1).strip(), m.group(2)
        fields = {}
        for fm in re.finditer(r"(\w+)\s*=\s*\{(.*?)\}\s*,?\s*(?=\n\s*\w+\s*=|\s*$)", body, re.S):
            fields[fm.group(1).lower()] = " ".join(fm.group(2).split())
        entries[key] = fields
    return entries


def authors(field: str) -> list:
    """['Peddinti, Raghavendra D.', ...] -> ['R. D. Peddinti', ...]"""
    out = []
    for a in field.split(" and "):
        a = delatex(a)
        if "," in a:
            last, first = [p.strip() for p in a.split(",", 1)]
            initials = " ".join(f"{w[0]}." for w in first.split() if w and w[0].isalpha())
            out.append(f"{initials} {last}".strip())
        else:
            out.append(a)
    return out


def surname(field: str) -> str:
    first = field.split(" and ")[0]
    return delatex(first.split(",")[0].strip() if "," in first else first.split()[-1])


def short_ref(e: dict) -> str:
    """Compact label for the per-slide footnote line."""
    names = field_authors = e.get("author", "")
    n = len(field_authors.split(" and "))
    who = surname(names)
    if n == 2:
        who += " & " + surname(" and ".join(field_authors.split(" and ")[1:]))
    elif n > 2:
        who += " *et al.*"
    return f"{who} ({e.get('year','')})"


def full_ref(e: dict) -> str:
    """Reference-slide entry, physics style."""
    au = authors(e.get("author", ""))
    who = au[0] if len(au) == 1 else (
        " & ".join(au) if len(au) == 2 else f"{au[0]} *et al.*")
    title = delatex(e.get("title", ""))
    journal = delatex(e.get("journal", ""))
    year, vol, pages = e.get("year", ""), e.get("volume", ""), delatex(e.get("pages", ""))

    if journal.lower().startswith("arxiv preprint"):
        arxiv = journal.split("arXiv:")[-1].strip()
        return f"{who}, *{title}*, arXiv:{arxiv} ({year})."

    bits = f"{who}, *{title}*, {journal}"
    if vol:
        bits += f" **{vol}**"
    if pages:
        bits += f", {pages}"
    bits += f" ({year})."
    note = e.get("note", "")
    if note.startswith("arXiv:"):
        bits += f" [{note}]"
    return bits


def strip_generated(text: str) -> str:
    # Consume the blank lines that surround the block too, otherwise each run
    # leaves a pair behind and the file grows on every invocation.
    text = re.sub(r"\n*" + re.escape(BEGIN) + r".*?" + re.escape(END) + r"\n*",
                  "\n\n", text, flags=re.S)
    i = text.find(BIB_BEGIN)
    if i != -1:
        text = text[:i]
    return text


def main() -> int:
    bib = parse_bib(BIB.read_text(encoding="utf-8"))
    src = strip_generated(QMD.read_text(encoding="utf-8")).rstrip("\n")

    # cut the old bibliography section; it is regenerated below
    m = re.search(r"\n# Bibliography\b.*$", src, re.S)
    if m:
        src = src[: m.start()]

    cite_re = re.compile(r"\[([^\]\[]*@[^\]\[]*)\]")
    key_re = re.compile(r"@([A-Za-z][\w:.#$%&+?<>~/-]*)")

    # pass 1: global numbering = order of first appearance (matches citeproc)
    order = []
    for grp in cite_re.findall(src):
        for k in key_re.findall(grp):
            if k not in order:
                order.append(k)
    num = {k: i + 1 for i, k in enumerate(order)}

    missing = [k for k in order if k not in bib]
    if missing:
        print(f"error: cited keys absent from bibliography.bib: {missing}", file=sys.stderr)
        return 1

    # pass 2: append a footnote line to every h2 slide that cites something
    out, slide, in_slide = [], [], False

    def flush():
        if not slide:
            return
        body = "\n".join(slide)
        keys = []
        for grp in cite_re.findall(body):
            for k in key_re.findall(grp):
                if k not in keys:
                    keys.append(k)
        # Normalise trailing blank lines so output does not depend on input state.
        while slide and not slide[-1].strip():
            slide.pop()
        out.extend(slide)
        if keys:
            keys.sort(key=lambda k: num[k])
            line = " · ".join(
                f'[<span class="ref-n">{num[k]}</span>]&nbsp;{short_ref(bib[k])}'
                for k in keys)
            out.extend(["", BEGIN, "::: slide-refs", line, ":::", END])
        out.append("")
        slide.clear()

    for ln in src.split("\n"):
        if ln.startswith("## "):
            flush()
            in_slide = True
            slide.append(ln)
        elif ln.startswith("# ") and not ln.startswith("##"):
            flush()
            in_slide = False
            out.append(ln)
        elif in_slide:
            slide.append(ln)
        else:
            out.append(ln)
    flush()

    # pass 3: multi-slide, numerically ordered reference list
    chunks = [order[i:i + REFS_PER_SLIDE] for i in range(0, len(order), REFS_PER_SLIDE)]
    biblio = ["", BIB_BEGIN, '# Bibliography {background-color="#bc6c16"}', ""]
    for chunk in chunks:
        # Every slide is titled plainly "References"; the numbered list carries
        # the continuation, so no range suffix is needed in the title.
        biblio.append("## References")
        biblio.append("")
        biblio.append("::: reference-list")
        for k in chunk:
            biblio.append(f"{num[k]}. {full_ref(bib[k])}")
        biblio.extend([":::", ""])

    QMD.write_text("\n".join(out).rstrip("\n") + "\n" + "\n".join(biblio), encoding="utf-8")
    print(f"{len(order)} references numbered, "
          f"{sum(1 for l in out if l == BEGIN)} slides annotated, "
          f"{len(chunks)} reference slides")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
