---
type: overview
module: runtime-registry
status: active
tags: [runtime, registry, overview]
---

# Runtime Registry Overview

## Runtime Categories

### Local Runtimes
| Runtime | Module | Purpose |
|---------|--------|---------|
| ComfyUI | `local_runtimes.py` | Image generation |
| Stable Diffusion WebUI | `local_runtimes.py` | Image generation |
| Ollama | `local_runtimes.py` | LLM inference |
| llama.cpp | `local_runtimes.py` | LLM inference |

### Remote Endpoints
| Endpoint | Module | Purpose |
|----------|--------|---------|
| Pollinations | `remote_endpoints.py` | Free image generation |
| HuggingFace | `remote_endpoints.py` | Model hosting |
| Together AI | `remote_endpoints.py` | Inference API |
| Replicate | `remote_endpoints.py` | Model deployment |

### Agent Backends
| Backend | Module | Purpose |
|---------|--------|---------|
| Claude Code | `agent_interface.py` | Agent execution |
| Codex | `agent_interface.py` | Agent execution |
| Cursor | `agent_interface.py` | Agent execution |

## Runtime Health

```dataview
TABLE healthy, latency_ms, last_check
FROM "36-Generated"
WHERE type = "runtime-health"
SORT healthy DESC
```

## Related

- [[Architecture Overview]]
- [[Provider Registry Overview]]
- [[Execution Engine Overview]]
