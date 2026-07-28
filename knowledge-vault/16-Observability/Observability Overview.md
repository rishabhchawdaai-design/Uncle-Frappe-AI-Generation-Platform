---
type: overview
module: observability
status: active
tags: [observability, overview]
---

# Observability Overview

## Three Pillars

### Traces
- Request tracing across providers
- Execution flow visualization
- Latency breakdown

### Metrics
- Request count
- Success/failure rates
- Latency percentiles
- Cost tracking

### Logs
- Structured logging
- Error logging
- Audit logging

## Components

| Component | Module | Purpose |
|-----------|--------|---------|
| Observability | `observability.py` | Core observability |
| OtelExporter | `otel_export.py` | OpenTelemetry export |
| HealthMonitor | `health_monitor.py` | Health monitoring |
| DecisionLedger | `decision_ledger.py` | Decision audit |

## OpenTelemetry Integration

```python
from ai_generation.otel_export import OtelExporter

exporter = OtelExporter(config={
    "service_name": "uncle-frappe",
    "endpoint": "http://localhost:4317",
    "export_traces": True,
    "export_metrics": True,
})
```

## Health Monitoring

```dataview
TABLE provider, healthy, latency_ms, consecutive_failures
FROM "36-Generated"
WHERE type = "provider-health"
SORT healthy DESC
```

## Related

- [[Architecture Overview]]
- [[Performance Overview]]
- [[Security Overview]]
