---
type: index
tags: [home, index, dashboard]
---

# Uncle Frappe AI Generation Platform — Knowledge Vault

> **Single source of truth for engineering knowledge, architecture, and operational intelligence.**

## Quick Navigation

### Core Architecture
- [[01-Architecture/Architecture Overview|Architecture Overview]]
- [[01-Architecture/Decision-Records/ADR Index|Architecture Decision Records]]
- [[02-Capability-Registry/Capability Registry Overview|Capability Registry]]

### Platform Components
- [[03-Execution-Engine/Execution Engine Overview|Execution Engine]]
- [[04-Negotiation-Engine/Negotiation Engine Overview|Negotiation Engine]]
- [[05-SDK/SDK Overview|Unified SDK]]
- [[06-MCP-Ecosystem/MCP Ecosystem Overview|MCP Ecosystem]]

### Intelligence Layer
- [[07-Skills/Skills Overview|Skills]]
- [[08-Plugins/Plugin System Overview|Plugins]]
- [[09-Providers/Provider Registry Overview|Providers]]
- [[10-Models/Model Registry Overview|Models]]

### Infrastructure
- [[11-Runtime-Registry/Runtime Registry Overview|Runtimes]]
- [[12-Execution-Strategies/Execution Strategies Overview|Strategies]]
- [[18-Infrastructure/Infrastructure Overview|Infrastructure]]
- [[19-Networking/Networking Overview|Networking]]

### Quality & Reliability
- [[13-Quality-Engineering/Quality Engineering Overview|Quality Engineering]]
- [[14-Testing/Testing Overview|Testing]]
- [[15-Benchmarks/Benchmark Overview|Benchmarks]]
- [[16-Observability/Observability Overview|Observability]]
- [[17-Security/Security Overview|Security]]
- [[20-Performance/Performance Overview|Performance]]
- [[21-Failure-Atlas/Failure Atlas Overview|Failure Atlas]]

### Planning & Operations
- [[22-Playbooks/Playbooks Overview|Playbooks]]
- [[23-Roadmaps/Roadmap Overview|Roadmaps]]
- [[24-Research/Research Overview|Research]]
- [[25-Meeting-Notes|Meeting Notes]]
- [[26-Project-Journal/Project Journal|Project Journal]]
- [[27-Release-Notes/Release Notes|Release Notes]]
- [[28-Technical-Debt/Technical Debt Tracker|Technical Debt]]
- [[29-Future-Ideas/Future Ideas|Future Ideas]]

### Developer Resources
- [[30-Developer-Guides/Developer Guides|Developer Guides]]
- [[31-API-Documentation/API Documentation|API Documentation]]
- [[32-Operational-Runbooks/Operational Runbooks|Runbooks]]

---

## Live Dashboards

### System Status
```dataview
TABLE status, module, capability
FROM "02-Capability-Registry"
WHERE status = "VERIFIED"
SORT file.name ASC
LIMIT 25
```

### Architecture Decision Records
```dataview
TABLE date, status, module
FROM "01-Architecture/Decision-Records"
WHERE type = "adr"
SORT date DESC
LIMIT 10
```

### Technical Debt
```dataview
TABLE priority, category, status
FROM "28-Technical-Debt"
WHERE status != "resolved"
SORT priority ASC
LIMIT 15
```

### Recent Journal Entries
```dataview
TABLE date
FROM "26-Project-Journal"
WHERE type = "journal"
SORT date DESC
LIMIT 5
```
