---
type: dashboard
tags: [dashboard, research, integration, traceability]
---

# Research Integration Dashboard

> Live view of the research ↔ implementation ecosystem. Canonical sources:
> ACOS-Research (knowledge), Capability Registry (status), this vault (human layer).

## Ecosystem Snapshot

| Metric | Value |
|--------|-------|
| Research documents indexed | 57 |
| Registry capabilities | 251 |
| Verified (eligible 204/204) | 204 |
| Blocked (external dependency) | 47 |
| Modules | 65 |
| MCP tools | 210 |
| Tests | 1,156 |
| Capabilities mapped to research | 251 / 251 |
| Research documents with implementation links | 39 |
| Queue: satisfied / blocked / speculative / implementable | 37 / 19 / 1 / 0 |

## Capabilities by Research Source

```dataview
TABLE length(rows) AS "Capabilities"
FROM "36-Generated/Capabilities"
WHERE type = "capability"
GROUP BY source
SORT length(rows) DESC
```

## Capabilities by Status

```dataview
TABLE length(rows) AS "Count"
FROM "36-Generated/Capabilities"
WHERE type = "capability"
GROUP BY status
SORT status
```

## Research to Implementation Mapping

```dataview
TABLE WITHOUT ID capability_id AS "ID", capability AS "Capability", source AS "Research Source", status AS "Status"
FROM "36-Generated/Capabilities"
WHERE type = "capability" AND status = "verified"
SORT capability_id
LIMIT 50
```

## Traceability Tooling

| Tool | Purpose |
|------|---------|
| `python -m ai_generation.cli research-trace <ID>` | Capability → research/modules/tests/SDK/MCP/commit |
| `python -m ai_generation.cli research-impact <RESEARCH_ID>` | Implementation blast radius |
| `python -m ai_generation.cli research-graph` | Traversable ecosystem graph (~900 nodes / ~1,300 edges) |
| `scripts/research-sync.sh --check` | Pending research change check |
| MCP: `research_index`, `trace_capability`, `research_impact_analysis`, `research_sync_status`, `research_graph` | Agent-accessible traceability |

## Related

- [[24-Research/Research Integration|Research Integration]]
- [[02-Capability-Registry/Capability Registry Overview|Capability Registry]]
- [[22-Playbooks/Research Sync Runbook|Research Sync Runbook]]
- [[Architecture Overview]]
