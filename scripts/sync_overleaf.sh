#!/usr/bin/env bash
#
# Sync this whole repo with its linked Overleaf project.
#
# Overleaf's git integration links a whole git repository to a whole Overleaf project, and
# Overleaf projects default to a branch named "master" (independent of whatever your GitHub
# default branch is called). This script just wraps push/pull against the "overleaf" remote
# so nobody has to remember the branch-name mapping.
#
# One-time setup (see README.md "Overleaf setup"):
#   git remote add overleaf https://git.overleaf.com/<your-project-id>
#
# Usage:
#   ./scripts/sync_overleaf.sh push   # send local commits to Overleaf
#   ./scripts/sync_overleaf.sh pull   # bring Overleaf edits into your local branch
#
set -euo pipefail

REMOTE="overleaf"
OVERLEAF_BRANCH="main"          # Overleaf's side - fixed name, don't change
LOCAL_BRANCH="$(git symbolic-ref --short HEAD)"

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
    echo "Pushing local '${LOCAL_BRANCH}' -> Overleaf (${REMOTE}/${OVERLEAF_BRANCH})..."
    git push "${REMOTE}" "${LOCAL_BRANCH}:${OVERLEAF_BRANCH}"
    ;;
  pull)
    echo "Pulling Overleaf (${REMOTE}/${OVERLEAF_BRANCH}) -> local '${LOCAL_BRANCH}'..."
    git pull "${REMOTE}" "${OVERLEAF_BRANCH}:${LOCAL_BRANCH}"
    ;;
  *)
    usage
    ;;
esac
