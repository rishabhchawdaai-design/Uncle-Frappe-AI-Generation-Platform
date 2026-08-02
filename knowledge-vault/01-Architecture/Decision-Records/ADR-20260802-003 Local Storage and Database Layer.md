---
id: "ADR-20260802-003"
title: "Local Storage and Database Layer"
status: accepted
date: "2026-08-02"
module: "storage"
capability: "STR-01..06"
owner: "platform"
decision-makers: [platform-engineering]
tags: [adr, architecture, storage, sqlite, json]
---

# ADR-20260802-003: Local Storage and Database Layer

## Status

accepted

## Date

2026-08-02

## Context

Metadata, ledgers and audit records had no canonical home. Subsystems wrote ad-hoc JSON, making queries, consistency and a single storage abstraction impossible.

## Decision

Add `ai_generation/storage.py` with a `StorageRegistry` over local SQLite and JSON backends plus truthfully `not_configured` external profiles (PostgreSQL, Qdrant, MinIO, Neo4j, Prometheus, Redis). Task-based selection routes metadata/ledger/graph writes to the best available backend.

## Consequences

### Positive

- One storage API across subsystems
- Offline, zero-dependency persistence
- External profiles are truthful, not fake


### Negative

- External backends require user configuration


## Alternatives Considered

Direct SQLite everywhere (rejected: no abstraction) / external-only (rejected: no offline path)

## Related

- [[Capability Registry]]
- [[36-Generated/Modules/storage|storage]]
- Commits: `7d72e1b`

## Review History

| Date | Reviewer | Outcome |
|------|----------|---------|
| 2026-08-02 | Platform Engineering | accepted |
