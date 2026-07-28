---
type: dashboard
tags: [dashboard, risk, architecture]
---

# Architecture Risks Dashboard

## Risk Matrix

```dataview
TABLE WITHOUT ID
  "47" AS "Blocked Capabilities (External Deps)",
  "0" AS "Implementation Gaps",
  "1,128" AS "Tests Passing",
  "198" AS "MCP Tools"
FROM "34-Dashboards"
LIMIT 1
```

## External Dependencies

The following capabilities are BLOCKED by external infrastructure:

### Cloud Infrastructure
- Kubernetes Orchestration
- Cloud Instance Management
- Cost Optimization
- Spot Instance Management

### Distributed Computing
- Ray Integration
- DeepSpeed
- PyTorch Distributed
- Petals

### Networking
- Cilium Service Mesh
- Istio Integration
- Linkerd
- Envoy Proxy

### Storage
- PostgreSQL
- Redis
- MinIO
- Qdrant

### Messaging
- NATS
- Kafka
- RabbitMQ
- Redis Streams

## Mitigation Strategy

1. **Graceful Degradation**: Local alternatives for all blocked capabilities
2. **Provider Fallback**: Automatic failover to available backends
3. **Progressive Enhancement**: Enable cloud capabilities when infrastructure is available

## Related

- [[Capability Registry Overview]]
- [[Architecture Overview]]
- [[Failure Atlas Overview]]
