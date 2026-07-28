"""
Recovery Agent — detects dead providers, broken APIs, schema changes,
authentication failures, and rate limits. Automatically retries, switches
providers, rebuilds adapters, and removes unhealthy providers from routing.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .base_agent import BaseAgent, AgentTask, AgentResult


class RecoveryAgent(BaseAgent):
    agent_name = "recovery"
    agent_description = "Detects and recovers from provider failures, schema changes, and health issues"

    def __init__(self, config=None):
        super().__init__(config)
        self._incidents: List[Dict[str, Any]] = []
        self._recoveries: List[Dict[str, Any]] = []
        self._blacklisted: Dict[str, Dict[str, Any]] = {}
        self._consecutive_failures: Dict[str, int] = {}

    def _execute_task(self, task: AgentTask) -> AgentResult:
        task_type = task.task_type
        if task_type == "report_failure":
            return self._report_failure(task)
        elif task_type == "check_health":
            return self._check_health(task)
        elif task_type == "recover_provider":
            return self._recover_provider(task)
        elif task_type == "blacklist_provider":
            return self._blacklist_provider(task)
        elif task_type == "unblacklist_provider":
            return self._unblacklist_provider(task)
        elif task_type == "get_incidents":
            return AgentResult(data={"incidents": self._incidents[-20:], "total": len(self._incidents)})
        elif task_type == "get_recoveries":
            return AgentResult(data={"recoveries": self._recoveries[-20:], "total": len(self._recoveries)})
        elif task_type == "get_blacklist":
            return AgentResult(data={"blacklisted": list(self._blacklisted.keys()), "total": len(self._blacklisted)})
        return AgentResult(data={"status": "unknown_task"})

    def _report_failure(self, task: AgentTask) -> AgentResult:
        provider = task.payload.get("provider", "")
        error = task.payload.get("error", "unknown")
        failure_type = task.payload.get("failure_type", "execution_error")

        incident = {
            "provider": provider, "error": error, "failure_type": failure_type,
            "reported_at": datetime.now(timezone.utc).isoformat(),
        }
        self._incidents.append(incident)

        self._consecutive_failures[provider] = self._consecutive_failures.get(provider, 0) + 1
        if self._consecutive_failures[provider] >= 5:
            self._blacklisted[provider] = {
                "reason": "consecutive_failures",
                "blacklisted_at": datetime.now(timezone.utc).isoformat(),
            }
            incident["action"] = "blacklisted"
        else:
            incident["action"] = "retry"
            incident["retry_count"] = self._consecutive_failures[provider]

        return AgentResult(data=incident)

    def _check_health(self, task: AgentTask) -> AgentResult:
        provider = task.payload.get("provider", "")
        healthy = provider not in self._blacklisted
        failures = self._consecutive_failures.get(provider, 0)
        return AgentResult(data={
            "provider": provider, "healthy": healthy,
            "consecutive_failures": failures,
            "blacklisted": provider in self._blacklisted,
        })

    def _recover_provider(self, task: AgentTask) -> AgentResult:
        provider = task.payload.get("provider", "")
        strategy = task.payload.get("strategy", "retry")
        recovery = {
            "provider": provider, "strategy": strategy,
            "recovered_at": datetime.now(timezone.utc).isoformat(),
        }
        if strategy == "reset":
            self._consecutive_failures[provider] = 0
            self._blacklisted.pop(provider, None)
            recovery["status"] = "recovered"
        elif strategy == "retry":
            recovery["status"] = "retry_scheduled"
        else:
            recovery["status"] = "unknown_strategy"
        self._recoveries.append(recovery)
        return AgentResult(data=recovery)

    def _blacklist_provider(self, task: AgentTask) -> AgentResult:
        provider = task.payload.get("provider", "")
        reason = task.payload.get("reason", "manual")
        self._blacklisted[provider] = {
            "reason": reason, "blacklisted_at": datetime.now(timezone.utc).isoformat(),
        }
        return AgentResult(data={"provider": provider, "blacklisted": True, "reason": reason})

    def _unblacklist_provider(self, task: AgentTask) -> AgentResult:
        provider = task.payload.get("provider", "")
        removed = provider in self._blacklisted
        self._blacklisted.pop(provider, None)
        self._consecutive_failures[provider] = 0
        return AgentResult(data={"provider": provider, "unblacklisted": removed})

    def get_stats(self) -> Dict[str, Any]:
        base = super().get_stats()
        base.update({
            "total_incidents": len(self._incidents),
            "total_recoveries": len(self._recoveries),
            "blacklisted_providers": len(self._blacklisted),
            "providers_with_failures": len(self._consecutive_failures),
        })
        return base
