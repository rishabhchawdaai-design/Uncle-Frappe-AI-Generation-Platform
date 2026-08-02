---
id: "ADR-20260802-006"
title: "Compatibility Matrix — Model x Runtime x Hardware"
status: accepted
date: "2026-08-02"
module: "compatibility_matrix"
capability: "CGR-03, CGR-04, CGR-07"
owner: "platform"
decision-makers: [platform-engineering]
tags: [adr, architecture, compatibility, routing, matrix]
---

# ADR-20260802-006: Compatibility Matrix — Model x Runtime x Hardware

## Status

accepted

## Date

2026-08-02

## Context

The Negotiation Engine lacked the Model x Runtime x Hardware lookup table specified by COMPATIBILITY_MATRIX.md, so execution-path validation could not check whether a model actually runs on a chosen runtime and hardware.

## Decision

Add `ai_generation/compatibility_matrix.py`: 161 seeded entries across 44 models and 40 catalogued runtimes (llm/image/video/audio/ocr/browser/edge), with hardware fallback, runtime/model discovery, CGR-07 path validation, benchmark score feedback, 90-day refresh tracking, and JSON persistence. Exposed via SDK `compat_*`, five CLI commands, and five MCP tools.

## Consequences

### Positive

- Execution paths are validated against reality
- Benchmark results feed back into routing
- Seeded from the official matrix


### Negative

- Matrix data needs periodic refresh


## Alternatives Considered

No matrix (rejected: unvalidated routing) / static hardcoded table (rejected: not extensible)

## Related

- [[Capability Registry]]
- [[36-Generated/Modules/compatibility_matrix|compatibility_matrix]]
- Commits: `03cfef6`

## Review History

| Date | Reviewer | Outcome |
|------|----------|---------|
| 2026-08-02 | Platform Engineering | accepted |
