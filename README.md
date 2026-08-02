# Uncle Frappé — AI Generation Platform

> The canonical source for the AI Generation Platform. This repository owns all production code, providers, SDKs, APIs, and infrastructure.

## Overview

Uncle Frappé is an agent-first AI media orchestration platform capable of:

- **Image Generation** — Multiple providers, automatic failover, quality evaluation
- **Video Generation** — Text-to-video, image-to-video workflows
- **Audio Generation** — Speech, music, sound effects
- **Image Editing** — Inpainting, outpainting, background removal, style transfer
- **OCR & Document AI** — Text extraction, document understanding
- **Intelligent Routing** — Automatic provider selection, benchmarking, cost optimization
- **Multi-Provider** — OpenAI, HuggingFace, Replicate, Together, Fal, Pollinations, Stability, and more
- **Kimi K3 (Moonshot AI)** — 1M-context multimodal reasoning via official cloud API, vLLM, and SGLang execution paths

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                  Unified SDK / CLI / MCP             │
├─────────────────────────────────────────────────────┤
│              Generation Manager                      │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐            │
│  │ Prompt   │ │ Workflow │ │ Quality  │            │
│  │ Engine   │ │ Engine   │ │ Engine   │            │
│  └──────────┘ └──────────┘ └──────────┘            │
├─────────────────────────────────────────────────────┤
│              Provider Layer                          │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐    │
│  │ HF   │ │ Rep  │ │ Tog  │ │ Fal  │ │ Poll │    │
│  └──────┘ └──────┘ └──────┘ └──────┘ └──────┘    │
├─────────────────────────────────────────────────────┤
│              Execution Engine                        │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐            │
│  │ Routing  │ │ Failover │ │ Benchmark│            │
│  └──────────┘ └──────────┘ └──────────┘            │
└─────────────────────────────────────────────────────┘
```

## Kimi K3 (Moonshot AI)

The platform can use Kimi K3 as a chat/text-reasoning execution runtime through
every **officially supported** path:

| Path | Enable | Endpoint |
|------|--------|----------|
| Cloud API | `MOONSHOT_API_KEY` in `.env` | `kimi_k3_cloud` |
| Self-hosted vLLM | `KIMI_K3_VLLM_URL` in `.env` | `kimi_k3_vllm` |
| Self-hosted SGLang | `KIMI_K3_SGLANG_URL` in `.env` | `kimi_k3_sglang` |

```python
import asyncio
from ai_generation import UncleFrappeAI

async def main():
    ai = UncleFrappeAI()
    result = await ai.chat(
        "Explain Mixture of Experts",
        provider="auto",  # auto | kimi_k3_cloud | kimi_k3_vllm | kimi_k3_sglang
        reasoning_effort="high",  # low | high | max (official values)
    )
    print(result["text"])
    print(result["reasoning"])

asyncio.run(main())
```

CLI: `python -m ai_generation.cli kimi-chat "prompt"` · `kimi-info` · `kimi-health` · `kimi-benchmark`
Agent Interface: `await agent.chat("prompt", strategy="negotiate")`
Generation Manager: `await GenerationManager().generate_text("prompt")`
MCP tools: `kimi_k3_chat`, `kimi_k3_spec`, `kimi_k3_info`, `kimi_k3_health`, `kimi_k3_benchmark`

Kimi K3 specs and deployment recipes (TP/EP/PP, DSpark speculative decoding,
Blackwell/Hopper/AMD launch flags) are in `ai_generation/kimi_k3.py` and the
knowledge vault (`24-Research/Kimi K3.md`). Only official Moonshot AI paths are
supported; TensorRT-LLM, DeepSpeed, llama.cpp, Ollama, and HF TGI/Endpoints are
recorded as officially unsupported.

## Unified MCP Server Registry

The platform ships a canonical, verified MCP server registry
(`configs/mcp_servers.json`, single source of truth — no parallel registries).

- **59 servers catalogued** — 54 verified ready, 5 explicitly blocked (no stable verified distribution)
- Every ready entry records a verified install target (npm registry / PyPI JSON API audit) plus required env vars
- Categories: search, vector-db, ai-platform, infrastructure, version-control, browser, database, web, graph-db, and more

```bash
# CLI: browse the registry
python -m ai_generation.cli mcp-servers --category vector-db
python -m ai_generation.cli mcp-servers --search firecrawl
python -m ai_generation.cli mcp-servers --status blocked
```

```python
from ai_generation import UncleFrappeAI

