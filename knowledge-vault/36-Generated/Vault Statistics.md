---
type: statistics
generated: "2026-07-28"
tags: [statistics, generated]
---

# Vault Statistics

## Overview

| Metric | Value |
|--------|-------|
| Total Knowledge Pages | 345+ |
| Module Documentation | 64 |
| Capability Pages | 255 |
| Architecture Layer Pages | 13 |
| Dashboard Pages | 6 |
| Templates | 5 |
| Excalidraw Diagrams | 2 |
| Kanban Boards | 1 |

## Vault Structure

```
uncle-frappe-knowledge-vault/
├── HOME.md                           # Main entry point
├── 00-Inbox/                         # Unsorted notes
├── 01-Architecture/                  # Architecture docs
│   ├── Architecture Overview.md
│   └── Decision-Records/             # ADRs
├── 02-Capability-Registry/           # Capability docs
├── 03-Execution-Engine/              # Execution docs
├── 04-Negotiation-Engine/            # Negotiation docs
├── 05-SDK/                           # SDK docs
├── 06-MCP-Ecosystem/                 # MCP docs
├── 07-Skills/                        # Skills docs
├── 08-Plugins/                       # Plugin docs
├── 09-Providers/                     # Provider docs
├── 10-Models/                        # Model docs
├── 11-Runtime-Registry/              # Runtime docs
├── 12-Execution-Strategies/          # Strategy docs
├── 13-Quality-Engineering/           # QE docs
├── 14-Testing/                       # Test docs
├── 15-Benchmarks/                    # Benchmark docs
├── 16-Observability/                 # Observability docs
├── 17-Security/                      # Security docs
├── 18-Infrastructure/                # Infra docs
├── 19-Networking/                    # Network docs
├── 20-Performance/                   # Performance docs
├── 21-Failure-Atlas/                 # Failure docs
├── 22-Playbooks/                     # Playbook docs
├── 23-Roadmaps/                      # Roadmap docs
├── 24-Research/                      # Research docs
├── 25-Meeting-Notes/                 # Meeting docs
├── 26-Project-Journal/               # Journal docs
├── 27-Release-Notes/                 # Release docs
├── 28-Technical-Debt/                # Debt docs
├── 29-Future-Ideas/                  # Future docs
├── 30-Developer-Guides/              # Dev guides
├── 31-API-Documentation/             # API docs
├── 32-Operational-Runbooks/          # Runbook docs
├── 33-Visual-Docs/                   # Excalidraw diagrams
├── 34-Dashboards/                    # Dataview dashboards
├── 35-Templates/                     # Templater templates
├── 36-Generated/                     # Auto-generated content
│   ├── Modules/                      # 64 module pages
│   ├── Capabilities/                 # 255 capability pages
│   ├── Dashboards/                   # Architecture dashboards
│   ├── Module Summary.md
│   └── Vault Statistics.md
└── 37-Pipeline/                      # Knowledge pipeline
    └── generate_vault.py
```

## Plugin Status

| Plugin | Status | Purpose |
|--------|--------|---------|
| Dataview | ✅ Configured | Engineering database |
| Juggl | ✅ Configured | Graph visualization |
| Excalidraw | ✅ Configured | Visual documentation |
| Obsidian Git | ✅ Configured | Version control |
| Templater | ✅ Configured | Template engine |
| Kanban | ✅ Configured | Project management |
| DB Folder | ✅ Configured | Database views |
| Breadcrumbs | ✅ Configured | Navigation |
| Link Exploder | ✅ Configured | Link analysis |
| Metadata Menu | ✅ Configured | Metadata management |

## Dataview Dashboards

1. **HOME.md** — System status, capabilities, ADRs, journal
2. **Capabilities Dashboard** — All capabilities by status
3. **ADR Dashboard** — Architecture decision records
4. **System Health Dashboard** — Module status, quality metrics
5. **Documentation Coverage** — Documentation status
6. **Architecture Risks** — Risk matrix, blocked capabilities

## Knowledge Pipeline

The automated pipeline (`37-Pipeline/generate_vault.py`) generates:
- Module documentation from Python source
- Capability pages from CAPABILITY_REGISTRY.md
- Architecture layer pages
- Dataview-compatible dashboards
- Module summaries with statistics

Run with:
```bash
python3 37-Pipeline/generate_vault.py
```

## Related

- [[Architecture Overview]]
- [[Capability Registry Overview]]
- [[Quality Engineering Overview]]
