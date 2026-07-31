"""
Discovery Agent — automatically discovers REST APIs, OpenAPI schemas,
MCP servers, compatible execution endpoints, HuggingFace Spaces,
public inference endpoints, and community execution services.
"""
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .base_agent import BaseAgent, AgentTask, AgentResult


KNOWN_ENDPOINTS = [
    {"name": "pollinations", "url": "https://image.pollinations.ai/prompt", "type": "rest_api", "auth": "none", "tasks": ["text_to_image"]},
    {"name": "huggingface_inference", "url": "https://api-inference.huggingface.co", "type": "rest_api", "auth": "api_key", "tasks": ["text_to_image"]},
    {"name": "siliconflow", "url": "https://api.siliconflow.cn/v1", "type": "openai_compatible", "auth": "api_key", "tasks": ["text_to_image"]},
    {"name": "together", "url": "https://api.together.xyz/v1", "type": "openai_compatible", "auth": "api_key", "tasks": ["text_to_image"]},
    {"name": "stability", "url": "https://api.stability.ai/v2beta", "type": "rest_api", "auth": "api_key", "tasks": ["text_to_image", "img2img", "inpainting", "upscale"]},
    {"name": "replicate", "url": "https://api.replicate.com/v1", "type": "rest_api", "auth": "api_key", "tasks": ["text_to_image", "text_to_video", "image_to_video"]},
    {"name": "fal", "url": "https://fal.run", "type": "rest_api", "auth": "api_key", "tasks": ["text_to_image", "img2img"]},
    {"name": "craiyon", "url": "https://api.craiyon.com/v3", "type": "rest_api", "auth": "none", "tasks": ["text_to_image"]},
    {"name": "replicate_video", "url": "https://api.replicate.com/v1", "type": "rest_api", "auth": "api_key", "tasks": ["text_to_video"]},
    {"name": "deepseek", "url": "https://api.deepseek.com/v1", "type": "openai_compatible", "auth": "api_key", "tasks": ["text_to_speech"]},
    {"name": "groq", "url": "https://api.groq.com/openai/v1", "type": "openai_compatible", "auth": "api_key", "tasks": ["text_to_speech"]},
    {"name": "openrouter", "url": "https://openrouter.ai/api/v1", "type": "openai_compatible", "auth": "api_key", "tasks": ["text_to_image"]},
    {"name": "black_forest_labs", "url": "https://black-forest-labs-flux-1-schnell.hf.space", "type": "hf_space", "auth": "none", "tasks": ["text_to_image"]},
    {"name": "kimi_k3_cloud", "url": "https://api.moonshot.ai/v1", "type": "openai_compatible", "auth": "api_key", "tasks": ["chat"]},
    {"name": "kimi_k3_vllm", "url": "http://localhost:8000", "type": "openai_compatible", "auth": "none", "tasks": ["chat"]},
    {"name": "kimi_k3_sglang", "url": "http://localhost:30000", "type": "openai_compatible", "auth": "none", "tasks": ["chat"]},
]


class DiscoveryAgent(BaseAgent):
    agent_name = "discovery"
    agent_description = "Discovers and catalogs available execution endpoints and services"

    def __init__(self, config=None):
        super().__init__(config)
        self.data_dir = config.get("data_dir", "data/registry") if config else "data/registry"
        os.makedirs(self.data_dir, exist_ok=True)
        self._endpoints: List[Dict[str, Any]] = []
        self._discovery_history: List[Dict[str, Any]] = []
        self._load()

    def _load(self):
        path = os.path.join(self.data_dir, "provider_registry.json")
        if os.path.exists(path):
            try:
                with open(path) as f:
                    data = json.load(f)
                self._endpoints = data.get("endpoints", [])
                self._discovery_history = data.get("history", [])
            except Exception:
                pass
        if not self._endpoints:
            self._endpoints = list(KNOWN_ENDPOINTS)

    def _save(self):
        path = os.path.join(self.data_dir, "provider_registry.json")
        with open(path, "w") as f:
            json.dump({
                "endpoints": self._endpoints,
                "history": self._discovery_history[-200:],
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }, f, indent=2)

    def _execute_task(self, task: AgentTask) -> AgentResult:
        task_type = task.task_type
        if task_type == "discover_endpoints":
            return self._discover_endpoints(task)
        elif task_type == "get_endpoints":
            return AgentResult(data={"endpoints": self._endpoints, "total": len(self._endpoints)})
        elif task_type == "add_endpoint":
            return self._add_endpoint(task)
        elif task_type == "remove_endpoint":
            return self._remove_endpoint(task)
        elif task_type == "search_endpoints":
            return self._search_endpoints(task)
        return AgentResult(data={"status": "unknown_task"})

    def _discover_endpoints(self, task: AgentTask) -> AgentResult:
        endpoint_type = task.payload.get("type", "all")
        found = self._endpoints if endpoint_type == "all" else [
            e for e in self._endpoints if e.get("type") == endpoint_type
        ]
        self._discovery_history.append({
            "action": "discover", "type": endpoint_type, "found": len(found),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        self._save()
        return AgentResult(data={"endpoints": found, "total": len(found), "type": endpoint_type})

    def _add_endpoint(self, task: AgentTask) -> AgentResult:
        endpoint = {
            "name": task.payload.get("name", ""),
            "url": task.payload.get("url", ""),
            "type": task.payload.get("type", "rest_api"),
            "auth": task.payload.get("auth", "api_key"),
            "tasks": task.payload.get("tasks", []),
            "discovered_at": datetime.now(timezone.utc).isoformat(),
        }
        existing = next((e for e in self._endpoints if e["name"] == endpoint["name"]), None)
        if existing:
            existing.update(endpoint)
        else:
            self._endpoints.append(endpoint)
        self._save()
        return AgentResult(data={"endpoint": endpoint, "status": "registered"})

    def _remove_endpoint(self, task: AgentTask) -> AgentResult:
        name = task.payload.get("name", "")
        before = len(self._endpoints)
        self._endpoints = [e for e in self._endpoints if e["name"] != name]
        removed = before - len(self._endpoints)
        self._save()
        return AgentResult(data={"removed": removed, "name": name})

    def _search_endpoints(self, task: AgentTask) -> AgentResult:
        query = task.payload.get("query", "").lower()
        task_filter = task.payload.get("task", "")
        results = self._endpoints
        if query:
            results = [e for e in results if query in e.get("name", "").lower() or query in e.get("url", "").lower()]
        if task_filter:
            results = [e for e in results if task_filter in e.get("tasks", [])]
        return AgentResult(data={"results": results, "total": len(results)})

    def get_stats(self) -> Dict[str, Any]:
        base = super().get_stats()
        base.update({
            "total_endpoints": len(self._endpoints),
            "types": list(set(e.get("type", "") for e in self._endpoints)),
            "free_endpoints": len([e for e in self._endpoints if e.get("auth") == "none"]),
            "discovery_history": len(self._discovery_history),
        })
        return base
