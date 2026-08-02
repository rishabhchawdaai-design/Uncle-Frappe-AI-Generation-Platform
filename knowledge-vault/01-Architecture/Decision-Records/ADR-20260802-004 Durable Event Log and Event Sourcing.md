---
id: "ADR-20260802-004"
title: "Durable Event Log and Event Sourcing"
status: accepted
date: "2026-08-02"
module: "event_log"
capability: "MSG-01..06"
owner: "platform"
decision-makers: [platform-engineering]
tags: [adr, architecture, events, messaging, durable]
---

# ADR-20260802-004: Durable Event Log and Event Sourcing

## Status

accepted

## Date

2026-08-02

## Context

The in-memory event bus lost events on restart. Audit, replay and dead-letter requirements from the Messaging research could not be met.

## Decision

Add `ai_generation/event_log.py`: a SQLite-backed durable log with the ACOS event taxonomy, per-class delivery guarantees (at-most-once/at-least-once), replay, retention, and a dead-letter queue, attached to the live bus.

## Consequences

### Positive

- Events survive restarts
- Replay + DLQ for recovery
- Taxonomy-driven guarantees


### Negative

- SQLite write overhead per event


## Alternatives Considered

Keep in-memory only (rejected: no durability) / external message broker (rejected: needs infra)

## Related

- [[Capability Registry]]
- [[36-Generated/Modules/event_log|event_log]]
- Commits: `2e56aa9`

## Review History

| Date | Reviewer | Outcome |
|------|----------|---------|
| 2026-08-02 | Platform Engineering | accepted |
