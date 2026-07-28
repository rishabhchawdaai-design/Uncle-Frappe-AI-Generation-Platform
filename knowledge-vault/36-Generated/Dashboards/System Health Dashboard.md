---
type: dashboard
tags: [dashboard, health]
---

# System Health Dashboard

## Module Status

```dataview
TABLE line_count AS "Lines", length(classes) AS "Classes", length(functions) AS "Functions"
FROM "36-Generated/Modules"
WHERE module
SORT line_count DESC
```

## Quality Engineering Overview

```dataview
TABLE status, findings_count, grade
FROM "36-Generated"
WHERE type = "quality-engineering"
SORT grade ASC
```

## Recent Changes

```dataview
TABLE date, summary
FROM "26-Project-Journal"
WHERE type = "journal"
SORT date DESC
LIMIT 10
```
