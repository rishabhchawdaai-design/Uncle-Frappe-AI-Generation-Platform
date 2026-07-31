---
id: "ADR-20260731-001"
title: "Research Integration Layer and Canonical Ecosystem"
status: accepted
date: "2026-07-31"
module: "research_integration"
capability: ""
owner: "platform"
decision-makers: [platform-engineering]
tags: [adr, architecture, research, integration, canonical]
---

# ADR-20260731-001: Research Integration Layer and Canonical Ecosystem

## Status

accepted

## Date

2026-07-31

## Context

The project spans two GitHub repositories: ACOS-Research (canonical knowledge:
specifications, chapters, research areas, benchmarks, roadmaps) and the
Uncle-Frappe AI Generation Platform (canonical implementation). Prior state
risked duplicated documentation, disconnected knowledge, and no way to answer
"which research produced this capability?" or "what breaks if this research
changes?".

## Decision

Create ONE engineering ecosystem with distinct canonical homes:

- ACOS-Research = canonical knowledge (read-only upstream, never modified).
- Uncle-Frappe-AI-Generation-Platform = canonical implementation.
- Knowledge vault = human intelligence layer.
- Capability Registry = implementation status layer.
- Execution Engine / integration layer = autonomous implementation layer.

Implement a Research Integration Layer (`ai_generation/research_integration.py`)
that:

- imports only metadata (ids, titles, hashes, commits, categories) — never research content;
- maps every registry capability to exactly one canonical research document;
- cross-references documents to the capabilities that implement them (satisfaction);
- provides traceability, impact analysis, change detection, and an execution queue
  with truthful classifications (satisfied / blocked / speculative / implementable);
- exposes a traversable research ↔ implementation graph;
- automates synchronization via `scripts/research-sync.sh` and a CI cron
  (`.github/workflows/research-sync.yml`) guarded by `ACOS_RESEARCH_TOKEN`.

Generated caches (`data/research/*.json`) are committed; research content is not.

## Consequences

### Positive

- Every capability knows its research source, modules, tests, SDK, MCP tools, vault page, and commit.
- Research changes now have a computed blast radius.
- No duplicated markdown; the research repo remains the single knowledge source.
- Queue and registry truthfully reflect verified vs. externally blocked work.

### Negative

- The integration layer adds a synchronization step that must be kept fresh.
- Cross-reference mappings require maintenance as research evolves.
- CI cron automation waits on an `ACOS_RESEARCH_TOKEN` secret.

## Alternatives Considered

### Option A: Copy research into the production repo
Rejected — duplicates thousands of documents and creates two sources of truth.

### Option B: Merge both repositories
Rejected — different lifecycles (knowledge vs. implementation) and ownership.

### Option C: No integration layer
Rejected — research and implementation drift without traceability.

## Related

- [[Architecture Overview]]
- [[24-Research/Research Integration|Research Integration]]
- [[34-Dashboards/Research Integration Dashboard|Research Integration Dashboard]]
- [[22-Playbooks/Research Sync Runbook|Research Sync Runbook]]
- Commits: `81642cf` (integration layer), `0a443b2` (sync automation), `74eb1bb` (satisfaction traceability)

## Review History

| Date | Reviewer | Outcome |
|------|----------|---------|
| 2026-07-31 | Platform Engineering | accepted |
