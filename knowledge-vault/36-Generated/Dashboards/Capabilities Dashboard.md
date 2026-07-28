---
type: dashboard
tags: [dashboard, capabilities]
---

# Capabilities Dashboard

## Status Summary

```dataview
TABLE WITHOUT ID
  length(filter(rows, (r) => r.status = "verified")) AS "Verified",
  length(filter(rows, (r) => r.status = "blocked")) AS "Blocked",
  length(rows) AS "Total"
FROM "36-Generated/Capabilities"
WHERE status
GROUP BY true
```

## All Capabilities

```dataview
TABLE status, source
FROM "36-Generated/Capabilities"
WHERE status
SORT file.name ASC
```
