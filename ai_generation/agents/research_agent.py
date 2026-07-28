"""
Research Agent — continuously monitors GitHub, HuggingFace, docs, release notes,
engineering blogs, and model registries. Detects new providers, models, and capabilities.
Builds the Provider Knowledge Graph.
"""
import json
import os
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .base_agent import BaseAgent, AgentTask, AgentResult


KNOWN_RESEARCH_SOURCES = [
    {"source": "github", "url": "https://github.com", "type": "code", "focus": "new providers and models"},
    {"source": "huggingface", "url": "https://huggingface.co", "type": "models", "focus": "model releases and spaces"},
    {"source": "arxiv", "url": "https://arxiv.org", "type": "papers", "focus": "new research and architectures"},
    {"source": "provider_docs", "url": "", "type": "documentation", "focus": "API changes and new features"},
    {"source": "changelogs", "url": "", "type": "releases", "focus": "version updates and deprecations"},
    {"source": "mcp_ecosystem", "url": "", "type": "tools", "focus": "new MCP servers and connectors"},
    {"source": "engineering_blogs", "url": "", "type": "blogs", "focus": "technical deep dives and announcements"},
    {"source": "model_registries", "url": "https://huggingface.co/models", "type": "models", "focus": "open-weight model releases"},
]

PROVIDER_CANDIDATES = [
    {"name": "pollinations", "source": "github", "url": "https://image.pollinations.ai", "type": "image_generation", "free_tier": True},
    {"name": "huggingface_inference", "source": "huggingface", "url": "https://api-inference.huggingface.co", "type": "inference_api", "free_tier": True},
    {"name": "siliconflow", "source": "provider_docs", "url": "https://api.siliconflow.cn", "type": "inference_api", "free_tier": True},
    {"name": "together", "source": "provider_docs", "url": "https://api.together.xyz", "type": "inference_api", "free_tier": True},
    {"name": "stability", "source": "provider_docs", "url": "https://api.stability.ai", "type": "image_generation", "free_tier": False},
    {"name": "replicate", "source": "provider_docs", "url": "https://api.replicate.com", "type": "multi_modal", "free_tier": True},
    {"name": "fal", "source": "provider_docs", "url": "https://fal.ai", "type": "image_generation", "free_tier": False},
    {"name": "craiyon", "source": "github", "url": "https://api.craiyon.com", "type": "image_generation", "free_tier": True},
    {"name": "black_forest_labs", "source": "huggingface", "url": "https://huggingface.co/black-forest-labs", "type": "image_generation", "free_tier": True},
    {"name": "deepseek", "source": "provider_docs", "url": "https://api.deepseek.com", "type": "inference_api", "free_tier": True},
    {"name": "groq", "source": "provider_docs", "url": "https://api.groq.com", "type": "inference_api", "free_tier": True},
    {"name": "fireworks", "source": "provider_docs", "url": "https://api.fireworks.ai", "type": "inference_api", "free_tier": True},
    {"name": "cerebras", "source": "provider_docs", "url": "https://api.cerebras.ai", "type": "inference_api", "free_tier": True},
    {"name": "novita", "source": "provider_docs", "url": "https://api.novita.ai", "type": "inference_api", "free_tier": True},
    {"name": "openrouter", "source": "provider_docs", "url": "https://openrouter.ai", "type": "router", "free_tier": True},
]


class ResearchAgent(BaseAgent):
    agent_name = "research"
    agent_description = "Monitors providers, models, and capabilities across the AI ecosystem"

    def __init__(self, config=None):
        super().__init__(config)
        self.data_dir = config.get("data_dir", "data/knowledge") if config else "data/knowledge"
        os.makedirs(self.data_dir, exist_ok=True)
        self._research_db: List[Dict[str, Any]] = []
        self._providers: List[Dict[str, Any]] = []
        self._load()

    def _load(self):
        path = os.path.join(self.data_dir, "research_database.json")
        if os.path.exists(path):
            try:
                with open(path) as f:
                    data = json.load(f)
                self._research_db = data.get("discoveries", [])
                self._providers = data.get("providers", [])
            except Exception:
                pass
        if not self._providers:
            self._providers = list(PROVIDER_CANDIDATES)

    def _save(self):
        path = os.path.join(self.data_dir, "research_database.json")
        with open(path, "w") as f:
            json.dump({
                "discoveries": self._research_db[-200:],
                "providers": self._providers,
                "sources": KNOWN_RESEARCH_SOURCES,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }, f, indent=2)

    def _execute_task(self, task: AgentTask) -> AgentResult:
        task_type = task.task_type
        if task_type == "research_provider":
            return self._research_provider(task)
        elif task_type == "discover_models":
            return self._discover_models(task)
        elif task_type == "get_sources":
            return self._get_sources()
        elif task_type == "get_providers":
            return self._get_providers()
        elif task_type == "add_discovery":
            return self._add_discovery(task)
        return AgentResult(success=True, data={"status": "unknown_task", "task_type": task_type})

    def _research_provider(self, task: AgentTask) -> AgentResult:
        provider_name = task.payload.get("name", "")
        existing = next((p for p in self._providers if p["name"] == provider_name), None)
        if existing:
            existing["last_researched"] = datetime.now(timezone.utc).isoformat()
            self._save()
            return AgentResult(data={"provider": existing, "status": "updated"})
        new_provider = {
            "name": provider_name, "source": task.payload.get("source", "manual"),
            "url": task.payload.get("url", ""), "type": task.payload.get("type", "unknown"),
            "free_tier": task.payload.get("free_tier", False),
            "discovered_at": datetime.now(timezone.utc).isoformat(),
        }
        self._providers.append(new_provider)
        self._save()
        return AgentResult(data={"provider": new_provider, "status": "added"})

    def _discover_models(self, task: AgentTask) -> AgentResult:
        source = task.payload.get("source", "all")
        models_found = []
        for p in self._providers:
            if source == "all" or p.get("source") == source:
                models_found.append({"provider": p["name"], "type": p.get("type", "unknown")})
        return AgentResult(data={"models": models_found, "total": len(models_found)})

    def _get_sources(self) -> AgentResult:
        return AgentResult(data={"sources": KNOWN_RESEARCH_SOURCES, "total": len(KNOWN_RESEARCH_SOURCES)})

    def _get_providers(self) -> AgentResult:
        return AgentResult(data={"providers": self._providers, "total": len(self._providers)})

    def _add_discovery(self, task: AgentTask) -> AgentResult:
        discovery = task.payload.copy()
        discovery["discovered_at"] = datetime.now(timezone.utc).isoformat()
        self._research_db.append(discovery)
        self._save()
        return AgentResult(data={"discovery": discovery, "total_discoveries": len(self._research_db)})

    def get_stats(self) -> Dict[str, Any]:
        base = super().get_stats()
        base.update({
            "total_providers": len(self._providers),
            "total_discoveries": len(self._research_db),
            "research_sources": len(KNOWN_RESEARCH_SOURCES),
            "free_providers": len([p for p in self._providers if p.get("free_tier")]),
        })
        return base
