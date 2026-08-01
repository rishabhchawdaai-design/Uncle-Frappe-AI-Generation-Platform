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

from .providers.base import ProviderStatus

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
        import httpx

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


# ── Provider Health Cycle ─────────────────────────────────────────────────────

DISABLE_THRESHOLD = 3  # consecutive failures before a provider is disabled


class ProviderHealthCycle:
    """Periodic, persisted health cycle over the provider registry.

    Checks every cloud provider, auto-disables providers after repeated
    failures (making them unavailable to the Generation Manager), auto-re-
    enables them when a check succeeds, and persists the health registry to
    ``data/registry/health_registry.json``.
    """

    def __init__(
        self,
        registry=None,
        health_path: Optional[str] = None,
        discovery_registry_path: Optional[str] = None,
    ):
        from pathlib import Path as _Path

        from .providers.registry import get_registry

        self._registry = registry if registry is not None else get_registry()
        self._monitor = HealthMonitor()
        self.health_path = _Path(health_path or _Path(__file__).resolve().parent.parent
                                 / "data" / "registry" / "health_registry.json")
        self.discovery_registry_path = discovery_registry_path

    def _load_persisted(self):
        import json

        try:
            if self.health_path.exists():
                data = json.loads(self.health_path.read_text())
                for entry in data.get("statuses", []):
                    status = HealthStatus(**{
                        k: v for k, v in entry.items()
                        if k in HealthStatus.__dataclass_fields__
                    })
                    self._monitor._statuses[status.provider] = status
        except Exception as e:  # pragma: no cover - defensive parse
            logger.debug("Could not load health registry: %s", e)

    def _health_endpoints(self) -> Dict[str, str]:
        endpoints = {}
        for provider in self._registry.get_all():
            if not provider.cloud_first or not provider.base_url:
                continue  # local runtimes are expected to be offline on demand
            endpoints[provider.name] = provider.base_url
        return endpoints

    def _apply(self, statuses: Dict[str, "HealthStatus"]) -> Dict[str, Any]:
        changes = {"disabled": [], "re_enabled": [], "degraded": []}
        for name, status in statuses.items():
            provider = self._registry.get(name)
            if provider is None:
                continue
            if not status.healthy:
                provider.record_error(status.last_error or "health check failed")
                if status.consecutive_failures >= DISABLE_THRESHOLD:
                    provider._status = ProviderStatus.UNAVAILABLE
                    changes["disabled"].append(name)
                else:
                    changes["degraded"].append(name)
            else:
                if provider._status == ProviderStatus.UNAVAILABLE:
                    changes["re_enabled"].append(name)
                provider._status = ProviderStatus.AVAILABLE
                provider._error_count = 0
        return changes

    async def run_cycle(self, write: bool = True) -> Dict[str, Any]:
        """Run one full health cycle and persist results."""
        from datetime import datetime as _dt

        self._load_persisted()
        endpoints = self._health_endpoints()
        if endpoints:
            statuses = await self._monitor.check_all(endpoints)
        else:
            statuses = {}
        changes = self._apply(statuses)
        report = {
            "checked_at": _dt.now().isoformat(),
            "checked_providers": sorted(statuses.keys()),
            "healthy": [n for n, s in statuses.items() if s.healthy],
            "unhealthy": [n for n, s in statuses.items() if not s.healthy],
            "changes": changes,
            "statuses": [s.to_dict() for s in statuses.values()],
        }
        if write:
            self.health_path.parent.mkdir(parents=True, exist_ok=True)
            import json

            self.health_path.write_text(json.dumps(report, indent=2, default=str))
        # Keep the persisted provider ranking in sync with health state.
        if self.discovery_registry_path:
            try:
                from .provider_discovery_registrar import ProviderDiscoveryRegistrar

                ProviderDiscoveryRegistrar(
                    registry=self._registry,
                    registry_path=self.discovery_registry_path,
                ).refresh()
            except Exception as e:  # pragma: no cover - advisory refresh
                logger.debug("Discovery refresh after health cycle failed: %s", e)
        return report
