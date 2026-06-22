#!/usr/bin/env bash
# Sincroniza /home/hpp/amazon con DasLatam/amazon: si hay cambios, commit + push.
set -euo pipefail
cd /home/hpp/amazon

git add -A

if git diff --cached --quiet; then
  exit 0
fi

git commit -q -m "Auto-sync $(date '+%Y-%m-%d %H:%M:%S')"
git push -q origin main
echo "$(date '+%Y-%m-%d %H:%M:%S') sincronizado: $(git log -1 --format=%H)"
