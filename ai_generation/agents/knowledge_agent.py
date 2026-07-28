"""
Knowledge Agent — maintains provider graph, capability graph, benchmark history,
routing history, adapter cache, execution history, and health history.
Everything is searchable.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .base_agent import BaseAgent, AgentTask, AgentResult


class KnowledgeAgent(BaseAgent):
    agent_name = "knowledge"
    agent_description = "Maintains and queries the AIG-OS knowledge base"

    def __init__(self, config=None):
        super().__init__(config)
        self._knowledge: Dict[str, Any] = {
            "providers": {}, "models": {}, "capabilities": {},
            "benchmarks": {}, "routing": {}, "health": {}, "adapters": {},
        }
        self._search_index: Dict[str, List[str]] = {}
        self._query_log: List[Dict[str, Any]] = []

    def _execute_task(self, task: AgentTask) -> AgentResult:
        task_type = task.task_type
        if task_type == "store":
            return self._store_knowledge(task)
        elif task_type == "query":
            return self._query_knowledge(task)
        elif task_type == "search":
            return self._search_knowledge(task)
        elif task_type == "get_graph":
            return self._get_graph(task)
        elif task_type == "get_stats":
            return AgentResult(data=self._get_knowledge_stats())
        elif task_type == "export":
            return AgentResult(data=self._export_knowledge())
        return AgentResult(data={"status": "unknown_task"})

    def _store_knowledge(self, task: AgentTask) -> AgentResult:
        domain = task.payload.get("domain", "")
        key = task.payload.get("key", "")
        value = task.payload.get("value", {})
        if domain in self._knowledge:
            self._knowledge[domain][key] = value
            self._index_entry(domain, key, value)
            return AgentResult(data={"stored": True, "domain": domain, "key": key})
        return AgentResult(success=False, error=f"Unknown domain: {domain}")

    def _query_knowledge(self, task: AgentTask) -> AgentResult:
        domain = task.payload.get("domain", "")
        key = task.payload.get("key", "")
        if domain in self._knowledge:
            if key:
                value = self._knowledge[domain].get(key)
                if value:
                    return AgentResult(data=value)
            else:
                return AgentResult(data=self._knowledge[domain])
        return AgentResult(success=False, error=f"Not found: {domain}/{key}")

    def _search_knowledge(self, task: AgentTask) -> AgentResult:
        query = task.payload.get("query", "").lower()
        domain = task.payload.get("domain", "")
        results = {}
        sources = self._knowledge if not domain else {domain: self._knowledge.get(domain, {})}
        for dom, entries in sources.items():
            for key, value in entries.items():
                searchable = f"{key} {str(value)}".lower()
                if query in searchable:
                    results.setdefault(dom, {})[key] = value
        self._query_log.append({"query": query, "results": sum(len(v) for v in results.values()), "timestamp": datetime.now(timezone.utc).isoformat()})
        return AgentResult(data={"results": results, "total_matches": sum(len(v) for v in results.values())})

    def _get_graph(self, task: AgentTask) -> AgentResult:
        domain = task.payload.get("domain", "providers")
        entries = self._knowledge.get(domain, {})
        nodes = [{"id": k, "data": v} for k, v in entries.items()]
        return AgentResult(data={"domain": domain, "nodes": nodes, "total": len(nodes)})

    def _index_entry(self, domain: str, key: str, value: Any):
        text = f"{domain} {key} {str(value)}".lower()
        words = text.split()
        for word in words:
            if len(word) > 2:
                self._search_index.setdefault(word, []).append(f"{domain}/{key}")

    def _get_knowledge_stats(self) -> Dict[str, Any]:
        return {
            "domains": {dom: len(entries) for dom, entries in self._knowledge.items()},
            "total_entries": sum(len(entries) for entries in self._knowledge.values()),
            "index_size": len(self._search_index),
            "total_queries": len(self._query_log),
        }

    def _export_knowledge(self) -> Dict[str, Any]:
        return {
            "knowledge": self._knowledge,
            "stats": self._get_knowledge_stats(),
            "exported_at": datetime.now(timezone.utc).isoformat(),
        }

    def get_stats(self) -> Dict[str, Any]:
        base = super().get_stats()
        base.update(self._get_knowledge_stats())
        return base
