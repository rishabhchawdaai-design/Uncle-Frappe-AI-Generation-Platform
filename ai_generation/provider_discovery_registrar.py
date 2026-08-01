"""
Provider Discovery Registrar — persisted provider network state.

Combines the live provider registry (tier, availability, success rate,
latency, capabilities) with benchmark results into one ranked, durable view
written to ``data/registry/provider_discovery.json``. The Generation Manager
uses the ranked order for automatic routing, so provider ranking survives
restarts and fresh clones without re-running discovery.

The registrar never performs network I/O: it is a pure aggregation layer over
data the platform already collects (provider stats + benchmark scores).
"""
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from .providers.base import ProviderTier
from .providers.registry import get_registry

logger = logging.getLogger(__name__)

DEFAULT_REGISTRY_PATH = (
    Path(__file__).resolve().parent.parent
    / "data" / "registry" / "provider_discovery.json"
)
DEFAULT_BENCHMARKS_PATH = (
    Path(__file__).resolve().parent.parent
    / "data" / "benchmarks" / "benchmark_results.json"
)

_TIER_BONUS = {
    ProviderTier.FREE: 30,
    ProviderTier.COMMUNITY: 15,
    ProviderTier.PAID: 0,
    ProviderTier.ENTERPRISE: -10,
}


