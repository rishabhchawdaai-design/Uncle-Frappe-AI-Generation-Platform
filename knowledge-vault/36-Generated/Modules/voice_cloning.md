---
module: "voice_cloning"
type: module-doc
status: active
owner: ""
lines: 318
classes: 9
functions: 0
tags: [module, documentation]
generated: "2026-07-31"
---

# voice_cloning

> Voice Cloning — XTTS (Coqui), Fish Speech, OpenVoice.
All providers attempt local inference or HTTP API.
Gracefully degrade when backends are unavailable.

## Overview

- **File**: `ai_generation/voice_cloning.py`
- **Lines**: 318
- **Classes**: 9
- **Public Functions**: 0

## Classes

- `{{VoiceCloningProvider}}`
- `{{VoiceCloneStatus}}`
- `{{VoiceCloneProfile}}`
- `{{VoiceCloneResult}}`
- `{{VoiceCloningProviderBase}}`
- `{{XTVoiceCloningProvider}}`
- `{{FishSpeechVoiceCloningProvider}}`
- `{{OpenVoiceCloningProvider}}`
- `{{VoiceCloningEngine}}`

## Integration

- Part of the [[Architecture Overview|Unified AI Generation Platform]]
- Exposed via [[05-SDK/SDK Overview|SDK]] and [[06-MCP-Ecosystem/MCP Ecosystem Overview|MCP Tools]]
- Verified in [[02-Capability-Registry/Capability Registry Overview|Capability Registry]]

## Related

- [[Architecture Overview]]
- [[Capability Registry Overview]]
