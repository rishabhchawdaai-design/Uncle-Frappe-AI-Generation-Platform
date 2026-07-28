---
type: tracker
status: active
tags: [debt, tracker]
---

# Technical Debt Tracker

## Current Debt

```dataview
TABLE category, priority, status
FROM "28-Technical-Debt"
WHERE status != "resolved"
SORT priority ASC
```

## Debt Categories

- **Code Smells**: Bare excepts, star imports, magic numbers
- **TODOs**: Unresolved comments
- **FIXMEs**: Known issues requiring fix
- **HACKs**: Temporary workarounds
- **Missing Documentation**: Undocumented functions
- **Type Ignore**: Suppressed type errors

## Related

- [[Quality Engineering Overview]]
- [[Architecture Overview]]
- [[Capabilities Dashboard]]
