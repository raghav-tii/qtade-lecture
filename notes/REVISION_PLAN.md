# Revision plan: narrative structure and language of the lecture notes

Scope: `notes/main.tex` and `notes/sections/01–05`. This is a plan; no `.tex` is changed yet.
Line numbers refer to commit `55c7bf7`.

How it was produced: four parallel developmental-editing audits, one per part. Each read its part
in full against the promises made in `main.tex`. Their findings were merged here, and the
load-bearing factual claims were spot-checked against the source.

---

## 1. Diagnosis: why the notes read as incoherent

The individual paragraphs are mostly good. The problem is architectural, and it has five root causes.

1. **The structure is taken from the slides, not from an argument.** Every part declares
   "follows the slides, in slide order", in source comments and in the prose itself (I:20,
   II:7/22, III:17, IV:5). Slide order is tuned for a talk with a speaker filling the gaps.
   On paper it gives:
   - digressions in the middle of an argument (the history block in Part I; the literature
     block in Part III);
   - results before the tools they rely on (the error budget in Part II);
   - leftover phrases such as "The slides compare…", "DMRG in a slide", "Yes, but.", and
     "The slides close with four questions".
2. **The course's own frame is announced and never used again.** `main.tex` sets up two
   things: "the single idea" (low χ = weak inter-scale coupling) and a 5-stage pipeline
   (equation → formulation → TN encoding → time evolution → retrieval).
   - No part maps itself onto the pipeline.
   - Part III substitutes a different 5-step list, which is also syntactically broken
     (III:176–184).
   - Part I's actual thesis, "low rank = low inter-scale correlation", is the fourth bullet of
     a list 470 lines in (I:482–484).
3. **No hand-offs, and no ending.**
   - Each part ends on an exercise list.
   - Part I never says that implicit Euler *is* an `Ax=b` problem, so Part II restarts with a
     duplicate CFL derivation (`eq:heat-cfl` I:753 vs `eq:cfl-heat` II:56).
   - Nonlinearity, the real bridge from Part II to Part III, is hidden in "Further open
     questions".
   - Nothing closes the course or returns to the single idea.
4. **Material is duplicated across parts and the appendix, and the copies disagree.**
   - Rank inflation under products is stated four times.
   - The 80% Poisson figure appears three times, twice in Part II (II:205–230, 272, 631),
     before the reader has met the Navier–Stokes solver it measures. It belongs to Part III
     only.
   - DMRG and matrix cross are explained both in Part II and in the appendix, with different
     notation and different numbers:
     - the maxvol bound is "about one" vs "(r+1)";
     - the local problem size is χ²d vs χd²χ.
5. **Notation and register drift.**
   - **`N`.** `main.tex:100` defines it as `2^n`. Part I uses it for the number of legs,
     Part II for the number of cores, Part III for the number of bits ("mesh size 2^N"), and
     Part IV for the state dimension.
   - **Overloaded symbols.**
     - `α` is both diffusivity and mask sharpness.
     - `m` is the mask, a bit count and a sample count.
     - `ε` is both the truncation tolerance and the dissipation rate.
     - Rank appears as χ, `D` and `r`.
   - **Quantum register.** "Nothing here is quantum" (`main.tex:34`), yet the prose speaks of
     qubits, kets, amplitude encoding and entanglement without giving the promised
     numerical-analysis synonyms.

## 2. Style sheet (decide once, apply everywhere)

Add this as a short "Notation and conventions" block in `main.tex`, replacing the current
4-bullet version.

