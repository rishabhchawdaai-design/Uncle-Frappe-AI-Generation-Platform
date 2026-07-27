"""Tests for PLG-08/09/10 — Plugin Marketplace, Hot-Reloading, Signing."""
import pytest
import os
import tempfile


def test_marketplace_source_enum():
    from ai_generation.plugin_extensions import MarketplaceSource
    assert MarketplaceSource.LOCAL.value == "local"
    assert MarketplaceSource.GITHUB.value == "github"
    assert MarketplaceSource.PYPI.value == "pypi"


def test_plugin_sign_status_enum():
    from ai_generation.plugin_extensions import PluginSignStatus
    assert PluginSignStatus.UNSIGNED.value == "unsigned"
    assert PluginSignStatus.VERIFIED.value == "verified"
    assert PluginSignStatus.INVALID.value == "invalid"
    assert PluginSignStatus.REVOKED.value == "revoked"


def test_marketplace_entry_serialization():
    from ai_generation.plugin_extensions import MarketplaceEntry, MarketplaceSource
    e = MarketplaceEntry(
        plugin_id="test-plugin", name="Test Plugin", description="A test",
        version="1.0.0", author="test", source=MarketplaceSource.LOCAL,
        source_url="", license="MIT", tags=["test"],
    )
    d = e.to_dict()
    assert d["plugin_id"] == "test-plugin"
    assert d["source"] == "local"


def test_plugin_signature_serialization():
    from ai_generation.plugin_extensions import PluginSignature, PluginSignStatus
    s = PluginSignature(plugin_id="p1", version="1.0", status=PluginSignStatus.VERIFIED)
    d = s.to_dict()
    assert d["plugin_id"] == "p1"
    assert d["status"] == "verified"


def test_plugin_marketplace_import():
    from ai_generation.plugin_extensions import PluginMarketplace
    m = PluginMarketplace()
    assert m is not None


def test_plugin_marketplace_search():
    from ai_generation.plugin_extensions import PluginMarketplace, MarketplaceEntry, MarketplaceSource
    m = PluginMarketplace()
    m.register_entry(MarketplaceEntry(
        plugin_id="test1", name="Test Plugin 1", description="A test plugin",
        version="1.0.0", author="test", source=MarketplaceSource.LOCAL,
        source_url="", license="MIT", tags=["test"],
    ))
    results = m.search(query="test")
    assert len(results) == 1
    assert results[0]["plugin_id"] == "test1"


def test_plugin_marketplace_stats():
    from ai_generation.plugin_extensions import PluginMarketplace
    m = PluginMarketplace()
    stats = m.get_stats()
    assert stats["total_entries"] == 0


def test_plugin_hot_reloader_import():
    from ai_generation.plugin_extensions import PluginHotReloader
    r = PluginHotReloader()
    assert r is not None


def test_plugin_hot_reloader_watch():
    from ai_generation.plugin_extensions import PluginHotReloader
    r = PluginHotReloader()
    r.watch("test-plugin", "/tmp/test_plugin.py")
    assert "test-plugin" in r.get_watched()


def test_plugin_hot_reloader_stats():
    from ai_generation.plugin_extensions import PluginHotReloader
    r = PluginHotReloader()
    stats = r.get_stats()
    assert stats["watched"] == 0


def test_plugin_signer_import():
    from ai_generation.plugin_extensions import PluginSigner
    s = PluginSigner()
    assert s is not None


def test_plugin_signer_sign_and_verify():
    from ai_generation.plugin_extensions import PluginSigner, PluginSignStatus
    s = PluginSigner()
    sig = s.sign_plugin("test-plugin", "1.0.0", "print('hello')", key_id="test-key")
    assert sig.status == PluginSignStatus.VERIFIED
    result = s.verify_plugin("test-plugin", "1.0.0", "print('hello')")
    assert result.status == PluginSignStatus.VERIFIED


def test_plugin_signer_verify_tampered():
    from ai_generation.plugin_extensions import PluginSigner, PluginSignStatus
    s = PluginSigner()
    s.sign_plugin("test-plugin", "1.0.0", "original code", key_id="test-key")
    result = s.verify_plugin("test-plugin", "1.0.0", "tampered code")
    assert result.status == PluginSignStatus.INVALID


def test_plugin_signer_stats():
    from ai_generation.plugin_extensions import PluginSigner
    s = PluginSigner()
    stats = s.get_stats()
    assert stats["total_signatures"] == 0


# ── SDK Integration ──

def test_sdk_plugin_extensions_import():
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    assert ai.plugin_marketplace is not None
    assert ai.plugin_hot_reloader is not None
    assert ai.plugin_signer is not None


def test_sdk_plugin_extensions_in_stats():
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    stats = ai.get_stats()
    assert "plugin_marketplace" in stats
    assert "plugin_hot_reloader" in stats
    assert "plugin_signer" in stats


# ── MCP Tools ──

def test_mcp_plugin_extension_tools_exist():
    from ai_generation.mcp_tools import MCP_GENERATION_TOOLS
    assert "search_plugin_marketplace" in MCP_GENERATION_TOOLS
    assert "list_plugin_marketplace" in MCP_GENERATION_TOOLS
    assert "watch_plugin" in MCP_GENERATION_TOOLS
    assert "check_plugin_changes" in MCP_GENERATION_TOOLS
    assert "reload_plugin" in MCP_GENERATION_TOOLS
    assert "sign_plugin" in MCP_GENERATION_TOOLS
    assert "verify_plugin_signature" in MCP_GENERATION_TOOLS
    assert "get_plugin_signatures" in MCP_GENERATION_TOOLS


@pytest.mark.asyncio
async def test_mcp_sign_plugin():
    from ai_generation.mcp_tools import MCPGenerationTools
    mcp = MCPGenerationTools()
    result = await mcp.handle("sign_plugin", {"plugin_id": "test", "version": "1.0", "code": "hello"})
    assert result["status"] == "verified"


@pytest.mark.asyncio
async def test_mcp_verify_plugin():
    from ai_generation.mcp_tools import MCPGenerationTools
    mcp = MCPGenerationTools()
    # Sign first so it exists in this signer instance
    await mcp.handle("sign_plugin", {"plugin_id": "vtest", "version": "1.0", "code": "hello"})
    result = await mcp.handle("verify_plugin_signature", {"plugin_id": "vtest", "version": "1.0", "code": "hello"})
    assert result["status"] == "verified"