ai = UncleFrappeAI()
servers = ai.list_mcp_servers(category="search")   # filtered list
server = ai.get_mcp_server("postgres")              # one entry (install cmd, env)
stats = ai.get_mcp_registry_stats()                 # totals + categories + env keys
```

MCP tools: `list_mcp_servers`, `get_mcp_server`.

Runtime validation (offline config checks + live probes):

```bash
python -m ai_generation.cli mcp-check ollama            # offline config validation
python -m ai_generation.cli mcp-check --all              # validate every entry offline
python -m ai_generation.cli mcp-check ollama --live      # spawn probe (5s window)
```

```python
report = ai.validate_mcp_server("postgres")     # command resolvable, env documented
probe = ai.check_mcp_server_health("ollama")    # live spawn probe
batch = ai.run_mcp_validation()                 # offline validation of all servers
```

MCP tools: `validate_mcp_server`, `check_mcp_server_health`.

## Unified Tool Registry

The platform catalogues the external code-quality toolchain in one canonical
registry (`configs/tools.json`) — distributions verified against the PyPI/npm
JSON API on 2026-07-31.

- **15 tools catalogued** — 10 ready (ruff, black, isort, pyright, mypy, bandit, semgrep, import-linter, eslint, prettier), 5 blocked (codeql, trivy, hadolint, archunit, sonarqube — no stable pip/npm distribution)
- Categories: lint, format, type-check, security, architecture, docker, quality

```bash
python -m ai_generation.cli tools --category security
python -m ai_generation.cli tools --search formatter
python -m ai_generation.cli tools --status blocked
```

```python
from ai_generation import UncleFrappeAI

ai = UncleFrappeAI()
tools = ai.list_tools(category="security")   # filtered list
tool = ai.get_tool("semgrep")                 # one entry (install, command, config)
stats = ai.get_tool_registry_stats()          # totals + categories
```

MCP tools: `list_tools`, `get_tool`.


## Unified Skill Registry

The platform ships a canonical, unified skill registry
(`configs/skills.json`, single source of truth — no parallel skill registries).

- **80 skills catalogued** — 78 ready, 2 blocked (proprietary/no public distribution)
- 40 platform-native skills map to verified modules (quality gates, code review, test generation, benchmarking, generation, security, runtimes)
- 38 external skill-pack references (Anthropic/Claude, OpenCode, OpenHands, MCP Market) across all objective categories
- Categories: architecture, refactoring, testing, TDD, security, benchmarking, profiling, performance, memory/GPU optimization, distributed systems, image/video/audio generation, prompt engineering, research, code review, git, CI/CD, Docker, Kubernetes, Python, TypeScript, FastAPI, PyTorch, Diffusers, Transformers, ONNX, TensorRT, MLX, llama.cpp, ComfyUI, Forge, A1111, SD.Next

```bash
python -m ai_generation.cli skills --category code-review
python -m ai_generation.cli skills --search benchmark
python -m ai_generation.cli skills --status blocked
```

```python
from ai_generation import UncleFrappeAI

ai = UncleFrappeAI()
skills = ai.list_skills(category="testing")     # filtered list
skill = ai.get_skill("quality_gate_runner")      # one entry (module, usage, source)
stats = ai.get_skill_registry_stats()            # totals + categories + sources
```

MCP tools: `list_skills`, `get_skill`.

## Quick Start

```python
import asyncio
from ai_generation import UncleFrappeAI

async def main():
    ai = UncleFrappeAI()

    # Generate an image with automatic provider selection
    result = await ai.generate_image(
        prompt="A cinematic coffee advertisement with warm lighting",
        style="photorealistic",
    )
    print(result.status, result.provider)

    # Generate a video
    video = await ai.generate_video("A city timelapse at dusk", duration_secs=4.0)
    print(video.status, video.provider)

    # Generate speech (TTS)
    speech = await ai.generate_speech("Hello from the platform")

    # Generate a 3D asset (truthful result: completed or exact reason)
    model3d = await ai.generate_3d("a red cube")
    print(model3d["status"], model3d["error"])

    # Enhance a prompt with cinematic techniques
    enhanced = ai.enhance_prompt("A luxury café interior", style="cinematic")
    print(enhanced.enhanced)


asyncio.run(main())
```

Run `python -m ai_generation.cli --help` for the CLI, or use the 216 MCP tools
exposed via `ai_generation.mcp_tools.MCPGenerationTools`.

## Project Structure

```
ai_generation/          # Single canonical platform package
  sdk.py                # Unified SDK entry point
  cli.py                # CLI interface
  mcp_tools.py          # 216 MCP tools exposed by the platform
  generation_manager.py # Orchestration core
  auto_router.py        # Intelligent provider routing
  execution_engine.py   # Task execution
  workflow_engine.py    # Multi-step workflows
  negotiation_engine.py # Capability negotiation
  capability_registry.py# Capability graph
  benchmark_engine.py   # Provider benchmarking
  quality_engine.py     # Output quality evaluation
  quality_engineering.py# Quality gates, review, test generation
  security.py           # Security framework
  observability.py      # Metrics & OpenTelemetry
  research_integration.py # Research <-> implementation traceability
  providers/            # Provider implementations
  agents/               # Autonomous agent system
  tests/                # 1,446 tests
