---
module: "skill_registry"
type: module-doc
status: active
owner: ""
lines: 97
classes: 1
functions: 1
tags: [module, documentation]
generated: "2026-07-31"
---

# skill_registry

> Skill Registry — unified registry of skills for the platform.

Single source of truth: ``configs/skills.json`` (canonical — no parallel
skill registry). Platform-native skills map to verified modules;

## Overview

- **File**: `ai_generation/skill_registry.py`
- **Lines**: 97
- **Classes**: 1
- **Public Functions**: 1

## Classes

- `{{SkillRegistry}}`

## Public API

- `get_skill_registry()`

## Integration

- Part of the [[Architecture Overview|Unified AI Generation Platform]]
- Exposed via [[05-SDK/SDK Overview|SDK]] and [[06-MCP-Ecosystem/MCP Ecosystem Overview|MCP Tools]]
- Verified in [[02-Capability-Registry/Capability Registry Overview|Capability Registry]]

## Related

- [[Architecture Overview]]
- [[Capability Registry Overview]]
