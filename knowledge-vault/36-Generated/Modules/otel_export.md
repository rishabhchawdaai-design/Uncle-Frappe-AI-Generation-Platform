---
module: "otel_export"
type: module-doc
status: active
owner: ""
lines: 473
classes: 8
functions: 0
tags: [module, documentation]
generated: "2026-07-31"
---

# otel_export

> OpenTelemetry Export — OTLP metrics, traces, logs export.

Based on ACOS Research: Observability Research
Provides OTLP (OpenTelemetry Protocol) exporters for Prometheus, Grafana, Tempo, Loki.

## Overview

- **File**: `ai_generation/otel_export.py`
- **Lines**: 473
- **Classes**: 8
- **Public Functions**: 0

## Classes

- `{{OTLPTransport}}`
- `{{SignalType}}`
- `{{OTLPConfig}}`
- `{{ExportResult}}`
- `{{OTLPMetricsExporter}}`
- `{{OTLPTracesExporter}}`
- `{{OTLPLogsExporter}}`
- `{{OTLPExporterManager}}`

## Integration

- Part of the [[Architecture Overview|Unified AI Generation Platform]]
- Exposed via [[05-SDK/SDK Overview|SDK]] and [[06-MCP-Ecosystem/MCP Ecosystem Overview|MCP Tools]]
- Verified in [[02-Capability-Registry/Capability Registry Overview|Capability Registry]]

## Related

- [[Architecture Overview]]
- [[Capability Registry Overview]]
