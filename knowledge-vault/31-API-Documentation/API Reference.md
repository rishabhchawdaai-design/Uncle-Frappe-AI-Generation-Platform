---
type: api-doc
status: active
tags: [api, documentation, reference]
---

# API Reference

## UncleFrappeAI SDK

The main entry point for all AI generation capabilities.

### Initialization

```python
from ai_generation import UncleFrappeAI

ai = UncleFrappeAI(config={})
```

### Core Generation

| Method | Description |
|--------|-------------|
| `ai.generate(prompt, style, width, height)` | Generate image from text |
| `ai.edit_image(image, instruction)` | Edit existing image |
| `ai.generate_video(prompt, duration)` | Generate video from text |
| `ai.generate_audio(prompt)` | Generate audio from text |
| `ai.generate_music(prompt)` | Generate music from text |
| `ai.generate_speech(text, voice)` | Generate speech |
| `ai.clone_voice(audio, text)` | Clone voice and speak |
| `ai.enhance_audio(audio)` | Enhance audio quality |
| `ai.edit_video(video, operations)` | Edit video |
| `ai.generate_3d(prompt)` | Generate 3D content |

### Quality Engineering

| Property | Description |
|----------|-------------|
| `ai.quality_gates` | Swiss Cheese Model quality gates |
| `ai.code_review` | Dual-agent code review |
| `ai.quality_scoring` | 7-dimension quality scoring |
| `ai.test_generation` | Test case generation |
| `ai.coverage_gap` | Risk-weighted gap analysis |
| `ai.flaky_detection` | Flaky test detection |
| `ai.pattern_learning` | Codebase pattern memory |
| `ai.secret_scanner` | Secret detection |
| `ai.static_analyzer` | Security and quality analysis |
| `ai.structural_analyzer` | Dead code, duplication, complexity |
| `ai.multi_agent_review` | Parallel agent review |
| `ai.pr_verification` | PR verification checklist |
| `ai.debt_tracker` | Technical debt cataloging |
| `ai.refactoring_engine` | Code smell detection and suggestions |
| `ai.quality_dashboard` | Unified quality report |

### Orchestration

| Property | Description |
|----------|-------------|
| `ai.orchestration_pipeline` | Multi-agent orchestration pipeline |
| `ai.knowledge_base` | RAG-based context retrieval |

### Provider Management

| Property | Description |
|----------|-------------|
| `ai.provider_discovery` | Discover available providers |
| `ai.provider_intelligence` | Provider analytics |
| `ai.health_monitor` | Provider health monitoring |

### Execution

| Property | Description |
|----------|-------------|
| `ai.execution_engine` | Task execution |
| `ai.workflow_engine` | Multi-step workflows |
| `ai.benchmark_engine` | Benchmarking |
| `ai.auto_router` | Intelligent routing |

### Observability

| Property | Description |
|----------|-------------|
| `ai.observability` | Traces, metrics, logs |
| `ai.otel_exporter` | OpenTelemetry export |
| `ai.decision_ledger` | Decision audit trail |

### Security

| Property | Description |
|----------|-------------|
| `ai.security_manager` | RBAC, access control |
| `ai.encryption_at_rest` | Data encryption |
| `ai.encryption_in_transit` | TLS/SSL |

## MCP Tools

198 MCP tools available via the Unified MCP Interface.

### Quality Engineering Tools

| Tool | Description |
|------|-------------|
| `run_quality_gates` | Run quality gates on code |
| `run_single_gate` | Run a single quality gate |
| `review_code` | Automated code review |
| `score_quality` | Score code quality |
| `generate_tests` | Generate test cases |
| `analyze_coverage_gaps` | Analyze coverage gaps |
| `detect_flaky_tests` | Detect flaky tests |
| `learn_pattern` | Learn codebase pattern |
| `find_patterns` | Find learned patterns |
| `scan_secrets` | Scan for secrets |
| `analyze_code_static` | Static analysis |
| `analyze_code_structural` | Structural analysis |
| `run_multi_agent_review` | Multi-agent review |
| `verify_pr` | PR verification |
| `track_tech_debt` | Track technical debt |
| `detect_code_smells` | Detect code smells |
| `suggest_refactoring` | Suggest refactorings |
| `run_quality_dashboard` | Run quality dashboard |
| `get_quality_history` | Get quality history |
| `get_quality_stats` | Get quality statistics |

### Orchestration Tools

| Tool | Description |
|------|-------------|
| `run_orchestration_pipeline` | Run orchestration pipeline |
| `plan_agents` | Select agents for task |
| `add_kb_entry` | Add knowledge base entry |
| `retrieve_kb` | Retrieve KB entries |

### Generation Tools

| Tool | Description |
|------|-------------|
| `generate_image` | Generate image from text |
| `edit_image` | Edit existing image |
| `generate_video` | Generate video |
| `edit_video` | Edit video |
| `generate_audio` | Generate audio |
| `generate_music` | Generate music |
| `clone_voice` | Clone voice |
| `enhance_audio` | Enhance audio |
| `generate_3d` | Generate 3D content |

## Related

- [[Architecture Overview]]
- [[SDK Overview]]
- [[MCP Ecosystem Overview]]
- [[Quality Engineering Overview]]
