"""
Tests for the Provider Health Cycle: persisted health registry, automatic
provider disabling after repeated failures, and re-enabling when fixed.
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


class FakeResponse:
    def __init__(self, status_code):
        self.status_code = status_code


class RoutingFakeClient:
    """Fake httpx.AsyncClient that fails providers whose name is in their URL."""

    def __init__(self, healthy_suffixes=(), **kwargs):
        self.healthy_suffixes = healthy_suffixes

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def get(self, url, **kwargs):
        if any(s in url for s in self.healthy_suffixes):
            return FakeResponse(200)
        if "bad" in url:
            return FakeResponse(500)
        return FakeResponse(200)


class StubCloudProvider(ImageProvider):
    name = "stub"

    def __init__(self, name, base_url="", cloud_first=True):
        self.name = name
        self.cloud_first = cloud_first
        self.base_url = base_url or f"https://{name}.example.test"
        self.tier = ProviderTier.FREE
        self.requires_api_key = False
        self.provider_type = ProviderType.IMAGE
        self.supported_models = ["v1"]
        self.capabilities = [ProviderCapability(name="text_to_image")]
        super().__init__({})

    async def generate_image(self, **kwargs):
        return GenerationResult(provider=self.name, status="success")


class FakeRegistry:
    def __init__(self, providers):
        self._providers = providers

    def get_all(self):
        return list(self._providers)

    def get(self, name):
        for p in self._providers:
            if p.name == name:
                return p
        return None


@pytest.fixture
def fake_http(monkeypatch):
    import httpx

    monkeypatch.setattr(httpx, "AsyncClient", RoutingFakeClient)


def test_cycle_disables_unhealthy_and_persists(fake_http, tmp_path):
    from ai_generation.health_monitor import DISABLE_THRESHOLD, ProviderHealthCycle
    from ai_generation.providers.base import ProviderStatus

    good = StubCloudProvider("good")
    bad = StubCloudProvider("bad")
    registry = FakeRegistry([good, bad])
    cycle = ProviderHealthCycle(
        registry=registry,
        health_path=str(tmp_path / "health_registry.json"),
    )
    for _ in range(DISABLE_THRESHOLD):
        report = asyncio.run(cycle.run_cycle())

    assert bad.is_available is False
    assert bad._status == ProviderStatus.UNAVAILABLE
    assert good.is_available is True
    assert report["changes"]["disabled"] == ["bad"]
    assert "good" in report["healthy"]
    assert "bad" in report["unhealthy"]

    persisted = json.loads((tmp_path / "health_registry.json").read_text())
    assert persisted["checked_at"]
    assert {s["provider"] for s in persisted["statuses"]} == {"good", "bad"}


def test_cycle_does_not_disable_after_single_failure(fake_http, tmp_path):
    from ai_generation.health_monitor import ProviderHealthCycle

    bad = StubCloudProvider("bad")
    cycle = ProviderHealthCycle(
        registry=FakeRegistry([bad]),
        health_path=str(tmp_path / "h.json"),
    )
    report = asyncio.run(cycle.run_cycle())
    assert report["changes"]["disabled"] == []
    assert bad.is_available is True  # below the threshold


def test_cycle_re_enables_fixed_provider(fake_http, tmp_path):
    from ai_generation.health_monitor import DISABLE_THRESHOLD, ProviderHealthCycle
    from ai_generation.providers.base import ProviderStatus

    bad = StubCloudProvider("bad")
    registry = FakeRegistry([bad])
    cycle = ProviderHealthCycle(
        registry=registry,
        health_path=str(tmp_path / "h.json"),
    )
    for _ in range(DISABLE_THRESHOLD):
        asyncio.run(cycle.run_cycle())
    assert bad.is_available is False

    # provider recovers: swap the fake so "bad" is healthy again
    import httpx

    class HealthyClient(RoutingFakeClient):
        async def get(self, url, **kwargs):
            return FakeResponse(200)

    httpx.AsyncClient = HealthyClient
    report = asyncio.run(cycle.run_cycle())
    assert report["changes"]["re_enabled"] == ["bad"]
    assert bad.is_available is True
    assert bad._status == ProviderStatus.AVAILABLE


def test_cycle_skips_local_providers(fake_http, tmp_path):
    from ai_generation.health_monitor import ProviderHealthCycle

    local = StubCloudProvider("local_piper", cloud_first=False)
    cycle = ProviderHealthCycle(
        registry=FakeRegistry([local]),
        health_path=str(tmp_path / "h.json"),
    )
    report = asyncio.run(cycle.run_cycle())
    assert report["checked_providers"] == []
    assert local.is_available is True


def test_mcp_health_cycle_tool(fake_http, tmp_path):
    from ai_generation.health_monitor import ProviderHealthCycle
    from ai_generation.mcp_tools import MCP_GENERATION_TOOLS, MCPGenerationTools

    assert "run_provider_health_cycle" in MCP_GENERATION_TOOLS
    good = StubCloudProvider("good")
    registry = FakeRegistry([good])
    cycle = ProviderHealthCycle(
        registry=registry, health_path=str(tmp_path / "h.json"))
    asyncio.run(cycle.run_cycle())

    # SDK-level: use the cycle directly; MCP handler delegates to the SDK
    tools = MCPGenerationTools()
    # The SDK uses the real registry; exercise the handler with a healthy fake
    # http so the cycle completes without network.
    result = asyncio.run(tools.handle("run_provider_health_cycle", {}))
    assert isinstance(result, dict)
    assert "checked_at" in result
