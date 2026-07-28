---
type: overview
module: execution-engine
status: active
tags: [execution, engine, overview]
---

# Execution Engine Overview

## Execution Flow

```mermaid
graph LR
    A[Request] --> B[Intent Analysis]
    B --> C[Task Classification]
    C --> D[Capability Discovery]
    D --> E[Constraint Analysis]
    E --> F[Strategy Planning]
    F --> G[Backend Selection]
    G --> H[Generation]
    H --> I[Evaluation]
    I --> J[Refinement]
    J --> K[Delivery]
```

## Components

| Component | Module | Purpose |
|-----------|--------|---------|
| ExecutionEngine | `execution_engine.py` | Core execution |
| WorkflowEngine | `workflow_engine.py` | Multi-step workflows |
| AutoRouter | `auto_router.py` | Intelligent routing |
| AgentPlanner | `agent_planner.py` | Task planning |
| NegotiationEngine | `negotiation_engine.py` | Provider negotiation |
| DynamicAdapter | `dynamic_adapter.py` | Runtime adaptation |

## Execution Strategies

| Strategy | Purpose |
|----------|---------|
| Sequential | Single-provider execution |
| Parallel | Multi-provider execution |
| Fallback | Primary + backup providers |
| Consensus | Multiple providers agree |
| Adaptive | Dynamic strategy selection |

## Related

- [[Architecture Overview]]
- [[Negotiation Engine Overview]]
- [[Execution Strategies Overview]]
