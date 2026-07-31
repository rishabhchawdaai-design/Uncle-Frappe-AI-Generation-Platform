---
module: "quality_engineering"
type: module-doc
status: active
owner: ""
lines: 864
classes: 18
functions: 0
tags: [module, documentation]
generated: "2026-07-31"
---

# quality_engineering

> Quality Engineering Layer — extracted patterns from agentic-qe, the-pair, CrossCheck.

Implements:
- Quality Gates (Swiss Cheese Model from CrossCheck)
- Code Review Engine (dual-agent pattern from th

## Overview

- **File**: `ai_generation/quality_engineering.py`
- **Lines**: 864
- **Classes**: 18
- **Public Functions**: 0

## Classes

- `{{GateSeverity}}`
- `{{GateResult}}`
- `{{QualityGate}}`
- `{{GateCheckResult}}`
- `{{QualityGateEngine}}`
- `{{ReviewSeverity}}`
- `{{ReviewCategory}}`
- `{{ReviewFinding}}`
- `{{ReviewResult}}`
- `{{CodeReviewEngine}}`
- `{{QualityDimension}}`
- `{{QualityScore}}`
- `{{QualityScoringEngine}}`
- `{{TestTemplate}}`
- `{{TestGenerationEngine}}`
- `{{CoverageGapEngine}}`
- `{{FlakyDetectionEngine}}`
- `{{PatternLearningEngine}}`

## Integration

- Part of the [[Architecture Overview|Unified AI Generation Platform]]
- Exposed via [[05-SDK/SDK Overview|SDK]] and [[06-MCP-Ecosystem/MCP Ecosystem Overview|MCP Tools]]
- Verified in [[02-Capability-Registry/Capability Registry Overview|Capability Registry]]

## Related

- [[Architecture Overview]]
- [[Capability Registry Overview]]