configs/                # Canonical configuration (env template, MCP server registry)
data/                   # Runtime registries and benchmarks
knowledge-vault/        # Obsidian knowledge system (37 sections)
scripts/                # Setup & utility scripts
.github/workflows/      # CI/CD
```

## Providers

| Provider | Status | Image | Video | Audio |
|----------|--------|-------|-------|-------|
| HuggingFace | ✅ Active | ✅ | ✅ | ✅ |
| Replicate | ✅ Active | ✅ | ✅ | ✅ |
| Together AI | ✅ Active | ✅ | ❌ | ❌ |
| Fal.ai | ✅ Active | ✅ | ✅ | ❌ |
| Pollinations | ✅ Active | ✅ | ❌ | ❌ |
| Stability AI | ✅ Active | ✅ | ❌ | ❌ |
| SiliconFlow | ✅ Active | ✅ | ❌ | ❌ |
| Craiyon | ✅ Active | ✅ | ❌ | ❌ |

## Provider Network & Discovery Registrar

The platform maintains a persisted provider network snapshot at
`data/registry/provider_discovery.json`, regenerated from the live provider
registry and benchmark scores. It ranks every provider per modality using a
deterministic free-first, benchmark-aware score, and the Generation Manager
uses that ranked order for automatic routing (falling back to tier ordering
when no snapshot exists).

```bash
# Refresh the provider network and print the ranked list
python -m ai_generation.cli provider-rank [TYPE]

# Via the unified SDK
python -c "from ai_generation import UncleFrappeAI; ai = UncleFrappeAI(); print(ai.get_provider_ranking('image'))"
```

Ranking factors: tier (free first), key availability (keyless first),
availability/status, success rate, latency, and benchmark composite score.
Key-gated providers are marked `needs key` and remain listed but rank below
usable providers. The registrar is also exposed as the `get_provider_ranking`
MCP tool.

### Provider Health Cycle

`ProviderHealthCycle` checks every cloud provider, auto-disables providers
after 3 consecutive failures (they are excluded from routing), auto-re-enables
them when a check succeeds, and persists the result to
`data/registry/health_registry.json`.

```bash
python -m ai_generation.cli health-cycle
```

Also exposed via the SDK (`run_provider_health_cycle`) and the
`run_provider_health_cycle` MCP tool. Local-only runtimes (Piper, Kokoro,
OpenAI TTS) are skipped by design — they are expected to be started on demand.

## Verified Generation Matrix

`scripts/verify_generation.py` proves every modality by execution on the
current machine (stdlib + httpx only, no API keys required). Keyless paths
must produce real media; credential/local-gated paths must return clean,
truthful errors with exact reasons — never crashes.

```bash
python scripts/verify_generation.py
```

| Modality | Keyless on fresh install | Notes |
|----------|--------------------------|-------|
| Image | ✅ works | Pollinations (free, no key); Craiyon fallback |
| Text (chat) | ✅ works | Pollinations anonymous API (free, no key); Kimi K3 / self-hosted vLLM/SGLang as key/local backends |
| OCR | ✅ works (if Tesseract installed) | `tesseract-ocr` via `ocr_engine`; exact extraction verified |
| Embeddings | ✅ works (if `sentence-transformers` installed) | all-MiniLM-L6-v2, 384-dim, cos_sim 0.858 verified |
| Speech (TTS) | ✅ works (if `piper` + voice installed) | `piper_local` en_US-lessac-medium, 2.76s WAV verified |
| Speech (STT) | ✅ works (if `faster-whisper` installed) | tiny int8 CPU, TTS→STT round-trip verified |
| Translation | ✅ works (if `transformers` installed) | Helsinki-NLP opus-mt, en→fr verified |
| Upscaling | ✅ works (if `spandrel` + weights installed) | Real-ESRGAN x4v3, 200×60→800×240 verified |
| Background removal | ✅ works (if `rembg` installed) | u2net, RGBA 88.5% transparent verified |
| Video | ⛔ needs key | Replicate/Runway/fal providers require API tokens |
| Music / SFX | ⛔ needs local server | AudioCraft HTTP server (`MUSICGEN_URL`) |
| 3D | ⛔ needs GPU | TRELLIS/Hunyuan3D/Point-E/Shap-E require 8–16 GB VRAM |
| Reasoning / Tool calls | via chat backends | same credential requirements as Text |
| Storage (metadata/ledger/audit) | ✅ works | Local SQLite + JSON backends (stdlib, offline); PostgreSQL/Qdrant/MinIO/Neo4j/Prometheus/Redis registered as truthful `not_configured` profiles |
| Event sourcing | ✅ works | Durable event log (SQLite): ACOS taxonomy, per-class delivery guarantees, replay, dead-letter queue, retention |
| Capability graph | ✅ works | Auto-sync from provider/storage/event-log registries; 52 nodes / 48 edges; pathfinding for chat, embeddings, translation, upscaling, bg-removal, storage, events |
| Compatibility matrix | ✅ works | Model × Runtime × Hardware lookup: 161 entries / 44 models / 40 runtimes; path validation (CGR-07), benchmark feedback, 90-day refresh tracking |
| Research traceability | ✅ works | Every VERIFIED capability linked to implementation modules; BLOCKED capabilities truthfully unlinked; auto-linking + curated aliases |

The local backends are exposed through the unified SDK, CLI, and MCP:

```bash
python -m ai_generation.cli local-backends
python -m ai_generation.cli embed "text to embed"
python -m ai_generation.cli translate "Hello" --target fr
python -m ai_generation.cli tts "Hello from the platform" --output speech.wav
python -m ai_generation.cli stt speech.wav
python -m ai_generation.cli ocr document.png
python -m ai_generation.cli upscale photo.png --output upscaled.png
python -m ai_generation.cli bg-remove photo.png --output cutout.png
```

Storage (ACOS Storage Architecture — SQLite/JSON local, external profiles):

```bash
python -m ai_generation.cli storage-list
python -m ai_generation.cli storage-write ledger dec-1 '{"action": "route"}' --task ledger
python -m ai_generation.cli storage-read ledger dec-1
python -m ai_generation.cli storage-query ledger --limit 20
python -m ai_generation.cli storage-stats
```

Durable event log (ACOS Messaging & Events Research):

```bash
python -m ai_generation.cli event-classes
python -m ai_generation.cli event-emit request.completed '{"task_id": "t1"}'
python -m ai_generation.cli event-replay request.*
python -m ai_generation.cli event-stats
python -m ai_generation.cli event-purge dead_letter
```

Capability graph (ACOS Capability Graph — graph evolves automatically from
live registries via the unified SDK/CLI/MCP `sync_capability_graph` surface):

```bash
python -m ai_generation.cli cap-graph-sync
python -m ai_generation.cli capabilities
python -m ai_generation.cli research-graph
```

Compatibility matrix (ACOS Compatibility Matrix — Model × Runtime × Hardware
routing lookup, exposed via SDK/CLI/MCP `compat_*` / `compatibility_*` surfaces):

```bash
python -m ai_generation.cli compat
python -m ai_generation.cli compat-lookup llama3_8b vllm nvidia
python -m ai_generation.cli compat-runtimes sdxl
python -m ai_generation.cli compat-models video
python -m ai_generation.cli compat-validate cogvideox_5b comfyui_video nvidia
```

Every failure is returned as a structured result with the exact technical
reason (e.g. `AudioCraft server not reachable at http://localhost:9876`), and
the harness writes `output/verification/verify_generation.json` plus any
produced artifacts.

