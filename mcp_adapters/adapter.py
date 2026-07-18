"""
MCP Adapter Layer - Wraps MCP servers into Python-callable interfaces.
Bridges the gap between MCP servers and the UnifiedCollector.
"""
import asyncio
import json
import os
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

REGISTRY_PATH = Path(__file__).parent / "registry.json"


@dataclass
class MCPServerConfig:
    name: str
    command: str
    args: List[str]
    env: Dict[str, str]
    tools: List[str]
    description: str


class MCPAdapter:
    """Manages MCP server connections and tool execution."""

    def __init__(self, registry_path: Optional[str] = None):
        self.registry = self._load_registry(registry_path or str(REGISTRY_PATH))
        self._processes: Dict[str, subprocess.Popen] = {}

    def _load_registry(self, path: str) -> Dict[str, MCPServerConfig]:
        with open(path) as f:
            data = json.load(f)
        servers = {}
        for key, cfg in data.get("mcp_servers", {}).items():
            env = {}
            for k, v in cfg.get("env", {}).items():
                if v.startswith("${") and v.endswith("}"):
                    env_var = v[2:-1]
                    env[k] = os.environ.get(env_var, "")
                else:
                    env[k] = v
            servers[key] = MCPServerConfig(
                name=cfg["name"], command=cfg["command"],
                args=cfg.get("args", []), env=env,
                tools=cfg.get("tools", []), description=cfg.get("description", ""),
            )
        return servers

    def list_servers(self) -> List[Dict[str, Any]]:
        return [
            {"id": k, "name": v.name, "tools": v.tools, "description": v.description}
            for k, v in self.registry.items()
        ]

    def list_tools(self, server_id: str) -> List[str]:
        server = self.registry.get(server_id)
        return server.tools if server else []

    async def call_tool(self, server_id: str, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool on an MCP server via stdio JSON-RPC."""
        server = self.registry.get(server_id)
        if not server:
            return {"error": f"Unknown MCP server: {server_id}"}
        if tool_name not in server.tools:
            return {"error": f"Tool '{tool_name}' not available on {server_id}"}

        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {"name": tool_name, "arguments": arguments},
        }

        env = {**os.environ, **server.env}
        try:
            proc = await asyncio.create_subprocess_exec(
                server.command, *server.args,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
            )
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(input=json.dumps(request).encode()),
                timeout=60,
            )
            if stdout:
                return json.loads(stdout.decode())
            return {"error": stderr.decode() if stderr else "No output"}
        except asyncio.TimeoutError:
            return {"error": "MCP server timeout"}
        except Exception as e:
            return {"error": str(e)}

    async def health_check(self) -> Dict[str, Any]:
        results = {}
        for server_id, server in self.registry.items():
            try:
                init_req = {"jsonrpc": "2.0", "id": 0, "method": "initialize", "params": {"capabilities": {}}}
                proc = await asyncio.create_subprocess_exec(
                    server.command, *server.args,
                    stdin=asyncio.subprocess.PIPE,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    env={**os.environ, **server.env},
                )
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(input=json.dumps(init_req).encode()),
                    timeout=10,
                )
                results[server_id] = {"status": "available" if stdout else "error", "tools": server.tools}
            except (asyncio.TimeoutError, Exception) as e:
                results[server_id] = {"status": "unavailable", "error": str(e)[:100]}
        return results
