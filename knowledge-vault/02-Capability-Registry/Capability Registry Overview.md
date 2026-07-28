---
type: registry
status: active
tags: [capability, registry, index]
---

# Capability Registry

> **Source of truth for all platform capabilities and their implementation status.**

## Completion Status

```dataview
TABLE WITHOUT ID
  length(filter(rows, (r) => r.status = "VERIFIED")) AS "Verified",
  length(filter(rows, (r) => r.status = "BLOCKED")) AS "Blocked",
  length(rows) AS "Total"
FROM "02-Capability-Registry"
WHERE status
GROUP BY true
```

## All Capabilities by Domain

```dataview
TABLE status, module, source
FROM "02-Capability-Registry"
WHERE status
SORT file.name ASC
```

## Blocked Capabilities

```dataview
TABLE module, source, reason
FROM "02-Capability-Registry"
WHERE status = "BLOCKED"
SORT file.name ASC
```

## VERIFIED Capabilities

```dataview
TABLE module, source
FROM "02-Capability-Registry"
WHERE status = "VERIFIED"
SORT file.name ASC
```

## Domain Summary

| Domain | Verified | Blocked | Total |
|--------|----------|---------|-------|
| Image Generation | 13 | 0 | 13 |
| Image Editing | 8 | 0 | 8 |
| Video Generation | 7 | 2 | 9 |
| Audio Generation | 9 | 1 | 10 |
| OCR & Document | 10 | 0 | 10 |
| Search Systems | 11 | 0 | 11 |
| Routing & Negotiation | 9 | 0 | 9 |
| Execution Engine | 10 | 0 | 10 |
| Fault Tolerance | 8 | 0 | 8* |
| Benchmarking | 5 | 0 | 5* |
| Quality Engineering | 20 | 0 | 20 |
| Core Platform | 20 | 0 | 20 |
| Others | Various | Various | Various |

> *Some capabilities promoted from INTEGRATED to VERIFIED in latest batch.
