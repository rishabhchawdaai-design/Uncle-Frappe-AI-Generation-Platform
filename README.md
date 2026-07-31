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

    # Enhance a prompt with cinematic techniques
    enhanced = ai.enhance_prompt("A luxury café interior", style="cinematic")
    print(enhanced.enhanced)


asyncio.run(main())
```

Run `python -m ai_generation.cli --help` for the CLI, or use the 198 MCP tools
exposed via `ai_generation.mcp_tools.MCPGenerationTools`.

## Project Structure

```
ai_generation/          # Single canonical platform package
  sdk.py                # Unified SDK entry point
  cli.py                # CLI interface
  mcp_tools.py          # 198 MCP tools exposed by the platform
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
  providers/            # Provider implementations
  agents/               # Autonomous agent system
  tests/                # 1,141 tests
configs/                # Canonical configuration (env template, MCP servers)
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

## Development

```bash
# Setup
./scripts/setup.sh

# Run tests
python -m pytest ai_generation/tests/ -v

# Run CLI
python -m ai_generation.cli --help

# Build and run the container
docker build -t uncle-frappe-ai-generation-platform .
docker run --rm uncle-frappe-ai-generation-platform
```

CI runs the full `ai_generation/tests/` suite (1,141 tests), verifies every
module imports cleanly, smoke-tests the unified SDK, and builds the Docker
image on every push to `main` (`.github/workflows/ci.yml`).

## Knowledge Base

`knowledge-vault/` is an Obsidian vault generated from the codebase — 37
sections covering architecture, ADRs, capabilities, providers, runtimes,
benchmarks, and quality engineering. Regenerate with:

```bash
python3 knowledge-vault/37-Pipeline/generate_vault.py
```

## License

MIT
