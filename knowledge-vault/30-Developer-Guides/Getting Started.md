---
type: guide
status: active
tags: [developer, guide, getting-started]
---

# Getting Started

## Quick Start

```python
from ai_generation import UncleFrappeAI

# Initialize the SDK
ai = UncleFrappeAI()

# Generate an image
result = await ai.generate(
    prompt="a beautiful sunset over mountains",
    style="photorealistic",
    width=1024,
    height=1024
)

# Run quality analysis
report = ai.quality_dashboard.analyze(code, "my_module.py")
print(f"Quality: {report.overall_grade} ({report.overall_score}/100)")

# Run code review
review = ai.multi_agent_review.simulate_review(code, "my_module.py")
print(f"Findings: {review.total_findings}")

# Get refactoring suggestions
suggestions = ai.refactoring_engine.analyze(code, "my_module.py")
for s in suggestions:
    print(f"{s.technique}: {s.description}")
```

## Architecture Overview

The platform follows a layered architecture:

1. **Entry Layer** — CLI, SDK, MCP Tools
2. **Intelligence Layer** — Auto Router, Agent Planner, Negotiation Engine
3. **Quality Layer** — Quality Gates, Code Review, Dashboard
4. **Execution Layer** — Execution Engine, Workflows, Benchmarks
5. **Provider Layer** — Provider Discovery, Local Runtimes, Remote Endpoints

## Key Concepts

### Capabilities
Every feature is a "capability" with a unique ID (e.g., `IMG-01`, `VID-05`, `QE-09`).
Capabilities are tracked in the Capability Registry.

### Quality Gates
The Swiss Cheese Model applies 8 quality gates:
1. Secret scanning
2. Debug code detection
3. Import validation
4. Security analysis
5. Type hints
6. File size limits
7. Conventional commits
8. Test pass verification

### Multi-Agent Review
Code is reviewed by 6 specialized agents:
- Security, Performance, Patterns, Style, Testing, Architecture

### Orchestration Pipeline
Tasks flow through: Intent → Planning → QA → Review → Security → Delivery

## Development Workflow

1. Study the canonical specification
2. Check existing implementations
3. Identify reusable modules
4. Implement the capability
5. Integrate with SDK
6. Add to Capability Registry
7. Write tests
8. Run quality gates
9. Update documentation
10. Commit and push

## Related

- [[Architecture Overview]]
- [[API Reference]]
- [[Quality Engineering Overview]]
