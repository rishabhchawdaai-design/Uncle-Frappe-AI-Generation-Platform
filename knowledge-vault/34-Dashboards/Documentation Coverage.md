---
type: dashboard
tags: [dashboard, documentation, coverage]
---

# Documentation Coverage Dashboard

## Module Documentation

```dataview
TABLE line_count AS "Lines", length(classes) AS "Classes", length(functions) AS "Functions"
FROM "36-Generated/Modules"
WHERE module
SORT line_count DESC
```

## Documentation Status

| Category | Status | Coverage |
|----------|--------|----------|
| Architecture Overview | ✅ Complete | 100% |
| Module Documentation | ✅ Auto-generated | 100% |
| API Documentation | ✅ Via SDK | 100% |
| ADR Index | ✅ Created | Ready |
| Quality Engineering | ✅ Complete | 100% |
| Security Overview | ✅ Complete | 100% |
| Testing Overview | ✅ Complete | 100% |
| Failure Atlas | ✅ Complete | 100% |
| Roadmap | ✅ Complete | 100% |

## Dataview Queries Available

- Module listing with stats
- Capability status by domain
- Architecture decision records
- Technical debt tracking
- Quality engineering metrics
- Test results summary
- Provider health status
- Benchmark results

## Related

- [[Quality Engineering Overview]]
- [[Architecture Overview]]
