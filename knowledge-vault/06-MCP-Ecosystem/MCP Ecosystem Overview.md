---
type: overview
module: mcp
status: active
tags: [mcp, overview, index]
---

# MCP Ecosystem Overview

## 214 MCP Tools

The MCP (Model Context Protocol) ecosystem exposes all platform capabilities as structured tools.

## Unified MCP Server Registry

`configs/mcp_servers.json` is the single canonical MCP server registry:
**59 servers catalogued, 54 verified ready, 5 blocked** (verified against the
npm registry / PyPI JSON API on 2026-07-31). Every ready entry records an
install target, required env vars, and exposed tools. Surfaces:

- SDK: `ai.list_mcp_servers()`, `ai.get_mcp_server()`, `ai.get_mcp_registry_stats()`
- CLI: `python -m ai_generation.cli mcp-servers [--category|--status|--search]`
- MCP: `list_mcp_servers`, `get_mcp_server`, `validate_mcp_server`, `check_mcp_server_health`

## Tool Categories

### Generation Tools
- `generate_image`, `edit_image`, `generate_video`, `edit_video`
- `generate_audio`, `generate_music`, `clone_voice`, `enhance_audio`
- `generate_3d`, `generate_speech`

### Quality Tools
- `run_quality_gates`, `run_single_gate`, `review_code`
- `score_quality`, `generate_tests`, `analyze_coverage_gaps`
- `detect_flaky_tests`, `learn_pattern`, `find_patterns`

### Code Analysis Tools
- `scan_secrets`, `analyze_code_static`, `analyze_code_structural`
- `run_multi_agent_review`, `verify_pr`, `track_tech_debt`
- `detect_code_smells`, `suggest_refactoring`
- `run_quality_dashboard`, `get_quality_history`, `get_quality_stats`

### Orchestration Tools
- `run_orchestration_pipeline`, `plan_agents`
- `add_kb_entry`, `retrieve_kb`

### Provider Tools
- `list_providers`, `get_provider_health`, `discover_providers`

### System Tools
- `get_system_stats`, `get_capability_matrix`, `get_benchmark_results`

## Usage

```python
from ai_generation.mcp_tools import MCPGenerationTools

tools = MCPGenerationTools()
result = await tools.handle("scan_secrets", {"code": "API_KEY = 'sk-...'"})
```

## Related

- [[Architecture Overview]]
- [[SDK Overview]]
- [[Quality Engineering Overview]]
