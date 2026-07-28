---
type: overview
module: performance
status: active
tags: [performance, overview]
---

# Performance Overview

## Performance Components

| Component | Module | Purpose |
|-----------|--------|---------|
| BenchmarkEngine | `benchmark_engine.py` | Core benchmarking |
| BenchmarkLab | `benchmark_lab.py` | Lab experiments |
| CinemaBenchmark | `cinema_benchmark.py` | Cinematic quality |
| RegressionDetector | `regression_detector.py` | Statistical regression |
| ExecutionEngine | `execution_engine.py` | Task execution |
| AutoRouter | `auto_router.py` | Intelligent routing |
| NegotiationEngine | `negotiation_engine.py` | Provider negotiation |

## Benchmark Types

| Type | Purpose |
|------|---------|
| Latency | Response time measurement |
| Throughput | Requests per second |
| Quality | Output quality scoring |
| Cost | Cost per generation |
| Reliability | Success rate tracking |
| Regression | Quality degradation detection |

## Performance Dashboard

```dataview
TABLE latency_ms, quality_score, cost_per_generation
FROM "36-Generated"
WHERE type = "benchmark-result"
SORT latency_ms ASC
```

## Related

- [[Benchmark Overview]]
- [[Architecture Overview]]
- [[Quality Engineering Overview]]
