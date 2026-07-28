---
module: "edge_ai"
type: module-doc
status: active
owner: ""
lines: 661
classes: 5
functions: 2
tags: [module, documentation]
generated: "2026-07-28"
---

# edge_ai

> Edge AI Runtime Detection — detect and profile edge AI hardware and runtimes.

Based on ACOS Research: Edge AI Research, Technology Atlas §10
Provides hardware detection, capability profiling, deploym

## Overview

- **File**: `ai_generation/edge_ai.py`
- **Lines**: 661
- **Classes**: 5
- **Public Functions**: 2

## Classes

- `{{EdgeHardware}}`
- `{{EdgeRuntime}}`
- `{{EdgeDetectionMethod}}`
- `{{EdgeHardwareProfile}}`
- `{{EdgeAIManager}}`

## Public API

- `detect_edge_hardware()`
- `run_inference()`

## Integration

- Part of the [[Architecture Overview|Unified AI Generation Platform]]
- Exposed via [[05-SDK/SDK Overview|SDK]] and [[06-MCP-Ecosystem/MCP Ecosystem Overview|MCP Tools]]
- Verified in [[02-Capability-Registry/Capability Registry Overview|Capability Registry]]

## Related

- [[Architecture Overview]]
- [[Capability Registry Overview]]