class ProviderDiscoveryRegistrar:
    """Aggregate, rank, and persist provider network state."""

    def __init__(
        self,
        registry=None,
        registry_path: Optional[str] = None,
        benchmarks_path: Optional[str] = None,
    ):
        self._registry = registry if registry is not None else get_registry()
        self.registry_path = Path(
            registry_path or DEFAULT_REGISTRY_PATH)
        self.benchmarks_path = Path(
            benchmarks_path or DEFAULT_BENCHMARKS_PATH)
        self._cache: Optional[Dict[str, Any]] = None

    # ── data sources ──────────────────────────────────────────────

    def _load_benchmarks(self) -> Dict[str, Dict[str, float]]:
        """Provider -> benchmark summary from the committed benchmark file."""
        try:
            if not self.benchmarks_path.exists():
                return {}
            data = json.loads(self.benchmarks_path.read_text())
            scores = data.get("scores", []) if isinstance(data, dict) else []
        except Exception as e:  # pragma: no cover - defensive parse
            logger.debug("Could not load benchmarks: %s", e)
            return {}
        result: Dict[str, Dict[str, float]] = {}
        for entry in scores:
            provider = entry.get("provider")
            if not provider:
                continue
            result[provider] = {
                "composite_score": float(entry.get("composite_score", 0.0) or 0.0),
                "avg_quality": float(entry.get("avg_quality", 0.0) or 0.0),
                "avg_latency_ms": float(entry.get("avg_latency_ms", 0.0) or 0.0),
                "success_rate": float(entry.get("success_rate", 0.0) or 0.0),
                "total_benchmarks": int(entry.get("total_benchmarks", 0) or 0),
            }
        return result

    def _provider_snapshots(self) -> List[Dict[str, Any]]:
        snapshots = []
        for provider in self._registry.get_all():
            stats = provider.get_stats()
            snapshots.append({
                "name": provider.name,
                "type": stats["type"],
                "tier": stats["tier"],
                "available": bool(provider.is_available),
                "status": stats["status"],
                "requires_api_key": stats["requires_api_key"],
                "has_api_key": stats["has_api_key"],
                "cloud_first": stats["cloud_first"],
                "models": stats["models"],
                "capabilities": stats["capabilities"],
                "success_rate": stats["success_rate"],
                "avg_latency_ms": stats["avg_latency_ms"],
            })
        return snapshots

    # ── ranking ───────────────────────────────────────────────────

    def _score_provider(
        self,
        snapshot: Dict[str, Any],
        benchmark: Optional[Dict[str, float]],
    ) -> float:
        score = 0.0
        tier = snapshot["tier"]
        try:
            score += _TIER_BONUS.get(ProviderTier(tier), 0)
        except ValueError:  # pragma: no cover - unknown tier string
            pass
        if not snapshot["requires_api_key"] or snapshot["has_api_key"]:
            score += 10
        if snapshot["available"]:
            score += 20 if snapshot["status"] == "available" else 5
        score += snapshot["success_rate"] * 0.4
        score -= min(snapshot["avg_latency_ms"] / 1000.0, 40.0)
        if benchmark:
            score += min(benchmark.get("composite_score", 0.0) * 50.0, 50.0)
            score -= min(benchmark.get("avg_latency_ms", 0.0) / 1000.0, 40.0)
        return round(score, 3)

    def rank(
        self,
        provider_type: str = "",
        prefer_free: bool = True,
    ) -> List[Dict[str, Any]]:
        """Rank registered providers by fitness for a provider type."""
        benchmarks = self._load_benchmarks()
        ranked = []
        for snapshot in self._provider_snapshots():
            if provider_type and snapshot["type"] != provider_type:
                continue
            if prefer_free and snapshot["requires_api_key"] and not snapshot["has_api_key"]:
                # keyless and configured providers first; key-gated providers
                # without keys remain listed but rank below usable ones.
                pass
            bench = benchmarks.get(snapshot["name"])
            entry = dict(snapshot)
            entry["rank_score"] = self._score_provider(snapshot, bench)
            entry["benchmark"] = bench or {}
            ranked.append(entry)
        ranked.sort(
            key=lambda e: (
                e["rank_score"],
                -1 if (not e["requires_api_key"] or e["has_api_key"]) else 0,
                e["name"],
            ),
            reverse=True,
        )
        for idx, entry in enumerate(ranked):
            entry["rank"] = idx + 1
        return ranked

    # ── persistence ───────────────────────────────────────────────

    def refresh(self, write: bool = True) -> Dict[str, Any]:
        """Build the full provider network report and persist it."""
        providers = self._provider_snapshots()
        types = sorted({p["type"] for p in providers})
        report: Dict[str, Any] = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "provider_types": types,
            "providers": providers,
            "ranked_by_type": {
                t: [
                    {k: e[k] for k in (
                        "rank", "name", "type", "tier", "status", "available",
                        "requires_api_key", "has_api_key", "rank_score",
                        "avg_latency_ms", "success_rate",
                    )}
                    for e in self.rank(t)
                ]
                for t in types
            },
            "summary": {
                "total_providers": len(providers),
                "available": sum(1 for p in providers if p["available"]),
                "free": sum(1 for p in providers if p["tier"] == "free"),
                "by_type": {},
            },
        }
        for p in providers:
            report["summary"]["by_type"][p["type"]] = (
                report["summary"]["by_type"].get(p["type"], 0) + 1)
        if write:
            self.registry_path.parent.mkdir(parents=True, exist_ok=True)
            self.registry_path.write_text(
                json.dumps(report, indent=2, default=str))
        self._cache = report
        return report

    def get_report(self, refresh_if_missing: bool = True) -> Dict[str, Any]:
        if self._cache is not None:
            return self._cache
        if self.registry_path.exists():
            try:
                self._cache = json.loads(self.registry_path.read_text())
                return self._cache
            except Exception as e:  # pragma: no cover - defensive parse
                logger.debug("Could not read discovery registry: %s", e)
        if refresh_if_missing:
            return self.refresh()
        return {"generated_at": "", "providers": [], "ranked_by_type": {}}

    def get_ranked_order(self, provider_type: str) -> List[str]:
        """Ranked provider names for a provider type (for the Generation Manager)."""
        report = self.get_report(refresh_if_missing=False)
        ranked = report.get("ranked_by_type", {}).get(provider_type, [])
        return [entry["name"] for entry in ranked]

    def get_stats(self) -> Dict[str, Any]:
        report = self.get_report(refresh_if_missing=False)
        summary = report.get("summary", {})
        return {
            "path": str(self.registry_path),
            "generated_at": report.get("generated_at", ""),
            "provider_types": report.get("provider_types", []),
            **summary,
        }
