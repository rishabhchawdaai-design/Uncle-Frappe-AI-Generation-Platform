---
type: runbook
status: active
owner: platform
tags: [runbook, research, sync, integration, automation]
---

# Research Sync Runbook

> Keeps the production platform synchronized with the canonical ACOS-Research
> knowledge source without duplicating research content.

## When to Run

- Weekly via CI cron (`.github/workflows/research-sync.yml`, Sunday 03:23 UTC).
- Manually whenever ACOS-Research gains new documents or specifications.
- Locally before starting an implementation cycle.

## Prerequisites

- Local: the research repo clone at `../acos-research` with authenticated origin
  (token lives in that repo's git config — never in command arguments or logs).
- CI: `ACOS_RESEARCH_TOKEN` repository secret. The workflow degrades gracefully
  (job skipped) until the secret is configured.

## Local Sync

```bash
scripts/research-sync.sh --check   # report pending changes (exit 1 if any)
scripts/research-sync.sh           # pull research, refresh cache, open PR if changed
```

The script never prints the token. If the cache changed it creates branch
`chore/research-sync-<ts>`, pushes it, and opens a PR (main is protected;
merges require CI checks to pass).

## What Sync Does

1. Pulls the canonical research repo (`--ff-only`).
2. Runs `python -m ai_generation.cli research-sync`:
   - detects new / modified / removed research documents
   - refreshes `data/research/research_manifest.json` and `research_index.json`
   - classifies new research into `data/research/execution_queue.json`
     (`implementable` / `blocked` / `speculative` with reasons)
3. Opens a PR only when manifest or queue content changed — a regenerated
   index timestamp alone is not a synchronization event.

## After Sync

- Review the execution queue for `implementable` items and implement the
  highest-priority one (traceability via `research-trace <CAPABILITY>`).
- Keep `blocked` items in the queue with their external-dependency reason.

## References

- [[24-Research/Research Integration|Research Integration]]
- [[36-Generated/Modules/research_integration|research_integration module]]
- [[01-Architecture/Architecture Overview|Architecture Overview]]
