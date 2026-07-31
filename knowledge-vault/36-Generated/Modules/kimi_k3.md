---
module: "kimi_k3"
type: module-doc
status: active
owner: ""
lines: 1594
classes: 9
functions: 15
tags: [module, documentation]
generated: "2026-07-31"
---

# kimi_k3

> Kimi K3 Integration — Moonshot AI Kimi K3 as an execution runtime.

Kimi K3 is an open-weight multimodal reasoning model (text + image) with a
1,048,576-token context window. This module makes the pla

## Overview

- **File**: `ai_generation/kimi_k3.py`
- **Lines**: 1594
- **Classes**: 9
- **Public Functions**: 15

## Classes

- `{{KimiK3Error}}`
- `{{KimiK3Client}}`
- `{{KimiK3CloudClient}}`
- `{{KimiK3VllmServer}}`
- `{{KimiK3SglangServer}}`
- `{{KimiK3Request}}`
- `{{KimiK3Result}}`
- `{{KimiK3Manager}}`
- `{{_BenchmarkRecord}}`

## Public API

- `build_chat_messages()`
- `build_chat_payload()`
- `parse_chat_response()`
- `build_vllm_command()`
- `build_sglang_command()`
- `register_kimi_k3()`
- `register_kimi_k3_health()`
- `register_kimi_k3_graph()`
- `kimi_k3_capabilities()`
- `kimi_k3_candidates()`
- `build_vllm_docker_run()`
- `build_sglang_docker_run()`
- `register_kimi_k3_capability_graph()`
- `build_vllm_k8s_yaml()`
- `build_sglang_k8s_yaml()`

## Integration

- Part of the [[Architecture Overview|Unified AI Generation Platform]]
- Exposed via [[05-SDK/SDK Overview|SDK]] and [[06-MCP-Ecosystem/MCP Ecosystem Overview|MCP Tools]]
- Verified in [[02-Capability-Registry/Capability Registry Overview|Capability Registry]]

## Related

- [[Architecture Overview]]
- [[Capability Registry Overview]]