| Concept | Use | Never |
|---|---|---|
| number of cores per coordinate | `n` | `N`, `N_x`, `M` |
| grid points per coordinate | `N = 2^n` | "mesh size `2^N`" |
| bond dimension / rank | `χ` (MPS), `χ_A` (MPO); mention `r`/TT-rank once in conventions | `D`, `r` in body |
| truncation tolerance | `\varepsilon` | `\epsilon` |
| turbulent dissipation | `ε_K` or `\mathcal{E}` | bare `ε` |
| diffusivity | `α` | — |
| mask sharpness | `β` | `α` |
| time index / steps | `k`, `K`; time bits `n_t` | `t` as index, `m` |
| state vector | `\mathbf u` | `\mathbf x` (Part IV SINDy) |
| format name | "tensor train (TT)"; "MPS" in diagrams; "QTT" only when the quantics indexing matters | "MPS/QTT", "QTT (MPO)" |
| sweeping solvers | family name "sweeping solvers (ALS, mALS/DMRG, AMEn)" | "variants of DMRG" |
| grid vocabulary | "grid points" | "pixels", "cells" interchangeably |
| quantum terms | only in margin notes, with the numerical synonym | in body prose |

Prose rules:

- **No slide references in the prose.** No "the slides …". Source comments may point to the
  deck, but must not say "in slide order".
- **One claim, one home.** Every repeated fact gets a single canonical location; elsewhere use
  `\cref` plus one clause.
- **Bullets only for genuinely parallel, enumerable items** (exercises, open problems). Any
  argument (because / therefore / but) becomes a paragraph.
- **Margin notes follow `main.tex:113`.** They carry history, attribution and warnings only,
  never data, never cross-references, and never a restatement of the adjacent text. That
  removes roughly 12 of the current 30.
- **Paragraph heads are noun phrases** ("Solution retrieval.", not "Recover the solution.").
  Retire "Rank remark." and "Stability remark." as heads.
- **Register is plain and declarative.** Cut the chatty asides ("Yes, but.", "restore hope",
  "earns its keep", "costs nothing") and the vague intensifiers ("extremely efficient",
  "very versatile").
- **Every part opens and closes the same way:**
  - open with a 1-paragraph *bridge* ("Part X left us with problem P; this part solves it by…")
    and a pipeline-stage tag;
  - close with a short *Summary and hand-off* paragraph before the exercises.

## 3. Course-level architecture

The new spine is one sentence that every part advances:

> *Physical fields have low inter-scale coupling, so they live on a low-χ manifold; Part I
> builds that manifold and computes on it explicitly, Part II learns to solve on it, Part III
> stress-tests it on the hardest forward problem (turbulence), Part IV shows the same
> structure tames the inverse problem — and the conclusion tallies where χ stayed small, grew,
> or broke.*

Structural decisions:

1. **The pipeline is the frame.** Each part opens with "Pipeline stages covered: …". The
   heat-equation close of Part I, the solver section of Part III and the MPS-DMD section of
   Part IV are each written as an explicit walk through the stages.
2. **Fold the appendix into Part II** and delete `05-appendix.tex`.
   - Its two subsections (TT-cross, DMRG) are Part II's subject per `main.tex:75`.
   - Keeping both copies is what produced the contradictory numbers.
   - Parts III and IV `\cref` the Part II subsections instead.
