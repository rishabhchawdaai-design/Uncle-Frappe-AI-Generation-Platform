---
module: "execution_engine"
type: module-doc
status: active
owner: ""
lines: 510
classes: 8
functions: 0
tags: [module, documentation]
generated: "2026-07-31"
---

# execution_engine

> Execution Engine — 4-layer priority-based remote execution.

Layer 1: Public APIs (official documented endpoints)
Layer 2: Hosted Open-Source (HF Spaces, community inference)
Layer 3: User-Configured 

## Overview

- **File**: `ai_generation/execution_engine.py`
- **Lines**: 510
- **Classes**: 8
- **Public Functions**: 0

## Classes

- `{{ExecutionLayer}}`
- `{{TaskType}}`
- `{{ExecutionStatus}}`
- `{{ExecutionTask}}`
- `{{ExecutionResult}}`
- `{{ProviderEndpoint}}`
- `{{ExecutionRouter}}`
- `{{ExecutionEngine}}`

## Integration

- Part of the [[Architecture Overview|Unified AI Generation Platform]]
- Exposed via [[05-SDK/SDK Overview|SDK]] and [[06-MCP-Ecosystem/MCP Ecosystem Overview|MCP Tools]]
- Verified in [[02-Capability-Registry/Capability Registry Overview|Capability Registry]]

## Related

- [[Architecture Overview]]
- [[Capability Registry Overview]]
