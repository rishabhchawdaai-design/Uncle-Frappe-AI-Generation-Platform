---
type: overview
module: benchmarking
status: active
tags: [benchmark, overview]
---

# Benchmark Overview

## Benchmark Engines

| Engine | Module | Purpose |
|--------|--------|---------|
| BenchmarkEngine | `benchmark_engine.py` | Core benchmarking |
| BenchmarkLab | `benchmark_lab.py` | Lab experiments |
| CinemaBenchmark | `cinema_benchmark.py` | Cinematic quality |
| RegressionDetector | `regression_detector.py` | Statistical regression |

## Benchmark Types

### Provider Benchmarks
- Response latency
- Output quality
- Cost efficiency
- Reliability

### Model Benchmarks
- Image quality (FID, CLIP)
- Video quality (FVD, LPIPS)
- Audio quality (PESQ, MOS)
- Text quality (BLEU, ROUGE)

### System Benchmarks
- Throughput (requests/second)
- Concurrency (simultaneous requests)
- Memory usage
- GPU utilization

## Benchmark Results

```dataview
TABLE provider, model, latency_ms, quality_score
FROM "36-Generated"
WHERE type = "benchmark-result"
SORT quality_score DESC
```

## Regression Detection

The RegressionDetector monitors:
- Quality score changes
- Latency increases
- Cost changes
- Reliability drops

## Related

- [[Quality Engineering Overview]]
- [[Performance Overview]]
- [[Architecture Overview]]
