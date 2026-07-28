---
module: "supervisor"
type: module-doc
status: active
owner: ""
lines: 449
classes: 8
functions: 4
tags: [module, documentation]
generated: "2026-07-28"
---

# supervisor

> Supervisor Tree — Fail-Fast, Recover-Quietly framework.

Based on ACOS Research: Erlang/OTP-style supervision.
Ported from acos-research/core/supervisor.py for production use.

Constitution Adherence:

## Overview

- **File**: `ai_generation/supervisor.py`
- **Lines**: 449
- **Classes**: 8
- **Public Functions**: 4

## Classes

- `{{SupervisionStrategy}}`
- `{{WorkerType}}`
- `{{SupervisorConfig}}`
- `{{WorkerState}}`
- `{{SupervisorError}}`
- `{{WorkerCrashError}}`
- `{{SupervisionEvent}}`
- `{{SupervisorTree}}`

## Public API

- `create_provider_supervisor()`
- `create_agent_supervisor()`
- `create_engine_supervisor()`
- `create_platform_supervisor()`

## Integration

- Part of the [[Architecture Overview|Unified AI Generation Platform]]
- Exposed via [[05-SDK/SDK Overview|SDK]] and [[06-MCP-Ecosystem/MCP Ecosystem Overview|MCP Tools]]
- Verified in [[02-Capability-Registry/Capability Registry Overview|Capability Registry]]

## Related

- [[Architecture Overview]]
- [[Capability Registry Overview]]
