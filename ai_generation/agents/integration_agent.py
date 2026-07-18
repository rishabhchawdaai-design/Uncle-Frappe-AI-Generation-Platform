"""
Integration Agent — automatically reads documentation, parses schemas,
generates adapters, validates them, and registers providers.
Uses the Dynamic Adapter System for schema-driven integration.
"""
import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from .base_agent import BaseAgent, AgentTask, AgentResult


class IntegrationAgent(BaseAgent):
    agent_name = "integration"
    agent_description = "Automatically integrates providers using schema-driven adapter compilation"

    def __init__(self, config=None):
        super().__init__(config)
        self.data_dir = config.get("data_dir", "data/registry") if config else "data/registry"
        os.makedirs(self.data_dir, exist_ok=True)
        self._integrations: List[Dict[str, Any]] = []
        self._adapter_cache: Dict[str, Dict[str, Any]] = {}
        self._load()

    def _load(self):
        path = os.path.join(self.data_dir, "integrations.json")
        if os.path.exists(path):
            try:
                with open(path) as f:
                    data = json.load(f)
                self._integrations = data.get("integrations", [])
                self._adapter_cache = data.get("adapter_cache", {})
            except Exception:
                pass

    def _save(self):
        path = os.path.join(self.data_dir, "integrations.json")
        with open(path, "w") as f:
            json.dump({
                "integrations": self._integrations,
                "adapter_cache": self._adapter_cache,
                "updated_at": datetime.utcnow().isoformat(),
            }, f, indent=2)

    def _execute_task(self, task: AgentTask) -> AgentResult:
        task_type = task.task_type
        if task_type == "integrate_provider":
            return self._integrate_provider(task)
        elif task_type == "generate_adapter":
            return self._generate_adapter(task)
        elif task_type == "validate_adapter":
            return self._validate_adapter(task)
        elif task_type == "list_integrations":
            return AgentResult(data={"integrations": self._integrations, "total": len(self._integrations)})
        elif task_type == "remove_integration":
            return self._remove_integration(task)
        return AgentResult(data={"status": "unknown_task"})

    def _integrate_provider(self, task: AgentTask) -> AgentResult:
        provider = task.payload.get("provider", "")
        schema_type = task.payload.get("schema_type", "custom")
        schema_data = task.payload.get("schema_data", {})

        integration = {
            "provider": provider, "schema_type": schema_type,
            "status": "integrating", "started_at": datetime.utcnow().isoformat(),
        }

        adapter = self._compile_adapter(provider, schema_type, schema_data)
        if adapter:
            integration["status"] = "integrated"
            integration["adapter"] = adapter
            integration["completed_at"] = datetime.utcnow().isoformat()
            self._adapter_cache[provider] = adapter
        else:
            integration["status"] = "failed"
            integration["error"] = "Schema compilation failed"

        self._integrations.append(integration)
        self._save()
        return AgentResult(data=integration)

    def _compile_adapter(self, provider: str, schema_type: str, schema_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        endpoints = []
        auth = {"type": "api_key"}

        if schema_type == "openapi":
            paths = schema_data.get("paths", {})
            for path, methods in paths.items():
                for method in methods:
                    if method.lower() in ("get", "post", "put", "delete"):
                        endpoints.append({
                            "path": path, "method": method.upper(),
                            "operation": methods[method].get("operationId", ""),
                        })
        elif schema_type == "json_schema":
            for key, val in schema_data.get("properties", {}).items():
                endpoints.append({"name": key, "type": val.get("type", "string")})
        elif schema_type == "mcp_tools":
            for name, tool in schema_data.items():
                endpoints.append({"name": name, "input_schema": tool.get("inputSchema", {})})
        else:
            for key, val in schema_data.items():
                if isinstance(val, dict):
                    endpoints.append({"name": key, "details": val})

        if not endpoints:
            return None

        return {
            "provider": provider, "schema_type": schema_type,
            "endpoints": endpoints, "auth": auth,
            "compiled_at": datetime.utcnow().isoformat(),
            "version": 1,
        }

    def _generate_adapter(self, task: AgentTask) -> AgentResult:
        provider = task.payload.get("provider", "")
        cached = self._adapter_cache.get(provider)
        if cached:
            return AgentResult(data={"adapter": cached, "source": "cache"})
        return AgentResult(success=False, error=f"No adapter for {provider}")

    def _validate_adapter(self, task: AgentTask) -> AgentResult:
        provider = task.payload.get("provider", "")
        adapter = self._adapter_cache.get(provider)
        if not adapter:
            return AgentResult(success=False, error=f"No adapter for {provider}")
        has_endpoints = len(adapter.get("endpoints", [])) > 0
        has_auth = bool(adapter.get("auth"))
        return AgentResult(data={
            "provider": provider, "valid": has_endpoints and has_auth,
            "endpoints_count": len(adapter.get("endpoints", [])),
            "has_auth": has_auth,
        })

    def _remove_integration(self, task: AgentTask) -> AgentResult:
        provider = task.payload.get("provider", "")
        before = len(self._integrations)
        self._integrations = [i for i in self._integrations if i.get("provider") != provider]
        self._adapter_cache.pop(provider, None)
        self._save()
        return AgentResult(data={"removed": before - len(self._integrations), "provider": provider})

    def get_stats(self) -> Dict[str, Any]:
        base = super().get_stats()
        integrated = len([i for i in self._integrations if i.get("status") == "integrated"])
        base.update({
            "total_integrations": len(self._integrations),
            "successful": integrated,
            "failed": len(self._integrations) - integrated,
            "cached_adapters": len(self._adapter_cache),
        })
        return base
