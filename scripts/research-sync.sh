#!/usr/bin/env bash
# Research Synchronization — pull canonical ACOS-Research changes into the
# production platform's research integration cache and open a PR when the
# cache changes. Research content is never copied; only generated artifacts
# (manifest, index, execution queue) are updated.
#
# Usage:
#   scripts/research-sync.sh            sync research and open a PR if changed
#   scripts/research-sync.sh --check    report pending changes, exit 1 if any
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

RESEARCH_REPO="${ACOS_RESEARCH_REPO:-$REPO_ROOT/../acos-research}"
BRANCH="chore/research-sync-$(date +%s)"
REMOTE="origin"
REMOTE_URL="$(git remote get-url origin)"
TOKEN="$(echo "$REMOTE_URL" | sed -E 's#https://x-access-token:([^@]+)@.*#\1#')"
API_BASE="https://api.github.com/repos/rishabhchawdaai-design/Uncle-Frappe-AI-Generation-Platform"

echo "== Research Synchronization =="
echo "Research repo: $RESEARCH_REPO"

if [ "${1:-}" = "--check" ]; then
    echo "Checking for pending research changes..."
    PENDING="$(PYTHONPATH=. python3 - <<'PY'
from ai_generation.research_integration import ResearchIntegrationEngine
engine = ResearchIntegrationEngine()
print(len(engine.detect_changes()))
PY
)"
    if [ "$PENDING" != "0" ]; then
        echo "PENDING: $PENDING research change(s) — run scripts/research-sync.sh to sync."
        exit 1
    fi
    echo "OK: research cache is synchronized."
    exit 0
fi

# Refresh the canonical research repo clone (token lives in its origin URL).
if [ -d "$RESEARCH_REPO/.git" ]; then
    git -C "$RESEARCH_REPO" pull --ff-only origin main >/dev/null 2>&1 \
        || echo "WARN: could not pull research repo (offline/unauthenticated); using local state"
else
    echo "WARN: research repo not found at $RESEARCH_REPO; using committed manifest cache"
fi

PYTHONPATH=. python3 -m ai_generation.cli research-sync

# Only manifest/queue changes represent research evolution; a regenerated
# index timestamp alone is not a synchronization event.
if git diff --quiet -- data/research/research_manifest.json data/research/execution_queue.json; then
    git checkout -- data/research/research_index.json 2>/dev/null || true
    echo "No research changes — cache is synchronized."
    exit 0
fi

git checkout -b "$BRANCH"
git add data/research/
git commit -m "chore: synchronize research integration cache with ACOS-Research"
git push "$REMOTE" "$BRANCH" >/dev/null 2>&1

curl -sS -X POST -H "Authorization: Bearer $TOKEN" \
    -H "Accept: application/vnd.github+json" \
    "$API_BASE/pulls" \
    -d "{\"title\":\"chore: synchronize research integration cache\",\"head\":\"$BRANCH\",\"base\":\"main\",\"body\":\"Automated sync of the research integration cache from ACOS-Research. Review CI, then merge.\"}" \
    | python3 -c "import json,sys; d=json.load(sys.stdin); print('PR:', d.get('html_url') or d.get('message'))"

git checkout main >/dev/null 2>&1 || true
echo "Done. Merge the PR after CI passes."
