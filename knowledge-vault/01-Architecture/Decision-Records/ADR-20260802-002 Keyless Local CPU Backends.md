---
id: "ADR-20260802-002"
title: "Keyless Local CPU Backends"
status: accepted
date: "2026-08-02"
module: "providers/local_backends"
capability: "EDT-04, AUD-01, AUD-04, OCR-07"
owner: "platform"
decision-makers: [platform-engineering]
tags: [adr, architecture, backend, local, keyless, cpu]
---

# ADR-20260802-002: Keyless Local CPU Backends

## Status

accepted

## Date

2026-08-02

## Context

Keyless generation was limited to a few cloud APIs. Embeddings, TTS, STT, OCR, translation, upscaling and background removal all had free open-weight CPU implementations, but none were integrated, so a fresh install could not produce these modalities without keys or GPUs.

## Decision

Add a local backends layer (`ai_generation/providers/local_backends.py`) with lazy imports so the stdlib-only core stays light: sentence-transformers embeddings, Piper TTS, faster-whisper STT, Tesseract OCR, Helsinki opus-mt translation, Real-ESRGAN upscaling via spandrel, and rembg background removal. Every backend returns truthful dependency/install errors when its package is missing, and the unified SDK/CLI/MCP surface exposes each backend.

## Consequences

### Positive

- Keyless real-media generation for seven modalities
- No mandatory heavy dependencies
- Truthful errors instead of crashes


### Negative

- Heavy packages install on demand
- Local CPU quality varies by backend


## Alternatives Considered

Copy heavy packages into requirements.txt (rejected: breaks stdlib-first install) / cloud-only backends (rejected: requires keys)

## Related

- [[Capability Registry]]
- [[36-Generated/Modules/local_runtimes|local_runtimes]]
- Commits: `0479da8`

## Review History

| Date | Reviewer | Outcome |
|------|----------|---------|
| 2026-08-02 | Platform Engineering | accepted |
