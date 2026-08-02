---
id: "ADR-20260802-005"
title: "Capability Graph Auto-Synchronization"
status: accepted
date: "2026-08-02"
module: "capability_graph"
capability: "CGR-01..09"
owner: "platform"
decision-makers: [platform-engineering]
tags: [adr, architecture, graph, routing, registry]
---

# ADR-20260802-005: Capability Graph Auto-Synchronization

## Status

accepted

## Date

2026-08-02

## Context

The capability graph was a static default topology. Providers, storage backends and the event log registered at runtime, so the graph drifted from the real platform.

## Decision

Add `synchronize_from_registries()` to `CapabilityGraph`, exposed as SDK `sync_capability_graph()`, CLI `cap-graph-sync`, and the `sync_capability_graph` MCP tool. The graph now evolves automatically from the live provider/storage/event-log registries (52 nodes / 48 edges) and finds free-first execution paths.

## Consequences

### Positive

- Graph always matches implementation
- Free-first pathfinding
- Idempotent sync


### Negative

- Sync must be triggered or kept fresh by CI


## Alternatives Considered

Hand-maintained graph (rejected: drift) / fully dynamic graph (rejected: no defaults)

## Related

- [[Capability Registry]]
- [[36-Generated/Modules/capability_graph|capability_graph]]
- Commits: `c00727f`

## Review History

| Date | Reviewer | Outcome |
|------|----------|---------|
| 2026-08-02 | Platform Engineering | accepted |
