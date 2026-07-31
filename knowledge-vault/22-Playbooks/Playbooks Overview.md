---
type: overview
module: playbooks
status: active
tags: [playbooks, overview, index]
---

# Playbooks Overview

## Recovery Playbooks

### GPU OOM Recovery (FLT-05)
1. Detect GPU OOM error
2. Record failure event
3. Reduce batch size by 50%
4. Enable quantization
5. Enable CPU offload
6. Retry generation
7. If failed, try alternative provider

### GPU Crash Recovery (FLT-06)
1. Detect GPU crash
2. Reset GPU state
3. Restart runtime
4. Restore checkpoint
5. Retry with fallback provider

### Runtime Crash Recovery (FLT-07)
1. Detect runtime crash
2. Restart runtime process
3. Restore from checkpoint
4. Resume execution

### Provider Down Recovery (FLT-09)
1. Detect connection errors
2. Exponential backoff retry
3. Failover to fallback provider
4. Alert on repeated failures

### Rate Limit Recovery (FLT-10)
1. Detect 429 / rate limit errors
2. Parse retry-after header
3. Reduce request rate
4. Reduce batch size
5. Retry after backoff

## Operational Playbooks

### New Provider Integration
1. Discover provider API
2. Add provider configuration
3. Register in provider registry
4. Add to capability matrix
5. Benchmark provider
6. Document in vault

### New Model Integration
1. Research model capabilities
2. Check license compatibility
3. Add model to registry
4. Create adapter
5. Benchmark model
6. Document in vault

## Related

- [[Failure Atlas Overview]]
- [[Quality Engineering Overview]]
- [[Operational Runbooks]]
