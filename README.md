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
from ai_generation.sdk import UncleFrappeAI

ai = UncleFrappeAI()

# Generate an image
result = ai.generate_image(
    prompt="A cinematic coffee advertisement with warm lighting",
    model="stabilityai/stable-diffusion-xl-base-1.0"
)

# Generate with automatic provider selection
result = ai.generate_image(
    prompt="A luxury café interior",
    auto_select=True  # Picks best available provider
)
```

## Project Structure

```
ai_generation/          # Core AI generation engine
  providers/            # Provider implementations
  agents/               # Autonomous agent system (Phase 14)
  tests/                # Test suite
  sdk.py               # Python SDK
  cli.py               # CLI interface
  mcp_tools.py         # MCP server tools
  generation_manager.py # Orchestration core
  prompt_engine.py     # Prompt optimization
  workflow_engine.py   # Workflow orchestration
  benchmark_engine.py  # Provider benchmarking
  quality_engine.py    # Output quality evaluation

browser_agents/         # Browser-based agent wrappers
core_platform/          # Platform infrastructure
  api.py               # REST API
  rag/                 # RAG system
  vector_store/        # Vector storage
  observability/       # Metrics & monitoring
  deployment/          # Docker & deployment

sections/               # Research section tools
wrappers/               # Web scraping wrappers
mcp_adapters/           # MCP protocol adapters
docker/                 # Container configurations
configs/                # Configuration files
scripts/                # Setup & utility scripts
data/                   # Runtime data (registries, benchmarks)
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
```

## License

MIT
