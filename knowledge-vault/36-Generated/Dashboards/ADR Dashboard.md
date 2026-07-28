---
type: dashboard
tags: [dashboard, adr]
---

# Architecture Decision Records

## Recent ADRs

```dataview
TABLE date, status, module
FROM "01-Architecture/Decision-Records"
WHERE type = "adr"
SORT date DESC
```

## ADR Statistics

```dataview
TABLE WITHOUT ID
  length(filter(rows, (r) => r.status = "accepted")) AS "Accepted",
  length(filter(rows, (r) => r.status = "proposed")) AS "Proposed",
  length(rows) AS "Total"
FROM "01-Architecture/Decision-Records"
WHERE type = "adr"
GROUP BY true
```
