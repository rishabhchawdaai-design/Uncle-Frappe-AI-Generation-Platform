---
type: overview
module: skills
status: active
tags: [skills, overview]
---

# Skills Overview

## Skill Categories

### Quality Skills
- Quality Gate Runner
- Code Review Specialist
- Test Generator
- Coverage Analyzer
- Refactoring Advisor

### Generation Skills
- Image Prompt Enhancer
- Video Script Writer
- Audio Prompt Optimizer
- 3D Scene Designer

### Analysis Skills
- Secret Scanner
- Static Analyzer
- Structural Analyzer
- Dependency Auditor

### Operations Skills
- Provider Health Monitor
- Benchmark Runner
- Regression Detector
- Failure Recovery

## Skill Architecture

```mermaid
graph TB
    subgraph "Skill System"
        Registry["Skill Registry"]
        Loader["Skill Loader"]
        Executor["Skill Executor"]
    end
    
    subgraph "Skill Types"
        Quality["Quality Skills"]
        Generation["Generation Skills"]
        Analysis["Analysis Skills"]
        Operations["Operations Skills"]
    end
    
    Registry --> Loader
    Loader --> Executor
    Quality --> Loader
    Generation --> Loader
    Analysis --> Loader
    Operations --> Loader
```

## Related

- [[Architecture Overview]]
- [[Plugin System Overview]]
- [[Quality Engineering Overview]]
