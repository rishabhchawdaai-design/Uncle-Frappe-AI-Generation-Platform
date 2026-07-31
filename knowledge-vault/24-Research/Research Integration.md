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
| Capability mapping | `DOMAIN_ALIASES` + registry parsing | 253 capabilities → 57 research docs |
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

## Cross-References & Satisfaction

Every research document knows which capabilities implement it. Registry
capabilities keep exactly one canonical research source (`DOMAIN_ALIASES`);
documents whose implementation lives under a different domain additionally
reference those capabilities via the satisfaction table:

- `CHAPTER_10_GLOBAL_BENCHMARK_INTELLIGENCE` -> `BMK-01..BMK-08`, `PLT-15`
- `COMPATIBILITY_MATRIX` -> `CGR-03/CGR-04/CGR-07`, `RUN-01..RUN-11`
- `SECURITY_THREAT_MODEL` -> `SEC-03..SEC-07`, `SEC-12`, `RTG-05`
- `CHAPTER_03_UNIVERSAL_WORKFLOW_COMPILER` -> `WFL-01/WFL-03`, `PLT-16/19/20`
- `CHAPTER_06_ADAPTIVE_SCHEDULER` -> `EXE-01..EXE-04/EXE-10`, `RUN-12`, `PLT-06`
- `CHAPTER_07_UNIVERSAL_AGENT_KERNEL` -> `PLT-01/08/16/17`, `RTG-08`, `OBS-02`
- `CHAPTER_11_MULTI_STAGE_GENERATION_ENGINE` -> `PLT-11/18/20`, `WFL-01/03`
- `CHAPTER_12_AUTONOMOUS_OPTIMIZATION_LOOP` -> `PLT-18`, `BMK-04/06/07/08`, `PLT-15`
- `CHAPTER_13_OBSERVABILITY_DIGITAL_TWIN` -> `OBS-01..OBS-07`, `PLT-06`
- `EXECUTION_GRAPH_SCHEMA` -> `PLT-20`, `WFL-01/03`, `PLT-16/09`, `EXE-01`
- `SCHEDULING_POLICY_SPECIFICATION` -> `EXE-01/02`, `RUN-12`, `PLT-06`
- `CHAPTER_01_UNIVERSAL_COMPUTE_GRAPH` -> `CGR-01/04/05/07`, `WFL-01`, `EXE-01`, `RUN-12`
- `CHAPTER_08_PLUGIN_OPERATING_SYSTEM` -> `PLG-01..PLG-10`, `SEC-01/02/07/10`
- `MODEL_CAPABILITY_REGISTRY` -> `CGR-02/03`, `RUN-12`, `PLT-15`
- `WORKFLOW_CAPABILITY_REGISTRY` -> `WFL-01/02/03`, `PLT-11`

Impact analysis (`research-impact`) unions both directions, so changing any
research document reports the complete implementation blast radius.

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
