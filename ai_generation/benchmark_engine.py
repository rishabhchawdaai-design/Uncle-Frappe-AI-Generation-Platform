"""
Benchmark Engine — provider performance tracking, comparative benchmarks,
cost analysis, and latency profiling.
"""
import asyncio
import time
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class BenchmarkResult:
    provider: str
    prompt: str
    success: bool = False
    latency_ms: float = 0.0
    output_bytes: int = 0
    output_url: str = ""
    cost_estimate: float = 0.0
    error: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class ProviderScore:
    provider: str
    avg_latency_ms: float = 0.0
    success_rate: float = 0.0
    total_runs: int = 0
    successful_runs: int = 0
    total_cost: float = 0.0
    avg_output_size: float = 0.0
    score: float = 0.0


class BenchmarkEngine:
    """Track and compare provider performance."""

    def __init__(self):
        self._results: List[BenchmarkResult] = []
        self._scores: Dict[str, ProviderScore] = {}

    async def benchmark_provider(self, provider, prompt, width=1024, height=1024, runs=3):
        results = []
        for _ in range(runs):
            try:
                start = time.time()
                result = await provider.generate_image(
                    prompt=prompt, width=width, height=height,
                )
                latency = round((time.time() - start) * 1000, 1)
                br = BenchmarkResult(
                    provider=provider.name, prompt=prompt,
                    success=result.success, latency_ms=latency,
                    output_bytes=len(result.output_bytes) if result.output_bytes else 0,
                    output_url=result.output_url or "",
                    cost_estimate=result.cost_estimate,
                    error=result.error or "",
                )
                results.append(br)
                self._results.append(br)
            except Exception as e:
                br = BenchmarkResult(
                    provider=provider.name, prompt=prompt,
                    success=False, error=str(e)[:200],
                )
                results.append(br)
                self._results.append(br)

        self._update_score(provider.name)
        return results

    async def benchmark_all(self, registry, prompt, provider_type=None, width=1024, height=1024, runs=2):
        if provider_type:
            providers = registry.get_available(provider_type)
        else:
            providers = registry.get_available()

        all_results = {}
        for provider in providers:
            try:
                results = await self.benchmark_provider(provider, prompt, width, height, runs)
                all_results[provider.name] = results
            except Exception as e:
                all_results[provider.name] = [BenchmarkResult(provider=provider.name, prompt=prompt, error=str(e)[:200])]

        return all_results

    def _update_score(self, provider_name):
        provider_results = [r for r in self._results if r.provider == provider_name]
        if not provider_results:
            return

        successful = [r for r in provider_results if r.success]
        total = len(provider_results)
        avg_latency = sum(r.latency_ms for r in successful) / max(len(successful), 1)
        success_rate = len(successful) / max(total, 1) * 100
        total_cost = sum(r.cost_estimate for r in provider_results)
        avg_output = sum(r.output_bytes for r in successful) / max(len(successful), 1)

        score = (
            min(success_rate, 100) * 0.4
            + max(0, 100 - avg_latency / 100) * 0.3
            + max(0, 100 - total_cost * 10) * 0.2
            + min(avg_output / 10000, 100) * 0.1
        )

        self._scores[provider_name] = ProviderScore(
            provider=provider_name, avg_latency_ms=round(avg_latency, 1),
            success_rate=round(success_rate, 1), total_runs=total,
            successful_runs=len(successful), total_cost=round(total_cost, 4),
            avg_output_size=round(avg_output), score=round(score, 2),
        )

    def get_rankings(self):
        return sorted(self._scores.values(), key=lambda s: s.score, reverse=True)

    def get_provider_report(self, provider_name):
        score = self._scores.get(provider_name)
        results = [r for r in self._results if r.provider == provider_name]
        return {
            "score": score.__dict__ if score else None,
            "recent_results": [r.__dict__ for r in results[-20:]],
        }

    def get_comparison(self, provider_names=None):
        scores = self._scores
        if provider_names:
            scores = {k: v for k, v in scores.items() if k in provider_names}
        return {
            provider: {
                "score": s.score, "success_rate": s.success_rate,
                "avg_latency_ms": s.avg_latency_ms, "total_cost": s.total_cost,
            }
            for provider, s in scores.items()
        }

    def get_stats(self):
        return {
            "total_benchmarks": len(self._results),
            "providers_tested": len(self._scores),
            "rankings": [
                {"provider": s.provider, "score": s.score, "success_rate": s.success_rate}
                for s in self.get_rankings()
            ],
        }
