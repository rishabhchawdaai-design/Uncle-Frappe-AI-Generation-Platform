"""
Tests for the Pollinations anonymous text provider and its integration
through the unified SDK, Generation Manager failover, CLI, and MCP surface.

All tests are offline: the Pollinations HTTP client is replaced with a
fake transport so the suite never depends on the live network.
"""
import asyncio
import os
import sys
import time
from types import SimpleNamespace

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from ai_generation.providers.base import GenerationResult  # noqa: E402
from ai_generation.providers.registry import get_registry  # noqa: E402


class FakeResponse:
    def __init__(self, status_code, text="", content=b"", headers=None):
        self.status_code = status_code
        self._text = text
        self.content = content
        self.headers = headers or {"content-type": "text/plain"}

    @property
    def text(self):
        return self._text


class FakeAsyncClient:
    """Drop-in httpx.AsyncClient replacement for offline tests."""

    def __init__(self, response=None, responses=None, exc=None,
                 timeout=60, follow_redirects=False):
        self.response = response or FakeResponse(200, "Hello from Pollinations")
        self.responses = responses  # optional sequence consumed per request
        self.exc = exc
        self.last_url = None
        self.last_params = None
        self.calls = 0

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def get(self, url, params=None, **kwargs):
        self.calls += 1
        self.last_url = url
        self.last_params = params
        if self.exc is not None:
            raise self.exc
        if self.responses:
            return self.responses[min(self.calls, len(self.responses)) - 1]
        return self.response


@pytest.fixture
def fake_httpx(monkeypatch):
    holder = {"client": None}

    def _install(response=None, responses=None, exc=None):
        client = FakeAsyncClient(response=response, responses=responses, exc=exc)
        holder["client"] = client
        monkeypatch.setattr(
            "ai_generation.providers.pollinations_text_provider.httpx.AsyncClient",
            lambda *a, **k: client,
        )
        return client

    return _install


def test_provider_auto_registered():
    reg = get_registry()
    provider = reg.get("pollinations_text")
    assert provider is not None
    assert provider.tier.value == "free"
    assert provider.requires_api_key is False
    stats = provider.get_stats()
    assert stats["has_api_key"] is False
    assert "chat" in stats["capabilities"]


def test_generate_text_success(fake_httpx):
    from ai_generation.providers.pollinations_text_provider import PollinationsTextProvider

    fake_httpx(response=FakeResponse(200, "The capital of France is Paris."))
    provider = PollinationsTextProvider()
    result = asyncio.run(provider.generate_text("What is the capital of France?"))
    assert result.success
    assert result.metadata["text"] == "The capital of France is Paris."
    assert result.cost_estimate == 0.0
    assert provider.success_rate == 100.0


def test_generate_text_passes_model_params(fake_httpx):
    from ai_generation.providers.pollinations_text_provider import PollinationsTextProvider

    client = fake_httpx(response=FakeResponse(200, "ok"))
    provider = PollinationsTextProvider()
    asyncio.run(provider.generate_text("hello", model="mistral", system_prompt="Be terse", seed=42, temperature=0.5))
    assert "https://text.pollinations.ai/hello" in client.last_url
    assert client.last_params["model"] == "mistral"
    assert client.last_params["seed"] == "42"
    assert client.last_params["temperature"] == "0.5"
    assert client.last_params["system"] == "Be terse"


def test_generate_text_deprecation_error(fake_httpx):
    from ai_generation.providers.pollinations_text_provider import PollinationsTextProvider

    fake_httpx(response=FakeResponse(402, '{"error":"402 Payment Required"}'))
    provider = PollinationsTextProvider()
    result = asyncio.run(provider.generate_text("hello", retries=0))
    assert result.status == "error"
    assert "402" in (result.error or "")
    assert provider.success_rate == 0.0


def test_generate_text_retries_then_succeeds(fake_httpx):
    from ai_generation.providers.pollinations_text_provider import PollinationsTextProvider

    client = fake_httpx(responses=[
        FakeResponse(402, '{"error":"402 Payment Required"}'),
        FakeResponse(200, "recovered after backoff"),
    ])
    provider = PollinationsTextProvider()
    result = asyncio.run(provider.generate_text("hello", retries=1))
    assert client.calls == 2
    assert result.success
    assert result.metadata["text"] == "recovered after backoff"


def test_generate_text_timeout(fake_httpx):
    import httpx

    from ai_generation.providers.pollinations_text_provider import PollinationsTextProvider

    fake_httpx(exc=httpx.TimeoutException("timed out"))
    provider = PollinationsTextProvider()
    result = asyncio.run(provider.generate_text("hello", retries=0))
    assert result.status == "timeout"
    assert "timed out" in (result.error or "")


def test_sdk_generate_text_success(fake_httpx):
    from ai_generation import UncleFrappeAI

    fake_httpx(response=FakeResponse(200, "A short answer."))
    ai = UncleFrappeAI()
    result = asyncio.run(ai.generate_text("Explain MoE in one sentence."))
    assert result.success
    assert result.provider == "pollinations_text"
    assert result.metadata["text"] == "A short answer."


def test_sdk_generate_text_failover_skips_key_providers(fake_httpx):
    """Without API keys, key-based text providers are skipped; the keyless
    Pollinations provider must be reached and succeed."""
    from ai_generation import UncleFrappeAI

    fake_httpx(response=FakeResponse(200, "fallback success"))
    ai = UncleFrappeAI()
    result = asyncio.run(ai.generate_text("hello"))
    assert result.success
    assert result.provider == "pollinations_text"


def test_generation_manager_plan_orders_text_providers():
    from ai_generation.generation_manager import GenerationManager, GenerationRequest
    from ai_generation.providers.base import ProviderType

    mgr = GenerationManager()
    plan = mgr.plan_generation(GenerationRequest(prompt="hi", provider_type=ProviderType.TEXT))
    assert "pollinations_text" in plan.provider_order
    assert "kimi_k3" in plan.provider_order
    # keyless provider should come before key-gated providers
    assert plan.provider_order.index("pollinations_text") < plan.provider_order.index("kimi_k3")


def test_mcp_generate_text_tool(fake_httpx):
    from ai_generation.mcp_tools import MCP_GENERATION_TOOLS, MCPGenerationTools

    assert "generate_text" in MCP_GENERATION_TOOLS
    schema = MCP_GENERATION_TOOLS["generate_text"]["inputSchema"]
    assert "prompt" in schema["properties"]

    fake_httpx(response=FakeResponse(200, "MCP answer"))
    tools = MCPGenerationTools()
    result = asyncio.run(tools.handle("generate_text", {"prompt": "hello"}))
    assert result["status"] == "success"
    assert result["provider"] == "pollinations_text"


def test_cli_text_command(fake_httpx, capsys):
    import ai_generation.cli as cli
    from ai_generation.sdk import UncleFrappeAI

    fake_httpx(response=FakeResponse(200, "CLI answer"))
    real_ai = UncleFrappeAI()
    result = asyncio.run(cli.cmd_text("hello"))
    out = capsys.readouterr().out
    assert result.success
    assert result.provider == "pollinations_text"
    assert "CLI answer" in out