The harness currently passes all 19 modality checks: real media is produced
for Image, Text, Speech (Piper local), Embeddings, Translation, OCR, STT
(piper -> faster-whisper round-trip), Upscaling (Real-ESRGAN 4x), Background
removal, Storage, Event sourcing, Capability graph and Compatibility matrix;
credential/local-gated modalities (Video, Music, SFX, 3D) return truthful,
structured reasons instead of crashes.

## Development

```bash
# Setup
./scripts/setup.sh

# Optional keyless local backends (embeddings, Piper TTS, faster-whisper STT,
# Helsinki translation, Real-ESRGAN upscaling, rembg background removal,
# OCR helpers, document parsing). Core platform works without these; install
# them to unlock self-hosted CPU generation:
bash scripts/install-optional.sh                 # all groups
bash scripts/install-optional.sh --group embeddings   # single group
bash scripts/install-optional.sh --dry-run            # preview only

# Run tests
python -m pytest ai_generation/tests/ -v

# Run CLI
python -m ai_generation.cli --help

# Build and run the container
docker build -t uncle-frappe-ai-generation-platform .
docker run --rm uncle-frappe-ai-generation-platform
```

CI runs the full `ai_generation/tests/` suite (1,446 tests), verifies every
module imports cleanly, smoke-tests the unified SDK, and builds the Docker
image on every push to `main` (`.github/workflows/ci.yml`).

## Knowledge Base

`knowledge-vault/` is an Obsidian vault generated from the codebase — 37
sections covering architecture, ADRs, capabilities, providers, runtimes,
benchmarks, and quality engineering. 9 accepted ADRs (`01-Architecture/
Decision-Records`) record the architecture decisions behind milestones #33-#40.
Regenerate with:

```bash
python3 knowledge-vault/37-Pipeline/generate_vault.py
```

## License

MIT
