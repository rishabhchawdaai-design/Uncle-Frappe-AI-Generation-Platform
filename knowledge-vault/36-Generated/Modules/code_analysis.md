---
module: "code_analysis"
type: module-doc
status: active
owner: ""
lines: 916
classes: 19
functions: 0
tags: [module, documentation]
generated: "2026-07-28"
---

# code_analysis

> Code Analysis Engines — extracted from ai-code-reviewer, llm-code-review, polyscan, claude-code-agents.

Provides: SecretScanner, StaticAnalyzer, StructuralAnalyzer,
MultiAgentReviewEngine, PRVerifica

## Overview

- **File**: `ai_generation/code_analysis.py`
- **Lines**: 916
- **Classes**: 19
- **Public Functions**: 0

## Classes

- `{{SecretSeverity}}`
- `{{SecretFinding}}`
- `{{SecretScanner}}`
- `{{IssueSeverity}}`
- `{{StaticIssue}}`
- `{{StaticAnalyzer}}`
- `{{StructuralFinding}}`
- `{{StructuralAnalyzer}}`
- `{{ReviewAgentRole}}`
- `{{AgentReviewResult}}`
- `{{AggregatedReview}}`
- `{{MultiAgentReviewEngine}}`
- `{{CheckStatus}}`
- `{{CheckResult}}`
- `{{PRVerificationEngine}}`
- `{{DebtCategory}}`
- `{{DebtPriority}}`
- `{{DebtItem}}`
- `{{TechnicalDebtTracker}}`

## Integration

- Part of the [[Architecture Overview|Unified AI Generation Platform]]
- Exposed via [[05-SDK/SDK Overview|SDK]] and [[06-MCP-Ecosystem/MCP Ecosystem Overview|MCP Tools]]
- Verified in [[02-Capability-Registry/Capability Registry Overview|Capability Registry]]

## Related

- [[Architecture Overview]]
- [[Capability Registry Overview]]
