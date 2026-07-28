---
type: overview
module: quality-engineering
status: active
tags: [quality, overview, index]
---

# Quality Engineering Overview

## Quality Engines

| Engine | Module | Purpose |
|--------|--------|---------|
| QualityGateEngine | `quality_engineering.py` | Swiss Cheese Model gates |
| CodeReviewEngine | `quality_engineering.py` | Dual-agent code review |
| QualityScoringEngine | `quality_engineering.py` | 7-dimension scoring |
| TestGenerationEngine | `quality_engineering.py` | Test case generation |
| CoverageGapEngine | `quality_engineering.py` | Risk-weighted gap analysis |
| FlakyDetectionEngine | `quality_engineering.py` | Pattern-based detection |
| PatternLearningEngine | `quality_engineering.py` | Codebase pattern memory |
| SecretScanner | `code_analysis.py` | Secret detection |
| StaticAnalyzer | `code_analysis.py` | Security & quality analysis |
| StructuralAnalyzer | `code_analysis.py` | Dead code, duplication, complexity |
| MultiAgentReviewEngine | `code_analysis.py` | Parallel agent review |
| PRVerificationEngine | `code_analysis.py` | PR checklist |
| TechnicalDebtTracker | `code_analysis.py` | Debt cataloging |
| RefactoringEngine | `refactoring_engine.py` | Smell detection & suggestions |
| SmellDetector | `refactoring_engine.py` | AST-based smell detection |
| OrchestrationPipeline | `orchestration.py` | Multi-agent pipeline |
| QualityDashboard | `quality_dashboard.py` | Unified quality report |

## Quality Score Dashboard

```dataview
TABLE WITHOUT ID
  length(filter(rows, (r) => r.findings_count > 0)) AS "With Findings",
  length(rows) AS "Dimensions"
FROM "36-Generated/Dashboards"
WHERE type = "quality-engineering"
GROUP BY true
```

## Related

- [[Architecture Overview]]
- [[Testing Overview]]
- [[Benchmarks Overview]]
