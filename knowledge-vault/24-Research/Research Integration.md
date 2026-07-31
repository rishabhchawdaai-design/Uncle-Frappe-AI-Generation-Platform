---
type: research-integration
status: active
owner: platform
tags: [research, integration, traceability, graph, canonical]
---

# Research Integration Layer

> One engineering ecosystem: ACOS-Research is the canonical knowledge source,
> this platform is the canonical implementation. Research flows into
> implementation; implementation always references research.

## Purpose

The Research Integration Layer connects every capability in the Capability
Registry back to the research document that produced it — without duplicating
research content. The research repository (`ACOS-Research`) remains the
canonical upstream; the platform only indexes, references, and links it.

## Components

| Component | Implementation | Output |
|-----------|----------------|--------|
| Structured importer | `ai_generation/research_integration.py` | `data/research/research_manifest.json` |
| Structured index | `ResearchIntegrationEngine.build_index()` | `data/research/research_index.json` |
| Capability mapping | `DOMAIN_ALIASES` + registry parsing | 251 capabilities → 57 research docs |
| Traceability | `trace_capability(capability_id)` | Capability → research/modules/tests/SDK/MCP/commit |
| Impact analysis | `research_impact(research_id)` | Affected capabilities, modules, tests, docs |
| Change detection | `detect_changes()` | new / modified / removed research |
| Autonomous queue | `sync()` | `data/research/execution_queue.json` |
| Implementation graph | `implementation_graph()` | ~900 nodes / ~1,300 edges, traversable |

## Traceability Contract

Every capability knows:

- Research document (id, title, category, sha256, commit)
- Implementation modules and their tests
- SDK interfaces and MCP tools
- Benchmarks and knowledge vault page
- Capability Registry entry and introducing commit

## Usage

### SDK

```python
ai = UncleFrappeAI()
trace = ai.trace_capability("SEC-05")   # full traceability record
impact = ai.research_impact("SECURITY_CANON")  # implementation blast radius
ai.research_sync_status()               # pending research changes
ai.research_graph()                     # traversable ecosystem graph
```

### CLI

```bash
python -m ai_generation.cli research-index
python -m ai_generation.cli research-trace SEC-05
python -m ai_generation.cli research-impact SECURITY_CANON
python -m ai_generation.cli research-sync
python -m ai_generation.cli research-graph
```

### MCP Tools

`research_index`, `trace_capability`, `research_impact_analysis`,
`research_sync_status`, `research_graph`.

## Synchronization Policy

- Research content is never copied into this repository — only hashes and metadata.
- `research-sync` detects changes, refreshes the index, and classifies new
  research as `implementable`, `blocked`, or `speculative` in the execution queue.
- Blocked items record the external dependency (credentials, licensing,
  hardware, unavailable service).
- The Capability Registry remains the source of truth for capability status.

## Related

- [[Research Overview]]
- [[02-Capability-Registry/Capability Registry Overview|Capability Registry]]
- [[36-Generated/Modules/research_integration|research_integration module]]
- [[Architecture Overview]]
