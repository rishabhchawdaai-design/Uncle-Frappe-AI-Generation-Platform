"""Shared base classes for all Research MCP Stack sections."""
import asyncio, time, json, hashlib
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from pathlib import Path
from enum import Enum

class ToolCategory(str, Enum):
    SEARCH = "search_mcp"
    RAIPUR_DATA = "raipur_data"
    SOCIAL = "social_data"
    AI_RESEARCH = "ai_research"
    OCR = "ocr_docs"
    KNOWLEDGE_GRAPH = "knowledge_graph"
    VALIDATION = "data_validation"
    RAIPUR_TARGETS = "raipur_targets"

@dataclass
class ToolResult:
    source: str
    category: str = ""
    data: Any = None
    raw: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    status: str = "success"
    error: Optional[str] = None
    tool: str = ""
    duration_ms: float = 0
    result_hash: str = ""

    def __post_init__(self):
        if self.raw and not self.result_hash:
            self.result_hash = hashlib.sha256(str(self.raw).encode()).hexdigest()[:16]
        if self.data is None:
            self.data = {}

    def to_dict(self) -> Dict:
        return {
            "source": self.source, "category": self.category, "tool": self.tool,
            "status": self.status, "duration_ms": self.duration_ms,
            "result_hash": self.result_hash, "metadata": self.metadata,
        }

class BaseTool(ABC):
    name: str = "base"
    category: ToolCategory = ToolCategory.SEARCH
    requires_api_key: bool = False
    requires_docker: bool = False
    mcp_server: Optional[str] = None
    capabilities: List[str] = []

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config if config is not None else {}

    @abstractmethod
    async def search(self, query: str, **kwargs) -> ToolResult:
        pass

    async def health_check(self) -> Dict[str, Any]:
        return {"tool": self.name, "status": "available", "category": self.category.value,
                "capabilities": self.capabilities, "requires_api_key": self.requires_api_key}

    def _timing(self, start: float) -> float:
        return round((time.time() - start) * 1000, 2)

    def _get_api_key(self, env_var: str) -> str:
        import os
        return self.config.get("api_key") or os.environ.get(env_var, "")
