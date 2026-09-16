#!/usr/bin/env python3
"""One-shot: rewrite pre-merge citation keys to the JabRef-style keys.

Kept in the repo as the audit trail for the 2026 bibliography merge. Running it
again is harmless (no old key survives), but it is not part of any build.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

MAP = {
    # repo bibliography.bib (slides + notes)
    "peddinti2024cfd": "Peddinti2024",
    "pisoni2026turbulence": "Pisoni2026",
    "peddinti2025spacetime": "Peddinti2025a",
    "peddinti2025compressible": "Peddinti2025",
    "white1992": "White1992",
    "schollwoeck2011": "Schollwoeck2011",
    "oseledets2011": "Oseledets2011",
    "khoromskij2011": "Khoromskij2011",
    "oseledets2010ttcross": "Oseledets2010",
    "dolgov2014amen": "Dolgov2014",
    "ritter2024qtci": "Ritter2024",
    "gourianov2022": "Gourianov2022",
    "kiffner2023rom": "Kiffner2023",
    "ye2022vlasov": "Ye2022",
    "orus2014": "Orus2014",
    "bridgeman2017": "Bridgeman2017",
    "hastings2007": "Hastings2007",
    "holtz2012als": "Holtz2012",
    "kazeev2012laplace": "Kazeev2012",
    "oseledets2013functions": "Oseledets2013",
    "lubich2015timeint": "Lubich2015",
    "nunez2025tci": "Nunez2025",
    "chorin1968": "Chorin1968",
    "gourianov2025pdf": "Gourianov2025",
    "schmid2010dmd": "Schmid2010",
    "tu2014dmd": "Tu2014",
    "klus2018tdmd": "Klus2018",
    "brunton2016sindy": "Brunton2016",
    "knuth1984": None,  # scaffolding entry, dropped
}

TARGETS = ["slides/slides.qmd"] + [str(p) for p in sorted(
    (ROOT / "notes" / "sections").glob("*.tex"))]


def main() -> int:
    bad = 0
    for rel in TARGETS:
        p = ROOT / rel if not Path(rel).is_absolute() else Path(rel)
        text = p.read_text(encoding="utf-8")
        orig = text
        for old, new in MAP.items():
            if new is None:
                continue
            text = re.sub(rf"(?<![\w:.#$%&+?<>~/-]){re.escape(old)}\b", new, text)
        leftover = [k for k in MAP if re.search(rf"(?<![\w-]){re.escape(k)}\b", text)]
        if leftover:
            print(f"{p.name}: unmapped keys remain: {leftover}", file=sys.stderr)
            bad = 1
        if text != orig:
            p.write_text(text, encoding="utf-8")
            print(f"rewrote {p.relative_to(ROOT)}")
    return bad


if __name__ == "__main__":
    raise SystemExit(main())
