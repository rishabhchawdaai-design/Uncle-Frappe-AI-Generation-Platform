---
module: "tool_registry"
type: module-doc
status: active
owner: ""
lines: 92
classes: 1
functions: 1
tags: [module, documentation]
generated: "2026-07-31"
---

# tool_registry

> Tool Registry — unified registry of external code-quality tools.

Single source of truth: ``configs/tools.json`` (canonical — no parallel
tool registry). Every ready entry records a distribution verif

## Overview

- **File**: `ai_generation/tool_registry.py`
- **Lines**: 92
- **Classes**: 1
- **Public Functions**: 1

## Classes

- `{{ToolRegistry}}`

## Public API

- `get_tool_registry()`

## Integration

- Part of the [[Architecture Overview|Unified AI Generation Platform]]
- Exposed via [[05-SDK/SDK Overview|SDK]] and [[06-MCP-Ecosystem/MCP Ecosystem Overview|MCP Tools]]
- Verified in [[02-Capability-Registry/Capability Registry Overview|Capability Registry]]

## Related

- [[Architecture Overview]]
- [[Capability Registry Overview]]
