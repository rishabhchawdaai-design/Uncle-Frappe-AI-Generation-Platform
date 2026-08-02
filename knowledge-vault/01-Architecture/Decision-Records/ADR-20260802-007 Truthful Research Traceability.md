---
id: "ADR-20260802-007"
title: "Truthful Research Traceability"
status: accepted
date: "2026-08-02"
module: "research_integration"
capability: "RTG-01..08"
owner: "platform"
decision-makers: [platform-engineering]
tags: [adr, architecture, research, traceability, knowledge]
---

# ADR-20260802-007: Truthful Research Traceability

## Status

accepted

## Date

2026-08-02

## Context

The research index linked capabilities by token overlap, producing false positives (blocked capabilities claiming implementation) and false negatives (47 verified capabilities with no module links).

## Decision

Add curated ID-based aliases to `research_integration.py` linking all 47 verified-but-unlinked capabilities to their real modules, and stop linking BLOCKED capabilities entirely. The index now guarantees: every VERIFIED capability has >=1 module link; every BLOCKED capability has none.

## Consequences

### Positive

- Index truthfully reflects implementation
- Regression guards prevent drift


### Negative

- Curated aliases need review when modules are renamed


## Alternatives Considered

Uncurated token linking (rejected: false positives/negatives)

## Related

- [[ADR-20260731-001 Research Integration Layer]]
- [[36-Generated/Modules/research_integration|research_integration]]
- Commits: `ebcbf76`

## Review History

| Date | Reviewer | Outcome |
|------|----------|---------|
| 2026-08-02 | Platform Engineering | accepted |
