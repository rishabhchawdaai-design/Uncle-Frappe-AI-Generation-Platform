---
type: guide
status: active
tags: [developer, guide, contributing]
---

# Contributing Guide

## Code Style

- Use type hints for all function signatures
- Use dataclasses for structured data
- Use enums for constants
- Use async/await for I/O operations
- Follow the existing naming conventions

## Module Structure

Every new module should follow this pattern:

```python
"""Module description."""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

class MyEnum(str, Enum):
    VALUE = "value"

@dataclass
class MyData:
    field: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {"field": self.field}

class MyEngine:
    """Engine description."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
    
    def do_something(self) -> MyData:
        return MyData(field="value")
```

## SDK Integration

1. Add lazy-loaded property to `UncleFrappeAI.__init__`
2. Add `@property` method
3. Add convenience methods if appropriate
4. Add MCP tool definitions
5. Add MCP tool handlers

## Testing

- Write tests for every public method
- Use pytest fixtures for common setup
- Test both success and error paths
- Aim for >90% coverage on new code

## Quality Gates

All code must pass:
- Secret scanning (no hardcoded secrets)
- Static analysis (no security issues)
- Structural analysis (no excessive complexity)
- Code review (multi-agent review)
- Test verification (all tests pass)

## Related

- [[Architecture Overview]]
- [[API Reference]]
- [[Testing Overview]]
