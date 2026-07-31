"""
Tool Registry — unified registry of external code-quality tools.

Single source of truth: ``configs/tools.json`` (canonical — no parallel
tool registry). Every ready entry records a distribution verified on the
PyPI/npm JSON API; blocked entries carry the reason. This module is a
read-only view so SDK, CLI, and MCP surfaces expose the same registry
without duplicating data.
"""
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

CONFIG_PATH = Path(__file__).resolve().parent.parent / "configs" / "tools.json"


class ToolRegistry:
    """Unified code-quality tool registry (read-only view)."""

    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = Path(config_path) if config_path else CONFIG_PATH
        self._tools: Dict[str, Dict[str, Any]] = {}
        self._load()

    def _load(self):
        if not self.config_path.exists():
            logger.warning("Tool registry config missing: %s", self.config_path)
            return
        try:
            with open(self.config_path) as f:
                data = json.load(f)
            tools = data.get("tools", data)
            self._tools = {k: dict(v) for k, v in tools.items()}
        except Exception as e:
            logger.warning("Failed to load tool registry config: %s", e)

    def list_tools(self, category: str = "", status: str = "",
                   search: str = "") -> List[Dict[str, Any]]:
        """List tools, optionally filtered by category, status, or text search."""
        results = []
        q = search.lower().strip()
        for tool in self._tools.values():
            if category and tool.get("category", "") != category:
                continue
            if status and tool.get("status", "ready") != status:
                continue
            if q:
                haystack = " ".join(str(tool.get(k, "")) for k in
                                    ("id", "name", "purpose", "package"))
                if q not in haystack.lower():
                    continue
            results.append(dict(tool))
        return sorted(results, key=lambda t: t.get("id", ""))

    def get_tool(self, tool_id: str) -> Optional[Dict[str, Any]]:
        tool = self._tools.get(tool_id)
        return dict(tool) if tool else None

    def categories(self) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for tool in self._tools.values():
            cat = tool.get("category", "other")
            counts[cat] = counts.get(cat, 0) + 1
        return dict(sorted(counts.items()))

    def stats(self) -> Dict[str, Any]:
        total = len(self._tools)
        ready = sum(1 for t in self._tools.values() if t.get("status") == "ready")
        blocked = total - ready
        return {
            "total_tools": total,
            "ready": ready,
            "blocked": blocked,
            "categories": self.categories(),
        }

    def ready_tools(self) -> List[Dict[str, Any]]:
        return self.list_tools(status="ready")


_registry: Optional[ToolRegistry] = None


def get_tool_registry() -> ToolRegistry:
    """Return the process-wide singleton tool registry."""
    global _registry
    if _registry is None:
        _registry = ToolRegistry()
    return _registry
