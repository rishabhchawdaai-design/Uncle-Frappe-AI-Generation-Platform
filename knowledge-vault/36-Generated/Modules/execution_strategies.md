---
module: "execution_strategies"
type: module-doc
status: active
owner: ""
lines: 489
classes: 15
functions: 2
tags: [module, documentation]
generated: "2026-07-28"
---

# execution_strategies

> Execution Strategies — CPU Offload, Tensor Parallelism, Pipeline Parallelism.

Based on ACOS Research: Execution Strategy Library
Implements execution strategies for model inference with fallback chai

## Overview

- **File**: `ai_generation/execution_strategies.py`
- **Lines**: 489
- **Classes**: 15
- **Public Functions**: 2

## Classes

- `{{StrategyType}}`
- `{{StrategyStatus}}`
- `{{HardwareProfile}}`
- `{{ModelRequirements}}`
- `{{ExecutionPlan}}`
- `{{ExecutionStrategy}}`
- `{{CPUOffloadStrategy}}`
- `{{DiskOffloadStrategy}}`
- `{{SingleGPUStrategy}}`
- `{{TensorParallelStrategy}}`
- `{{PipelineParallelStrategy}}`
- `{{ExpertParallelStrategy}}`
- `{{DataParallelStrategy}}`
- `{{SequenceParallelStrategy}}`
- `{{StrategySelector}}`

## Public API

- `create_cpu_offload_plan()`
- `create_execution_plan()`

## Integration

- Part of the [[Architecture Overview|Unified AI Generation Platform]]
- Exposed via [[05-SDK/SDK Overview|SDK]] and [[06-MCP-Ecosystem/MCP Ecosystem Overview|MCP Tools]]
- Verified in [[02-Capability-Registry/Capability Registry Overview|Capability Registry]]

## Related

- [[Architecture Overview]]
- [[Capability Registry Overview]]
