---
type: dashboard
tags: [dashboard, intelligence, system]
---

# Platform Intelligence Dashboard

## System Overview

```dataview
TABLE WITHOUT ID
  "66" AS "Modules",
  "1,216" AS "Tests",
  "206" AS "MCP Tools",
  "204" AS "Verified Capabilities",
  "47" AS "Blocked (External)"
FROM "34-Dashboards"
LIMIT 1
```

## Module Health

```dataview
TABLE line_count AS "Lines", length(classes) AS "Classes", length(functions) AS "Functions"
FROM "36-Generated/Modules"
WHERE module
SORT line_count DESC
LIMIT 15
```

## Quality Summary

| Dimension | Status |
|-----------|--------|
| Security | ✅ Secret scanner + static analysis |
| Code Review | ✅ Multi-agent (6 roles) |
| Quality Gates | ✅ Swiss Cheese Model (8 gates) |
| Refactoring | ✅ 20 smell types + techniques |
| Tech Debt | ✅ Tracked in registry |
| Testing | ✅ 1,216 tests passing |

## Capability Status by Domain

```dataview
TABLE status
FROM "36-Generated/Capabilities"
WHERE status
GROUP BY status
```

## Blocked Capabilities

```dataview
TABLE source
FROM "36-Generated/Capabilities"
WHERE status = "blocked"
SORT file.name ASC
LIMIT 15
```

## Recent Activity

```dataview
TABLE date, summary
FROM "26-Project-Journal"
WHERE type = "journal"
SORT date DESC
LIMIT 5
```

## Next Priorities

1. Docker containerization
2. CI/CD pipeline
3. Automated benchmarking
4. Kubernetes support
5. Lip sync / avatar generation

## Related

- [[Capabilities Dashboard]]
- [[System Health Dashboard]]
- [[Architecture Risks Dashboard]]
- [[Documentation Coverage]]
