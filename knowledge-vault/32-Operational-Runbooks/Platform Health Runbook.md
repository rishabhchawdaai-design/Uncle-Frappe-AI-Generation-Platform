---
type: runbook
status: active
tags: [runbook, operational, health]
---

# Platform Health Runbook

## Quick Health Check

```bash
# Run all tests
python3 -m pytest ai_generation/tests/ --tb=short -q

# Run quality dashboard
python3 -c "
from ai_generation.quality_dashboard import QualityDashboard
import os
d = QualityDashboard()
for f in sorted(os.listdir('ai_generation')):
    if f.endswith('.py') and not f.startswith('test_'):
        with open(f'ai_generation/{f}') as fh:
            r = d.analyze(fh.read(), f)
            if r.overall_score < 70:
                print(f'{f}: {r.overall_grade}')
"
```

## Test Suite

| Metric | Value |
|--------|-------|
| Total Tests | 1,128 |
| Passing | 1,128 |
| Failing | 0 |
| Skipped | 1 |
| Warnings | 339 |

## Module Count

| Category | Count |
|----------|-------|
| Total Modules | 65 |
| Test Files | 35 |
| MCP Tools | 198 |
| Capabilities | 204 VERIFIED |

## Common Issues

### Import Errors
- Cause: Circular imports
- Fix: Use lazy loading in SDK properties

### Test Failures
- Cause: Missing dependencies
- Fix: Check test fixtures and conftest.py

### Quality Score Drops
- Cause: New code with security patterns
- Fix: Review and update quality gates

## Related

- [[Quality Engineering Overview]]
- [[Testing Overview]]
- [[Architecture Overview]]
