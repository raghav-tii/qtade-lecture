#!/usr/bin/env bash
#
# Sync the notes/ subfolder with an Overleaf project via git subtree, without ever
# pulling the rest of this repo (slides/, notebooks/, CI, ...) into Overleaf.
#
# One-time setup (see notes/README.md for the full walkthrough):
#   git remote add overleaf https://git.overleaf.com/<your-project-id>
#
# Usage:
#   ./scripts/sync_overleaf.sh push   # send local notes/ changes to Overleaf
#   ./scripts/sync_overleaf.sh pull   # bring Overleaf edits into local notes/
#
set -euo pipefail

REMOTE="overleaf"
BRANCH="master"   # Overleaf git projects default to "master"; adjust if yours differs
PREFIX="notes"

usage() {
  echo "Usage: $0 {push|pull}"
  exit 1
}

if ! git remote get-url "$REMOTE" >/dev/null 2>&1; then
  echo "error: git remote '$REMOTE' is not configured." >&2
  echo "Run: git remote add $REMOTE <your-overleaf-project-git-url>" >&2
  exit 1
fi

case "${1:-}" in
  push)
    echo "Pushing local ${PREFIX}/ -> Overleaf (${REMOTE}/${BRANCH})..."
    git subtree push --prefix="${PREFIX}" "${REMOTE}" "${BRANCH}"
    ;;
  pull)
    echo "Pulling Overleaf (${REMOTE}/${BRANCH}) -> local ${PREFIX}/..."
    git subtree pull --prefix="${PREFIX}" "${REMOTE}" "${BRANCH}" --squash
    ;;
  *)
    usage
    ;;
esac
