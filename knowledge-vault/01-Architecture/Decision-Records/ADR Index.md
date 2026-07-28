---
type: index
tags: [adr, index]
---

# Architecture Decision Records

## Index

```dataview
TABLE date, status, module
FROM "01-Architecture/Decision-Records"
WHERE type = "adr"
SORT date DESC
```

## Create New ADR

Use the Templater template: `35-Templates/ADR-Template.md`

## Related

- [[Architecture Overview]]
- [[Capability Registry Overview]]
