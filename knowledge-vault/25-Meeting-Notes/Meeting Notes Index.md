---
type: index
tags: [meeting, index]
---

# Meeting Notes Index

## Create New Meeting Note

Use the Templater template: `35-Templates/Meeting-Note.md`

## Recent Meetings

```dataview
TABLE date, attendees
FROM "25-Meeting-Notes"
WHERE type = "meeting"
SORT date DESC
```

## Related

- [[HOME]]
- [[Project Journal]]
- [[Roadmap Overview]]
