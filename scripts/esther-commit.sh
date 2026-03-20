#!/bin/bash
# Usage: bash esther-commit.sh "commit message" [file or . for all]
MSG="$1"
shift
cd ~/esther-lab
git add "${@:-.}"
git commit -m "$MSG"
git push
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "REAL SHA: $(git rev-parse HEAD)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
