"""
Benchmark Lab — standardized benchmark suites for provider evaluation.
Measures quality, speed, reliability, and cost across all providers.
"""
import json
import os
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


BENCHMARK_PROMPTS = {
    "realism": [
        "a photorealistic portrait of a woman in golden hour lighting",
        "a hyper-realistic macro photo of a dewdrop on a leaf",
        "a realistic street scene in Tokyo at night",
    ],
    "prompt_adherence": [
        "a red cat sitting on a blue chair in a green room",
        "an astronaut riding a horse on Mars with two moons",
        "a vintage coffee shop with exposed brick and warm lighting",
    ],
    "anatomy": [
        "a full body portrait of a person standing",
        "a hand holding a coffee cup, detailed fingers",
        "two people shaking hands in an office",
    ],
    "typography": [
        "a sign that says HELLO WORLD in bold letters",
        "a magazine cover with the title VOL 1 ISSUE 1",
        "a neon sign reading OPEN 24 HOURS",
    ],
    "composition": [
        "a golden ratio composition of a spiral staircase",
        "rule of thirds landscape with a lighthouse",
        "symmetrical architecture of a cathedral interior",
    ],
    "lighting": [
        "dramatic chiaroscuro portrait with single light source",
        "soft diffused natural lighting on a flower arrangement",
        "neon cyberpunk lighting on a rainy street",
    ],
}


@dataclass
class BenchmarkResult:
    benchmark_id: str = ""
    provider: str = ""
    model: str = ""
    category: str = ""
    prompt: str = ""
    quality_score: float = 0.0
    prompt_adherence: float = 0.0
    latency_ms: float = 0.0
    success: bool = False
    error: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = ""

    def __post_init__(self):
        if not self.benchmark_id:
            self.benchmark_id = str(uuid.uuid4())[:8]
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "benchmark_id": self.benchmark_id, "provider": self.provider, "model": self.model,
            "category": self.category, "prompt": self.prompt[:50],
            "quality_score": round(self.quality_score, 2), "prompt_adherence": round(self.prompt_adherence, 2),
            "latency_ms": round(self.latency_ms, 1), "success": self.success, "error": self.error,
            "timestamp": self.timestamp,
        }


@dataclass
class ProviderScore:
    provider: str = ""
    total_benchmarks: int = 0
    avg_quality: float = 0.0
    avg_prompt_adherence: float = 0.0
    avg_latency_ms: float = 0.0
    success_rate: float = 0.0
    category_scores: Dict[str, float] = field(default_factory=dict)
    composite_score: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "provider": self.provider, "total_benchmarks": self.total_benchmarks,
            "avg_quality": round(self.avg_quality, 2), "avg_prompt_adherence": round(self.avg_prompt_adherence, 2),
            "avg_latency_ms": round(self.avg_latency_ms, 1), "success_rate": round(self.success_rate, 2),
            "composite_score": round(self.composite_score, 2),
            "category_scores": {k: round(v, 2) for k, v in self.category_scores.items()},
        }


class BenchmarkLab:
    """Standardized benchmark suite for AIG-OS provider evaluation."""

    def __init__(self, data_dir: str = "data/benchmarks"):
        self.data_dir = data_dir
        self._results: List[BenchmarkResult] = []
        self._scores: Dict[str, ProviderScore] = {}
        os.makedirs(data_dir, exist_ok=True)
        self._load()

    def _load(self):
        path = os.path.join(self.data_dir, "benchmark_results.json")
        if os.path.exists(path):
            try:
                with open(path) as f:
                    data = json.load(f)
                for rd in data.get("results", []):
                    self._results.append(BenchmarkResult(**rd))
                for sd in data.get("scores", []):
                    ps = ProviderScore(**sd)
                    self._scores[ps.provider] = ps
            except Exception:
                pass

    def _save(self):
        path = os.path.join(self.data_dir, "benchmark_results.json")
        data = {
            "results": [r.to_dict() for r in self._results[-500:]],
            "scores": [s.to_dict() for s in self._scores.values()],
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    def get_benchmark_prompts(self, category: str) -> List[str]:
        return BENCHMARK_PROMPTS.get(category, [])

    def get_all_categories(self) -> List[str]:
        return list(BENCHMARK_PROMPTS.keys())

    def record_result(self, result: BenchmarkResult):
        self._results.append(result)
        self._update_scores(result)
        self._save()

    def _update_scores(self, result: BenchmarkResult):
        provider = result.provider
        if provider not in self._scores:
            self._scores[provider] = ProviderScore(provider=provider)

        ps = self._scores[provider]
        ps.total_benchmarks += 1

        if result.success:
            total_success = ps.success_rate * (ps.total_benchmarks - 1) + 1
            ps.success_rate = total_success / ps.total_benchmarks
            if result.quality_score > 0:
                ps.avg_quality = (ps.avg_quality * (ps.total_benchmarks - 1) + result.quality_score) / ps.total_benchmarks
            if result.prompt_adherence > 0:
                ps.avg_prompt_adherence = (ps.avg_prompt_adherence * (ps.total_benchmarks - 1) + result.prompt_adherence) / ps.total_benchmarks
            if result.latency_ms > 0:
                ps.avg_latency_ms = (ps.avg_latency_ms * (ps.total_benchmarks - 1) + result.latency_ms) / ps.total_benchmarks
            if result.category:
                cat_scores = ps.category_scores.get(result.category, 0.5)
                ps.category_scores[result.category] = (cat_scores * 0.8 + result.quality_score * 0.2)
        else:
            total_success = ps.success_rate * (ps.total_benchmarks - 1)
            ps.success_rate = total_success / ps.total_benchmarks

        speed_score = max(0, 1.0 - min(ps.avg_latency_ms / 30000, 1.0))
        ps.composite_score = (
            ps.avg_quality * 0.3 +
            ps.avg_prompt_adherence * 0.25 +
            speed_score * 0.15 +
            ps.success_rate * 0.3
        )

    def get_provider_score(self, provider: str) -> Optional[Dict[str, Any]]:
        ps = self._scores.get(provider)
        return ps.to_dict() if ps else None

    def get_leaderboard(self) -> List[Dict[str, Any]]:
        scores = sorted(self._scores.values(), key=lambda s: s.composite_score, reverse=True)
        return [s.to_dict() for s in scores]

    def get_results(self, provider: Optional[str] = None, category: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        results = self._results
        if provider:
            results = [r for r in results if r.provider == provider]
        if category:
            results = [r for r in results if r.category == category]
        return [r.to_dict() for r in results[-limit:]]

    def get_stats(self) -> Dict[str, Any]:
        return {
            "total_results": len(self._results),
            "total_providers": len(self._scores),
            "total_categories": len(BENCHMARK_PROMPTS),
            "top_provider": self.get_leaderboard()[0]["provider"] if self._scores else None,
            "avg_success_rate": round(
                sum(s.success_rate for s in self._scores.values()) / max(len(self._scores), 1), 2
            ),
        }
