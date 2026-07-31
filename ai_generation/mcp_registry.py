"""
MCP Registry — unified registry of MCP servers for the platform.

Single source of truth: ``configs/mcp_servers.json`` (canonical, merged
with the platform's original MCP configuration — no parallel registry).
Every entry records a verified install target (npm registry / PyPI JSON
API audit) or an explicit blocked reason. This module is a read-only
view over that configuration so SDK, CLI, and MCP surfaces expose the
same registry without duplicating data.
"""
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

CONFIG_PATH = Path(__file__).resolve().parent.parent / "configs" / "mcp_servers.json"

CATEGORIES = [
    "filesystem", "version-control", "infrastructure", "browser", "web",
    "search", "docs", "reasoning", "memory", "database", "vector-db",
    "graph-db", "api", "communication", "productivity", "design",
    "knowledge", "ai-platform",
]


class MCPRegistry:
    """Unified MCP server registry (read-only view over the canonical config)."""

    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = Path(config_path) if config_path else CONFIG_PATH
        self._servers: Dict[str, Dict[str, Any]] = {}
        self._load()

    def _load(self):
        if not self.config_path.exists():
            logger.warning("MCP registry config missing: %s", self.config_path)
            return
        try:
            with open(self.config_path) as f:
                data = json.load(f)
            servers = data.get("mcp_servers", data)
            self._servers = {k: dict(v) for k, v in servers.items()}
        except Exception as e:
            logger.warning("Failed to load MCP registry config: %s", e)

    def list_servers(self, category: str = "", status: str = "",
                     search: str = "") -> List[Dict[str, Any]]:
        """List servers, optionally filtered by category, status, or text search."""
        results = []
        q = search.lower().strip()
        for server in self._servers.values():
            if category and server.get("category", "") != category:
                continue
            if status and server.get("status", "ready") != status:
                continue
            if q:
                haystack = " ".join(str(server.get(k, "")) for k in
                                    ("id", "name", "description", "note", "package"))
                if q not in haystack.lower():
                    continue
            results.append(dict(server))
        return sorted(results, key=lambda s: s.get("id", ""))

    def get_server(self, server_id: str) -> Optional[Dict[str, Any]]:
        server = self._servers.get(server_id)
        return dict(server) if server else None

    def categories(self) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for server in self._servers.values():
            cat = server.get("category", "other")
            counts[cat] = counts.get(cat, 0) + 1
        return dict(sorted(counts.items()))

    def stats(self) -> Dict[str, Any]:
        total = len(self._servers)
        ready = sum(1 for s in self._servers.values() if s.get("status") == "ready")
        blocked = total - ready
        return {
            "total_servers": total,
            "ready": ready,
            "blocked": blocked,
            "categories": self.categories(),
            "env_required": sorted({
                key for s in self._servers.values()
                for key in (s.get("env") or {})
            }),
        }

    def ready_servers(self) -> List[Dict[str, Any]]:
        return self.list_servers(status="ready")

    def get_runtime_config(self) -> Dict[str, Any]:
        """Return the merged runtime config (launch-ready entries only)."""
        out = {}
        for server_id, server in self._servers.items():
            if server.get("status") == "ready" and server.get("command"):
                out[server_id] = {
                    "name": server.get("name", server_id),
                    "command": server.get("command"),
                    "args": server.get("args", []),
                    "env": server.get("env", {}),
                    "tools": server.get("tools", []),
                }
        return out


_registry: Optional[MCPRegistry] = None


def get_mcp_registry() -> MCPRegistry:
    """Singleton accessor for the unified MCP registry."""
    global _registry
    if _registry is None:
        _registry = MCPRegistry()
    return _registry
