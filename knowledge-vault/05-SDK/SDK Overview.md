---
type: overview
module: sdk
status: active
tags: [sdk, overview, index]
---

# SDK Overview

## UncleFrappeAI — The Unified SDK

The `UncleFrappeAI` class is the single entry point for all platform capabilities.

## Initialization

```python
from ai_generation import UncleFrappeAI

ai = UncleFrappeAI(config={
    "max_retries": 3,
    "timeout": 30,
    "quality_gates": True,
})
```

## Capability Domains

### Generation
| Property | Returns | Purpose |
|----------|---------|---------|
| `generation_manager` | `GenerationManager` | AI generation orchestration |
| `prompt_engine` | `PromptEngine` | Prompt enhancement |
| `asset_intelligence` | `AssetIntelligence` | Asset analysis |

### Quality
| Property | Returns | Purpose |
|----------|---------|---------|
| `quality_gates` | `QualityGateEngine` | Quality gates |
| `code_review` | `CodeReviewEngine` | Code review |
| `quality_scoring` | `QualityScoringEngine` | Quality scoring |
| `quality_dashboard` | `QualityDashboard` | Unified quality report |

### Code Analysis
| Property | Returns | Purpose |
|----------|---------|---------|
| `secret_scanner` | `SecretScanner` | Secret detection |
| `static_analyzer` | `StaticAnalyzer` | Static analysis |
| `structural_analyzer` | `StructuralAnalyzer` | Structural analysis |
| `refactoring_engine` | `RefactoringEngine` | Refactoring suggestions |
| `debt_tracker` | `TechnicalDebtTracker` | Debt tracking |

### Orchestration
| Property | Returns | Purpose |
|----------|---------|---------|
| `orchestration_pipeline` | `OrchestrationPipeline` | Multi-agent pipeline |
| `knowledge_base` | `KnowledgeBaseContext` | RAG context |

### Execution
| Property | Returns | Purpose |
|----------|---------|---------|
| `execution_engine` | `ExecutionEngine` | Task execution |
| `workflow_engine` | `WorkflowEngine` | Workflows |
| `benchmark_engine` | `BenchmarkEngine` | Benchmarking |

### Providers
| Property | Returns | Purpose |
|----------|---------|---------|
| `provider_discovery` | `ProviderDiscovery` | Provider discovery |
| `provider_intelligence` | `ProviderIntelligence` | Provider analytics |
| `health_monitor` | `HealthMonitor` | Health monitoring |

## Related

- [[Architecture Overview]]
- [[API Reference]]
- [[MCP Ecosystem Overview]]
