"""
Health Monitor — continuous provider health monitoring and latency tracking.
Never assumes a provider is available because it existed previously.
"""
import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)


@dataclass
class HealthStatus:
    provider: str = ""
    healthy: bool = True
    latency_ms: float = 0.0
    last_check: str = ""
    consecutive_failures: int = 0
    last_error: str = ""
    status_code: int = 0
    health_url: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "provider": self.provider,
            "healthy": self.healthy,
            "latency_ms": round(self.latency_ms, 1),
            "consecutive_failures": self.consecutive_failures,
            "last_error": self.last_error,
            "last_check": self.last_check,
        }


class HealthMonitor:
    """Continuous provider health monitoring."""

    def __init__(self):
        self._statuses: Dict[str, HealthStatus] = {}
        self._check_history: List[Dict[str, Any]] = []

    def register_provider(self, name: str, health_url: str = ""):
        if name not in self._statuses:
            self._statuses[name] = HealthStatus(provider=name, health_url=health_url)

    async def check_provider(self, name: str, url: str) -> HealthStatus:
        status = self._statuses.get(name, HealthStatus(provider=name))
        start = time.time()
        try:
            async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
                r = await client.get(url)
                latency = round((time.time() - start) * 1000, 1)
                status.healthy = r.status_code < 500
                status.latency_ms = latency
                status.status_code = r.status_code
                status.last_check = datetime.now().isoformat()
                if status.healthy:
                    status.consecutive_failures = 0
                else:
                    status.consecutive_failures += 1
                status.last_error = "" if status.healthy else f"HTTP {r.status_code}"
        except Exception as e:
            latency = round((time.time() - start) * 1000, 1)
            status.healthy = False
            status.latency_ms = latency
            status.consecutive_failures += 1
            status.last_error = str(e)[:100]
            status.last_check = datetime.now().isoformat()

        self._statuses[name] = status
        self._check_history.append(status.to_dict())
        return status

    async def check_all(self, endpoints: Dict[str, str]) -> Dict[str, HealthStatus]:
        """Check all providers. endpoints = {name: url}."""
        tasks = [self.check_provider(name, url) for name, url in endpoints.items()]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        statuses = {}
        for name, result in zip(endpoints.keys(), results):
            if isinstance(result, HealthStatus):
                statuses[name] = result
            else:
                statuses[name] = HealthStatus(provider=name, healthy=False, last_error=str(result)[:100])
        return statuses

    def get_status(self, name: str) -> Optional[Dict[str, Any]]:
        status = self._statuses.get(name)
        return status.to_dict() if status else None

    def get_all_statuses(self) -> Dict[str, Any]:
        return {name: s.to_dict() for name, s in self._statuses.items()}

    def is_healthy(self, name: str) -> bool:
        status = self._statuses.get(name)
        return status.healthy if status else False

    def get_healthy_providers(self) -> List[str]:
        return [name for name, s in self._statuses.items() if s.healthy]

    def get_unhealthy_providers(self) -> List[str]:
        return [name for name, s in self._statuses.items() if not s.healthy]

    def get_stats(self) -> Dict[str, Any]:
        healthy = sum(1 for s in self._statuses.values() if s.healthy)
        total = len(self._statuses)
        avg_latency = sum(s.latency_ms for s in self._statuses.values() if s.healthy) / max(healthy, 1)
        return {
            "total_monitored": total,
            "healthy": healthy,
            "unhealthy": total - healthy,
            "avg_latency_ms": round(avg_latency, 1),
            "checks_performed": len(self._check_history),
        }
