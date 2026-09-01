# `notes/` — LaTeX lecture notes (Overleaf-synced)

This folder is a self-contained LaTeX project: everything it `\input`s or `\includegraphics`s
lives inside `notes/`, so it can be synced to an Overleaf project without pulling in the rest
of the repo.

## Files

- `main.tex` — top-level document; sets the document class, includes `preamble.tex`, and
  `\input`s each file under `sections/`.
- `preamble.tex` — shared packages, macros, theorem environments, tensor-network TikZ macros, etc.
- `sections/` — one `.tex` file per section of the notes. Add new sections here and `\input`
  them from `main.tex`.
- `figures/` — all figures used in the notes (also referenced by the slides via a relative path).
- `bibliography.bib` — the shared bibliography for the whole repo (slides symlink to this file).

## Linking this folder to Overleaf

Overleaf syncs an entire git repository into a project; it can't sync "just a subfolder" on its
own. We work around this with `git subtree`, so only the contents of `notes/` ever reach Overleaf.

**One-time setup:**

1. In Overleaf, create a new project ("Blank Project" is fine) and rename it, e.g.
   "QTADE tensor networks — lecture notes".
2. Open the project → menu (top-left) → **Git** (requires an Overleaf plan with Git access —
   Overleaf's paid tiers, or a Pro account issued via your institution) → copy the git URL and
   token/credentials Overleaf shows you.
3. In your local clone of *this* repo:
   ```bash
   git remote add overleaf https://git.overleaf.com/<your-project-id>
   ```
   (use the exact URL Overleaf gave you; it embeds your project id and, depending on Overleaf's
   auth setup, you'll authenticate with a token as the password when prompted).
4. Push the current `notes/` content to Overleaf for the first time:
   ```bash
   ./scripts/sync_overleaf.sh push
   ```

**Day to day:**

- If you or a collaborator edited in **Overleaf**, pull those changes into the repo before
  editing locally:
  ```bash
  ./scripts/sync_overleaf.sh pull
  ```
- If you edited **locally** (or merged a PR), push to Overleaf so it reflects the latest:
  ```bash
  ./scripts/sync_overleaf.sh push
  ```
- Treat this repo (not Overleaf) as the canonical copy for anything merged via a pull request;
  use Overleaf mainly for live/collaborative editing sessions, then push back.

## Building locally

Any standard LaTeX toolchain works, e.g.:

```bash
cd notes
latexmk -pdf main.tex
```

CI does this automatically on every push (see `.github/workflows/build-notes.yml`).
