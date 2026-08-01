"""
Tests for the Provider Discovery Registrar: provider network persistence,
deterministic free-first ranking, and Generation Manager ranked routing.
"""
import asyncio
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from ai_generation.providers.base import (  # noqa: E402
    GenerationResult, ImageProvider, ProviderCapability, ProviderTier,
    ProviderType,
)
from ai_generation.providers.registry import get_registry  # noqa: E402


class StubImageProvider(ImageProvider):
    name = "stub"

    def __init__(self, name, tier=ProviderTier.FREE, requires_api_key=False,
                 has_key=False, available=True, success_rate=100.0,
                 latency_ms=500.0):
        self.name = name
        self.tier = tier
        self.requires_api_key = requires_api_key
        self.cloud_first = True
        self.provider_type = ProviderType.IMAGE
        self.supported_models = ["v1"]
        self.capabilities = [ProviderCapability(name="text_to_image")]
        super().__init__({"api_key": "key" if has_key else ""})
        self._success_count = int(success_rate)
        self._error_count = 0 if success_rate >= 100 else 10
        self._total_latency_ms = latency_ms * (self._success_count + self._error_count)
        if not available:
            self._error_count = 99

    async def generate_image(self, **kwargs):
        return GenerationResult(provider=self.name, status="success")


class FakeRegistry:
    def __init__(self, providers):
        self._providers = providers

    def get_all(self):
        return list(self._providers)


def _write_discovery(registry_path, ranked_map):
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "generated_at": "2026-08-01T00:00:00+00:00",
        "provider_types": list(ranked_map.keys()),
        "ranked_by_type": {
            t: [{"name": name} for name in names]
            for t, names in ranked_map.items()
        },
        "summary": {"total_providers": 0, "available": 0, "free": 0},
    }
    registry_path.write_text(json.dumps(report))


def test_rank_free_keyless_first():
    from ai_generation.provider_discovery_registrar import ProviderDiscoveryRegistrar

    free_keyless = StubImageProvider(
        "free_keyless", ProviderTier.FREE, requires_api_key=False)
    paid_key = StubImageProvider(
        "paid_key", ProviderTier.PAID, requires_api_key=True, has_key=False)
    community_key = StubImageProvider(
        "community_key", ProviderTier.COMMUNITY, requires_api_key=True, has_key=True)

    registrar = ProviderDiscoveryRegistrar(
        registry=FakeRegistry([community_key, paid_key, free_keyless]),
        registry_path="/tmp/nonexistent-discovery.json",
        benchmarks_path="/tmp/nonexistent-benchmarks.json",
    )
    ranked = registrar.rank(provider_type="image")
    assert ranked[0]["name"] == "free_keyless"
    names = [e["name"] for e in ranked]
    assert names.index("free_keyless") < names.index("community_key")
    assert names.index("community_key") < names.index("paid_key")
    assert ranked[0]["rank"] == 1
    assert ranked[0]["rank_score"] > ranked[-1]["rank_score"]


def test_rank_benchmarks_boost():
    from ai_generation.provider_discovery_registrar import ProviderDiscoveryRegistrar

    a = StubImageProvider("a", ProviderTier.FREE, latency_ms=2000.0)
    b = StubImageProvider("b", ProviderTier.FREE, latency_ms=2000.0)
    registry = FakeRegistry([a, b])
    benchmarks_path = "/tmp/bench-tmp.json"
    with open(benchmarks_path, "w") as f:
        json.dump({
            "scores": [
                {"provider": "b", "composite_score": 0.95, "avg_latency_ms": 100,
                 "avg_quality": 0.9, "success_rate": 1.0, "total_benchmarks": 5},
            ],
        }, f)
    registrar = ProviderDiscoveryRegistrar(
        registry=registry,
        registry_path="/tmp/nonexistent-discovery.json",
        benchmarks_path=benchmarks_path,
    )
    ranked = registrar.rank()
    assert ranked[0]["name"] == "b"
    assert ranked[0]["benchmark"]["composite_score"] == 0.95


def test_refresh_persists_and_reads_back(tmp_path):
    from ai_generation.provider_discovery_registrar import ProviderDiscoveryRegistrar

    reg_path = tmp_path / "provider_discovery.json"
    registrar = ProviderDiscoveryRegistrar(
        registry=FakeRegistry([StubImageProvider("x", ProviderTier.FREE)]),
        registry_path=str(reg_path),
        benchmarks_path=str(tmp_path / "no-bench.json"),
    )
    report = registrar.refresh()
    assert reg_path.exists()
    assert report["summary"]["total_providers"] == 1
    assert "x" in [e["name"] for e in report["ranked_by_type"]["image"]]

    registrar2 = ProviderDiscoveryRegistrar(
        registry=FakeRegistry([]), registry_path=str(reg_path),
    )
    assert registrar2.get_ranked_order("image") == ["x"]


def test_generation_manager_uses_ranked_order(tmp_path):
    from ai_generation.generation_manager import GenerationManager, GenerationRequest
    from ai_generation.providers.base import ProviderType

    reg_path = tmp_path / "provider_discovery.json"
    available = [p for p in get_registry().get_available(ProviderType.IMAGE)]
    names = [p.name for p in available]
    assert len(names) >= 2
    # write a ranked order with pollinations last and everything else first
    reversed_order = [n for n in reversed(names)]
    _write_discovery(reg_path, {"image": reversed_order})

    mgr = GenerationManager(config={"discovery_registry_path": str(reg_path)})
    plan = mgr.plan_generation(
        GenerationRequest(prompt="x", provider_type=ProviderType.IMAGE))
    assert plan.provider_order == reversed_order


def test_generation_manager_ranked_order_ignores_unknown(tmp_path):
    from ai_generation.generation_manager import GenerationManager, GenerationRequest
    from ai_generation.providers.base import ProviderType

    reg_path = tmp_path / "provider_discovery.json"
    _write_discovery(reg_path, {"image": ["does_not_exist", "also_missing"]})
    mgr = GenerationManager(config={"discovery_registry_path": str(reg_path)})
    plan = mgr.plan_generation(
        GenerationRequest(prompt="x", provider_type=ProviderType.IMAGE))
    # unknown ranked names must not replace the registry-derived plan
    assert "does_not_exist" not in plan.provider_order
    assert len(plan.provider_order) >= 2


def test_sdk_provider_ranking_surface(tmp_path):
    from ai_generation import UncleFrappeAI

    reg_path = tmp_path / "provider_discovery.json"
    _write_discovery(reg_path, {"image": ["pollinations"]})
    ai = UncleFrappeAI()
    ranked = ai.get_provider_ranking(provider_type="image", registry_path=str(reg_path))
    assert isinstance(ranked, list)
    assert "rank" in ranked[0]


def test_mcp_provider_ranking_tool(tmp_path):
    from ai_generation.mcp_tools import MCP_GENERATION_TOOLS, MCPGenerationTools

    assert "get_provider_ranking" in MCP_GENERATION_TOOLS
    reg_path = tmp_path / "provider_discovery.json"
    _write_discovery(reg_path, {"image": ["pollinations"]})
    import ai_generation.provider_discovery_registrar as pdr
    pdr.DEFAULT_REGISTRY_PATH = reg_path
    try:
        tools = MCPGenerationTools()
        result = asyncio.run(tools.handle(
            "get_provider_ranking", {"provider_type": "image"}))
        assert result["count"] >= 1
        assert result["ranked"][0]["rank"] == 1
    finally:
        del pdr  # restore nothing; registry_path is per-call below
