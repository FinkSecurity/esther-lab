#!/bin/bash
# esther-commit.sh — commit, push, and print real SHA
# Usage: bash esther-commit.sh "commit message" [file or . for all]
# Run from the repo directory you want to commit to.

MSG="$1"
shift

if [ -z "$MSG" ]; then
 echo "Usage: bash esther-commit.sh \"commit message\" [file or . for all]"
 exit 1
fi

# Confirm we're inside a git repo
if ! git rev-parse --git-dir > /dev/null 2>&1; then
 echo "ERROR: Not inside a git repository. cd to the correct repo first."
 exit 1
fi

REPO=$(basename "$(git rev-parse --show-toplevel)")

git add "${@:-.}"
git commit -m "$MSG"
git push

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "REPO: $REPO"
echo "REAL SHA: $(git rev-parse HEAD)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
