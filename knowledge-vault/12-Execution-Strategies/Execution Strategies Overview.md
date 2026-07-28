---
type: overview
module: execution-strategies
status: active
tags: [execution, strategies, overview]
---

# Execution Strategies Overview

## Strategy Types

| Strategy | Purpose | Use Case |
|----------|---------|----------|
| Sequential | Single-provider execution | Simple tasks |
| Parallel | Multi-provider execution | Speed-critical tasks |
| Fallback | Primary + backup providers | Reliability-critical tasks |
| Consensus | Multiple providers agree | Quality-critical tasks |
| Adaptive | Dynamic strategy selection | Unknown workloads |
| Cost-Optimized | Minimize cost | Budget-constrained tasks |
| Quality-Optimized | Maximize quality | Quality-critical tasks |
| Latency-Optimized | Minimize latency | Time-critical tasks |

## Strategy Selection

The Execution Engine selects strategies based on:

1. **Task Requirements** — Quality, latency, cost constraints
2. **Provider Availability** — Which providers are healthy
3. **Historical Performance** — Past provider performance
4. **Current Load** — Provider current utilization
5. **Cost Budget** — Available budget for the task

## Strategy Configuration

```python
from ai_generation.execution_strategies import ExecutionStrategies

strategies = ExecutionStrategies(config={
    "default_strategy": "adaptive",
    "fallback_enabled": True,
    "consensus_threshold": 0.8,
    "max_parallel": 5,
})
```

## Related

- [[Execution Engine Overview]]
- [[Negotiation Engine Overview]]
- [[Provider Registry Overview]]
