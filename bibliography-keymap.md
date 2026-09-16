# Bibliography merge — key map

Three files became one. `bibliography.bib` at the repo root is now the only
bibliography; `references.bib` and `master_database.bib` are retired.

Keys follow **JabRef style**: `Surname` + `Year`, disambiguated `a`, `b`, `c` in
insertion order. JabRef regenerates them with *Quality → Generate BibTeX key*, so
they stay stable if the file is edited there.

Abstracts, `file`, `keywords`, `urldate`, `annote` and `collaborator` fields were
dropped on merge. They break `scripts/gen_slide_refs.py`'s reader and neither
biblatex nor citeproc uses them here.

## Old repo key → new key

These are the keys that were live in `slides/slides.qmd` and `notes/sections/`.
`scripts/rekey.py` performed the rewrite and is kept as the audit trail.

| old (repo `bibliography.bib`) | new |
|---|---|
| `bridgeman2017` | `Bridgeman2017` |
| `brunton2016sindy` | `Brunton2016` |
| `chorin1968` | `Chorin1968` |
| `dolgov2014amen` | `Dolgov2014` |
| `gourianov2022` | `Gourianov2022` |
| `gourianov2025pdf` | `Gourianov2025` |
| `hastings2007` | `Hastings2007` |
| `holtz2012als` | `Holtz2012` |
| `kazeev2012laplace` | `Kazeev2012` |
| `khoromskij2011` | `Khoromskij2011` |
| `kiffner2023rom` | `Kiffner2023` |
| `klus2018tdmd` | `Klus2018` |
| `lubich2015timeint` | `Lubich2015` |
| `nunez2025tci` | `Nunez2025` |
| `orus2014` | `Orus2014` |
| `oseledets2010ttcross` | `Oseledets2010` |
| `oseledets2011` | `Oseledets2011` |
| `oseledets2013functions` | `Oseledets2013` |
| `peddinti2024cfd` | `Peddinti2024` |
| `peddinti2025compressible` | `Peddinti2025` |
| `peddinti2025spacetime` | `Peddinti2025a` |
| `pisoni2026turbulence` | `Pisoni2026` |
| `ritter2024qtci` | `Ritter2024` |
| `schmid2010dmd` | `Schmid2010` |
| `schollwoeck2011` | `Schollwoeck2011` |
| `tu2014dmd` | `Tu2014` |
| `white1992` | `White1992` |
| `ye2022vlasov` | `Ye2022` |
| `knuth1984` | *dropped* (scaffolding, never cited) |

## Old `references.bib` / `master_database.bib` keys

Both files were merged wholesale. The pattern is mechanical:

* `master_database.bib` already used JabRef keys, so most carried over unchanged
  (`Gourianov2022`, `Kiffner2023`, `Chorin1968`, `Pope2000`, …).
* `references.bib` used ad-hoc keys; they map to the JabRef key of the same work:
  `peddinti` → `Peddinti2024`, `pisoni2025compression` → `Pisoni2026`,
  `Erika_vlasov_eq` → `Ye2022`, `kornev2023chemicalmixer` → `Kornev2024`,
  `Greens_function_MPS` / `Shinaoka2023` → `Shinaoka2023`,
  `White_PRL_1992` → `White1992`, `Image_Compression` → `Latorre2005`, and so on.
  If you cannot find an old key, search `bibliography.bib` for the title.

Duplicates collapsed on merge (the two files disagreed on several):

* Oseledets 2012 *Constructive representation…* is `Oseledets2013` (the printed
  Constructive Approximation issue is 2013; the online-first date is 2012).
* Tindall *et al.* existed three times (arXiv 2023, PRX Quantum 2023, PRX Quantum
  2024). Only the published version survives, as `Tindall2024`.
* Kurmapu *et al.* existed as arXiv 2022 and PRX Quantum; kept as `Kurmapu2023`.
* Latorre 2005, White 1992, Orús 2014, Oseledets 2012 (linear systems), Kornev
  (TetraFEM) and Gourianov 2022 each existed twice; one survives.
* Kornev *et al.* 2023 (chemical mixers, arXiv) and 2024 (TetraFEM, *Mathematics*)
  are different papers and both survive, as `Kornev2023` and `Kornev2024`.

## What was added

New entries, by why the course needs them:

* **Notation and foundations** — `Penrose1971`, `Vidal2004` (TEBD).
* **Approximation theory** — `Kazeev2018` (exponential convergence of quantized
  FEM), `Beylkin2002`, `Khoromskij2018`.
* **Algorithms** — `Goreinov2010` (maxvol, previously cited only in prose),
  `Ballani2013` (Krylov/projection in TT), `Lubich2013`,
  `Michailidis2025` (element-wise TT products — the Hadamard cost in Part III).
* **Classical numerics** — `LeVeque2007`, `Trefethen2000`, `Temam1969`,
  `Harlow1965`.
* **CFD benchmarks** — `Ghia1982` (lid-driven cavity), `Schaefer1996` (cylinder).
  Both are named as benchmarks in the notes but were previously uncited.
* **Turbulence** — `Frisch1995`.
* **TN-CFD field** — `Hoelscher2025` (GPU-accelerated 2D turbulence).
* **Data-driven** — `Mezic2005`, `Williams2015` (EDMD), `Sirovich1987`,
  `Berkooz1993` (POD baseline), `Gelss2019` (MANDy — SINDy in TT),
  `Stoudenmire2016`, and the neural-surrogate comparison class `Raissi2019`,
  `Lu2021`.
