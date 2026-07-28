---
type: overview
module: failure-atlas
status: active
tags: [failure, atlas, overview]
---

# Failure Atlas Overview

## Failure Types & Recovery

| Type | Detection | Recovery |
|------|-----------|----------|
| GPU OOM | Error pattern matching | Batch reduction, quantization, CPU offload |
| GPU Crash | Error pattern matching | Reset, restart, fallback |
| Runtime Crash | Error pattern matching | Restart, checkpoint restore |
| NaN/Inf | Tensor inspection | Revert, skip, adjust LR |
| Provider Down | Connection errors | Retry, backoff, failover |
| Rate Limit | HTTP 429 / keywords | Wait, reduce rate, batch size |

## Recovery Statistics

```dataview
TABLE total_events, total_recoveries, successful, failed
FROM "36-Generated"
WHERE type = "recovery-stats"
```

## Related

- [[Architecture Overview]]
- [[Quality Engineering Overview]]
- [[Playbooks Overview]]
