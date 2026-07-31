---
module: "mcp_registry"
type: module-doc
status: active
owner: ""
lines: 234
classes: 1
functions: 1
tags: [module, documentation]
generated: "2026-07-31"
---

# mcp_registry

> MCP Registry — unified registry of MCP servers for the platform.

Single source of truth: ``configs/mcp_servers.json`` (canonical, merged
with the platform's original MCP configuration — no parallel r

## Overview

- **File**: `ai_generation/mcp_registry.py`
- **Lines**: 234
- **Classes**: 1
- **Public Functions**: 1

## Classes

- `{{MCPRegistry}}`

## Public API

- `get_mcp_registry()`

## Integration

- Part of the [[Architecture Overview|Unified AI Generation Platform]]
- Exposed via [[05-SDK/SDK Overview|SDK]] and [[06-MCP-Ecosystem/MCP Ecosystem Overview|MCP Tools]]
- Verified in [[02-Capability-Registry/Capability Registry Overview|Capability Registry]]

## Related

- [[Architecture Overview]]
- [[Capability Registry Overview]]
