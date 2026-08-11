#!/usr/bin/env bash
# Experiment 01 — Generalization smoke test
# Run from repo root: bash docs/experiments/01-generalization-smoke-test/run-smoke-test.sh
# Produces docs/experiments/01-generalization-smoke-test/raw-output.log
set +e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
LOG="$REPO_ROOT/docs/experiments/01-generalization-smoke-test/raw-output.log"
> "$LOG"

# Real comic projects discovered via:  find ~ -maxdepth 5 -name shotlist.json
projects=(
  "$HOME/Documents/chunli-growth-series-v2"
  "$HOME/Documents/supergirl-inversion"
  "$HOME/Documents/chun-li-serum-courtyard"
  "$HOME/Documents/comic-april-mutagen-v2"
  "$HOME/Documents/mira-five-sips-groa34"
  "$HOME/Documents/chunli-issue-1"
  "$HOME/Documents/chunli-ascension-15p-2026-05-16"
  "$HOME/Documents/chun-li-ascension"
  "$HOME/Documents/checks-balances-demo-2026-05-16"
  "$HOME/Documents/Mira's Story — Ch1 Rooftop Pool"
  "$HOME/Documents/moving-experience-v2"
  "$HOME/Documents/supergirl-muscular.archived-2026-05-12"
  "$REPO_ROOT/projects/chun-li-test"
  "$REPO_ROOT/projects/ultra-gal-origin"
  "$REPO_ROOT/projects/solo-fmg-001"
)

cd "$REPO_ROOT"
for P in "${projects[@]}"; do
  echo "===== $P =====" | tee -a "$LOG"
  OUT=$(python3 skills/comic-production/scripts/next_panel.py "$P" --as-json 2>&1)
  RC=$?
  echo "$OUT" >> "$LOG"
  echo "exit code: $RC" | tee -a "$LOG"
  echo "" >> "$LOG"
done

echo "DONE — see $LOG"