3. **Add a closing section, "What the bond dimension told us"** (~1 page, new
   `05-conclusion.tex` placed before the bibliography). It contains:
   - a restatement of the single idea;
   - a pipeline recap naming where each part touched each stage, including retrieval: point
     evaluation (I), pixel sampling (III), modes/eigenvalues (IV);
   - a three-row table, "χ stayed small / grew / broke": heat; Navier–Stokes vs Re and the
     disc mask; white noise and sharp ICs;
   - the open theoretical question (a-priori rank bounds).

   It absorbs IV:467–473 ("The comparison that matters") and IV:480–484 ("One stone, two
   birds").
4. **Correct the dependency claim** (`main.tex:87–88`). Part IV reuses the Part III solver
   (IV:215, 464, 503). Say "Part IV refers to Part III's solver in two places; otherwise the
   parts can be read independently", or remove those references.
5. **Deduplicate `main.tex` against Part I.**
   - Part I:10–28 repeats "the single idea" almost verbatim. Keep it in `main.tex` (the
     course promise) and open Part I with the *wall* instead (the exponential grid cost,
     I:45–68).
   - Move the publication roadmap (I:428–443) and its margin note into `main.tex`'s
     "Materials" paragraph.
6. **Fix the notebook seam.** I:775 cites `01-heat-equation-qtmps-quimb.ipynb`, which
   contradicts "Parts I–II use NumPy only" (`main.tex:123`). Either drop the reference or
   flag it explicitly as an optional extra.

## 4. Per-part plans

### Part I: Representing fields and operators

The spine is: grids are exponential → a narrow bond is structure → the SVD finds it → quantics
turns resolution into chain length, so χ = scale coupling → operators are cheap too → one
explicit PDE step is O(n), and stability then forces a linear solve.

Revised order (existing line ranges in brackets):

1. **The wall and the way out** [45–68, 152–154]. Resolve the contradiction between "only way
   out is structure" (67) and "three ways out" (153).
2. **Tensors and diagrams** [36–43, 80–129]. Notation only. Drop the arrows (95–96) and the
   copy tensor (118–119), which are never used again.
3. **SVD → TT-SVD → MPS** [152–244]. Write the 4-step enumerate as prose. Put the
   quantum ↔ numerics dictionary table (366–377) beside the definition.
4. **Computing in the format** [295–316 *before* 260–287, then 131–143].
   - Canonical form and rounding come first, then the primitives and the MPO, each with its
     rank bill stated once.
   - Delete the keyword dump at 289–293.
5. **Quantics: scales become legs** [452–540]. Open with 482–484 rewritten as the part's
   thesis. Rewrite "Why an MPS can work at all" (246–258) around this reading; the spin-chain
   area law moves to a margin note.
6. **Multi-D ordering** [578–622]. Drop "D+T" from the heading, or add one sentence on it.
7. **Operators as MPOs** [624–693]. Use `χ_A` at 658. Define García-Ripoll's `2^{Nm}`
   (691–693) or cut it.
8. **Heat equation as one pass through the pipeline** [701–772]. Label the stages, turn
   "Rank remark." and "Stability remark." into prose, and **end with the implicit system
   `(1 − αΔt L) u^{k+1} = u^k` as an `Ax=b` with no SVD shortcut.** That is the hand-off to
   Part II. Pull in the stray hooks at 271 and 661–662.
9. **Context and further reading** [319–443, cut to ~40 lines of prose].
   - Fix "seventeen-year gap White (1992) → Oseledets (2011)" at 362; that is 19 years, or 17
     to the 2009 paper.
   - Retarget the stale label `subsec:numerical-methods-intro` (46), which Parts III and IV
     cite, to the new subsection 1.

### Part II: Linear algebra on the low-rank manifold

The spine is: Part I left two debts, stability (stage 4) and getting data into the format
(stage 3). Part II pays both, then names what remains open, with nonlinearity as the explicit
bridge to Part III.

1. **Two debts from Part I** [replaces 9–32 and 43–63]. Cite `eq:heat-cfl` and delete
   `eq:cfl-heat`. Replace the Q/A bullets (44–48) with prose.
2. **Implicit Euler and its price.** A-stability; state that the price is a linear solve on a
   set that is not a vector space.
3. **Solving `Ax=b` in TT format** [90–197, merged with appendix 83–136]. Ground rules, why
   direct and Krylov methods fail, the variational form, the two-site sweep, ALS/mALS/AMEn.
   Agree on one local-problem size and one name for the family.
4. **Error budget: tolerances and stopping** [280–314, moved *before* the results].
   - Define the residual once.
   - Delete "residual of the explicit update" (260–261).
   - Retitle the subsection, e.g. "Choosing tolerances", since χ_max is incidental to it.
5. **Heat equation, implicit** [232–279]. Introduce `B` before use. **No CFD numbers
   in Part II:** move "What the solve actually costs" (205–230, a Navier–Stokes measurement,
   including the 80% Poisson share) to Part III, and delete the 80% margin notes at 272
   and 631.
6. **Getting functions and boundary conditions into TT format** [320–448, merged with
   appendix 10–82].
   - Use one cross formula (`eq:matrix-ci` *or* `eq:skeleton`) and one maxvol bound.
   - **Add the missing treatment of Dirichlet/periodic BCs in the MPO.** `main.tex:77`
     promises it and it currently gets one bullet.
7. **Case study: an immersed-body mask** [449–555].
   - Reframe around the actual evidence: smoothing does not reduce rank at tight tolerance
     (table 530–555), but it does make TT-cross robust.
   - That resolves the contradiction between "Sharpness alone is free" (488) and "give up
     the sharp edge" (499).
   - Rename the mask parameter to `β`.
   - Move the Navier–Stokes pipeline (557–571) to Part III.
   - Line 514 describes a figure that is not in the notes: insert it or give its numbers.
8. **Open problems** [602–649]. Keep the solver/format items. Move turbulence, ∇·v and
   benchmarking to Part III's Outlook. **End on nonlinearity as the hand-off.**
9. Exercises.

### Part III: The forward problem (Navier–Stokes)

The spine is: rank = scale coupling, and turbulence is the PDE where scale coupling *is* the
difficulty. Build the solver through the pipeline, validate it on laminar flow, then ask
honestly how far the ranks stretch.

1. **Why fluids: the bet stated sharply** [32–46, 140–162]. Cut "The chain of reasoning on
   the slides is short" (144) and the "slogan" phrasing.
2. **Navier–Stokes and turbulence** [48–138]. Replace the DNS-cost argument (124–132) with a
   back-reference to Part I. Bullet-only paragraphs become prose.
3. **The solver, stage by stage** [164–437].
   - Replace the broken 5-item list (176–184) with the course pipeline.
   - Explain pressure once (merge 266, 284–317).
   - **Add one sentence on why an explicit predictor is acceptable here**, given Part II's
     case against explicit schemes.
   - Cut the smoothed-mask re-derivation to a pointer to `eq:smoothed-mask` in Part II.
   - Receive "What the solve actually costs" from Part II; this is the one place where the
     80% Poisson share appears.
   - Rename the paragraph head "Recover the solution." to "Solution retrieval.".
4. **Laminar validation** [440–477, plus the demonstrator remarks 393–437]. Put Peddinti's
   results and the course's own results side by side.
5. **Turbulence: how far ranks stretch** [519–703, reordered]:
   1. metrics;
   2. compression;
   3. diagnosis (660);
   4. Hybrid-TT fix (671), defined before use;
   5. **the rank vs inertial-range measurement, promoted from the remark at 697–702 into the
      main text**, because it is the answer to `main.tex:81`;
   6. open questions (currently 653–658, before the diagnosis).

   Define Kolmogorov time units, `Re_λ`, `ℓ_0` and `L_h` on first use.
6. **Outlook and related work** [480–516 + 705–748, merged]. Drop entries already surveyed
   in Part I (I:414–425). Hand off to Part IV.

Language:

- Title dash: "Forward Problem - Solving" becomes `---`.
- `n`/`N` fixes at 151, 210, 389–391, 404–407, 604, 644. Rewrite the garbled 404–407.
- `δv` vs `δu`.
- Replace `\margintext{arXiv…}` (672) with `\cite`.
- Cut the redundant margin notes at 141, 320 and 734.

### Part IV: The inverse problem (data-driven models)

The spine is: the curse of dimensionality hits DMD's SVD and SINDy's dictionary just as it hit
PDE solvers, and the same format lifts it from both.

1. **From equations to data** [27–101, trimmed]. **Retitle the part "Learning dynamics from
   data"**, because line 49 itself says it is not about the classic inverse problem. Drop the
   prediction/learning split (77–85), which is never used again.
2. **The same curse, again** [103–117, as prose].
3. **DMD** [119–162].
4. **Data as a space–time tensor train**. Bit encoding; loading *measured* snapshots (promote
   326–328 to the main route); the temporal bond as a complexity diagnostic. Cite Part I's
   ordering discussion at 195. Define the NLS example (196).
5. **MPS-DMD** [252–364]. Define `Q`, `P` (306–308) or rewrite in terms of `V`. Make this the
   *only* home for noise vs truncation, merging 355–364 and 500–502.
6. **SINDy and MANDy** [366–443]. Cut "And more." (445–465) to two cited sentences. Introduce
   the Lorenz data (393).
7. **Remark: the same structure can also produce the data.** The space–time solver (205–250)
   is demoted from a mid-argument detour to a closing remark, with the Part II duplicate
   (227–229) cut.
8. **Outlook** [486–510, deduplicated]. Then the new course conclusion follows (§3.3).

Language:

- `m`/`N`/`r`/`χ`/`t` clashes at 175, 213, 288, 339, 346, 378–418.
- Use `\enquote` for "bonus" (249).
- Cut the redundant margin notes at 189, 331, 428 and 487.
- Qualify the following:
  - "not subject to a step-size stability condition" (225);
  - "several times below it" (338);
  - "without the curse of dimensionality" (455);
  - "O(log N) compression" (484), which should be `O(nχ²)`.

## 5. Execution plan

Each phase is one commit. After every phase run `latexmk -lualatex main.tex`; it must build
with **no undefined references or multiply-defined labels**. The CI workflow
`build-notes.yml` does the same on push; without a TeX install, `python scripts/check_refs.py` catches duplicate labels, dangling refs and unbalanced environments.

| Phase | Work | Size | Risk |
|---|---|---|---|
| 0 | Approve the style sheet (§2); add it to `main.tex` conventions | S | none |
| 1 | **Mechanical consistency:** notation (`n`/`N`/χ/ε/α→β/`m`), terminology, title dash, year fix, `\cite` for the arXiv margin note, duplicate `eq:cfl-heat`, stale label | M | low; search-and-review, not blind replace |
| 2 | **Structural moves** per part: reorder subsections, merge the appendix into Part II, move cross-part material (II→III open problems and NS pipeline, III literature→Outlook). Labels move with their text | L | medium; cross-refs |
| 3 | **Bridges and closes:** new part openings (bridge + pipeline tag), Summary and hand-off paragraphs, Part I→II `Ax=b` hand-off, Part II→III nonlinearity hand-off; write `05-conclusion.tex` | M | low |
| 4 | **Line edit:** bullets→prose, remove slide residue, margin-note pruning, vague claims, register | L | low |
| 5 | **Read-through:** one cold read of the PDF start to finish, checking that every part's first paragraph follows from the previous part's last | S | — |

Order matters. Phase 1 comes before Phase 2 so that moved text is already consistent. Phase 4
comes last so that no effort goes into polishing paragraphs that Phase 2 deletes. Parts can be
line-edited in parallel once Phase 3 is done, because the bridges fix their interfaces.

Out of scope: slides and notebooks. The notes will no longer follow slide order exactly. If
the decks must stay in sync, that is a separate pass; the recommendation is to let the notes
lead.

## 6. Decisions (resolved)

The authors accepted the recommended option in each case.

1. **Notes vs slide order.** The notes follow their own argument. Source comments may still
   name the matching deck.
2. **Appendix.** Folded into Part II; `05-appendix.tex` is removed.
3. **Part IV title.** "Learning Dynamics from Data".
4. **Part III ↔ IV independence.** The claim in `main.tex` is softened to say that Part IV
   reuses the Part III solver.
5. **Conclusion section.** Added as `05-conclusion.tex`.

## 7. Further improvements to be made

Deferred from this pass:

- **Sharp-edge / disc-rank passage.** The passage (rank-2 step automaton; disc χ 17→128)
  appears three times (I:555–575, II:476–497, III:239–247). Keep one canonical version in
  Part I and reduce the other two to a sentence and a `\cref`.
