---
id: "ADR-20260802-008"
title: "E2E Verification Harness Standard"
status: accepted
date: "2026-08-02"
module: "scripts/verify_generation"
capability: "BMK-01..08"
owner: "platform"
decision-makers: [platform-engineering]
tags: [adr, architecture, verification, e2e, quality]
---

# ADR-20260802-008: E2E Verification Harness Standard

## Status

accepted

## Date

2026-08-02

## Context

The verification harness produced crashes and false failures: a NameError in the capability-graph check, an outdated speech assumption, fake-image inputs to PIL-based tools, and garbage bytes fed to faster-whisper.

## Decision

Fix the harness so all 19 modality checks pass with real artifacts: speech accepts keyless piper_local success, STT runs the piper -> faster-whisper round-trip, upscale/bg-removal consume the real generated image (512x512 -> 2048x2048 verified), and a valid stdlib tiny-PNG helper provides artifact fallback. Live run: 19/19 PASS, zero crashes.

## Consequences

### Positive

- Fresh-install proof for every modality
- Credential/local-gated modalities fail truthfully


### Negative

- Harness needs heavy optional deps for local backends


## Alternatives Considered

Mocked verification (rejected: fake success)

## Related

- [[Capability Registry]]
- [[36-Generated/Modules/benchmark_engine|benchmark_engine]]
- Commits: `977989c`

## Review History

| Date | Reviewer | Outcome |
|------|----------|---------|
| 2026-08-02 | Platform Engineering | accepted |
