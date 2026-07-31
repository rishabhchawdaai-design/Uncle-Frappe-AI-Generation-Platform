---
type: overview
status: active
tags: [research, overview, index]
---

# Research Overview

## Research Sources

| Repository | Purpose | Status |
|------------|---------|--------|
| rishabhchawda/Uncle-Frappé | Research, experiments, documentation | Active |
| rishabhchawdaai-design/Uncle-Frappe-AI-Generation-Platform | Production implementation | Active |
| ACOS Research Canon | Architectural specifications | Complete |

## Quality Engineering Research

All 19 candidate repositories cloned locally (2026-07-31) and evaluated for
reusable concepts. Verdicts: INTEGRATED (concept already implemented in this
platform), CATALOGUED (registered for reference, e.g. Skill Registry),
REFERENCE (pattern recorded; license unclear so code is not bundled),
ADAPTED (pattern informed existing design), BLOCKED (proprietary/commercial).

| Repository | License | Key Concept | Platform Integration | Status |
|------------|---------|-------------|----------------------|--------|
| proffesor-for-testing/agentic-qe | MIT | Test generation, coverage, flaky detection | `quality_engineering.py` (generate_tests, analyze_coverage_gaps, detect_flaky_tests) | INTEGRATED |
| timwuhaotian/the-pair | Apache-2.0 | Mentor/Executor pair, cross-verification | `supervisor.py`, `agents/` | INTEGRATED |
| sburl/CrossCheck | MIT | Consensus verification, layered quality gates | `quality_engineering.py` quality gates | INTEGRATED |
| Anirodh-Padhy/ai-code-reviewer | MIT | Secret scanning, multi-agent review | `security.py`, `quality_engineering.py` | INTEGRATED |
| radetsky/llm-code-review | none | LLM code review over OpenAI-compatible APIs | reference only — license unclear | REFERENCE |
| ludo-technologies/polyscan | MIT | Structural analysis, dead code, complexity | `code_analysis.py` | INTEGRATED |
| d-o-hub/github-template-ai-agents | MIT | PR verification checklists | `quality_engineering.py` (verify_pr) | INTEGRATED |
| andrealaforgia/claude-code-agents | none | Specialized dev agents, refactoring advisor | reference only — license unclear | REFERENCE |
| krishagarwal314/autodev-studio | MIT | Autonomous SDLC harness, orchestration + KB context | `orchestration.py`, `knowledge_graph.py` | INTEGRATED |
| jordansrowles/custom-ai-agents | none | Domain-specific Copilot review prompts | reference only — license unclear | REFERENCE |
| middleleap/ai-dlc | Apache-2.0 | Loom methodology, BrainKit skill packs | planning/execution patterns | ADAPTED |
| kambleakash0/agent-skills | MIT | Claude skills + MCP servers collection | Skill Registry (external source) | CATALOGUED |
| kairyou/agent-tools | MIT | Reusable agent skills + installable integrations | Skill Registry (external source) | CATALOGUED |
| shadcn/improve | MIT | Codebase audit → implementation plans | codebase audit patterns | REFERENCE |
| MarioDevTM/AI-CODE-REVIEW-ASSISTANT | none | Dual-mode local review assistant | reference only — license unclear | REFERENCE |
| rabu20367/AI-Coding-Agent | none | Agentic-RAG code review | reference only — license unclear | REFERENCE |
| JepStar990/asea-x | MIT | Multi-agent SDLC agent system | `supervisor.py`, `agents/` | ADAPTED |
| moatpsychologistkiln/qodo | none | Commercial AI test generation platform | Tool/agent ecosystem — proprietary | BLOCKED |
| sourcery-ai/sourcery-vscode | MIT code / proprietary service | AI refactoring assistant (commercial) | Tool Registry (blocked entry) | BLOCKED |

## ACOS Research Topics

- Browser AI Inference Layer
- Edge AI Runtime Detection
- Image Generation Research
- Audio & Speech Research
- OCR & Document Intelligence
- Workflow Orchestration
- Distributed AI
- Agent Frameworks
- Plugin Ecosystem
- Storage & Databases
- Messaging & Events
- Search Systems
- Observability
- Networking & Mesh

## Related

- [[Architecture Overview]]
- [[Quality Engineering Overview]]
- [[Roadmap Overview]]
