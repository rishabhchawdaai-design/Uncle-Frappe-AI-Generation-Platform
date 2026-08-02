"""
Tests for capability graph synchronization with the live registries
(Capability Graph Specification — graph must evolve automatically).

Covers the default graph covering all new providers/capabilities, registry
synchronization, pathfinding for new capabilities, and SDK/CLI/MCP surfaces.
"""
import asyncio
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))


@pytest.fixture
def synced_graph(tmp_path):
    from ai_generation.capability_graph import CapabilityGraph
    from ai_generation.providers.registry import get_registry
    from ai_generation.storage import StorageRegistry

    graph = CapabilityGraph()
    graph.synchronize_from_registries(
        provider_registry=get_registry(),
        storage_registry=StorageRegistry({
            "sqlite": {"db_path": str(tmp_path / "g.db")},
            "json": {"root": str(tmp_path / "gj")},
        }),
        event_log=True,
    )
    return graph


# ── Default graph coverage ───────────────────────────────────────────────

def test_default_graph_has_local_backends():
    from ai_generation.capability_graph import CapabilityGraph

    graph = CapabilityGraph()
    for nid in ("pollinations_text", "sentence_transformers", "piper_local",
                "faster_whisper", "helsinki_opus_mt", "realesrgan", "rembg",
                "tesseract", "sqlite_local", "json_files", "event_log"):
        assert graph.get_node(nid) is not None, f"missing default node {nid}"
    for cid in ("text_embedding", "translation", "upscale",
                "background_removal", "text_extraction", "storage",
                "event_sourcing"):
        assert graph.get_node(cid) is not None, f"missing default capability {cid}"


def test_default_graph_edges():
    from ai_generation.capability_graph import CapabilityGraph

    graph = CapabilityGraph()
    for provider, capability in (
        ("sentence_transformers", "text_embedding"),
        ("helsinki_opus_mt", "translation"),
        ("piper_local", "text_to_speech"),
        ("faster_whisper", "speech_to_text"),
        ("realesrgan", "upscale"),
        ("rembg", "background_removal"),
        ("tesseract", "text_extraction"),
        ("sqlite_local", "storage"),
        ("event_log", "event_sourcing"),
    ):
        neighbors = graph.get_neighbors(provider)
        assert any(n["node_id"] == capability for n in neighbors), \
            f"{provider} should support {capability}"


# ── Registry synchronization ─────────────────────────────────────────────

def test_sync_adds_providers(synced_graph):
    stats = synced_graph.get_stats()
    assert stats["node_count"] >= 50
    assert stats["node_types"].get("provider", 0) >= 30
    assert stats["node_types"].get("capability", 0) >= 14


def test_sync_is_idempotent(synced_graph):
    report1 = synced_graph.synchronize_from_registries(
        provider_registry=None, storage_registry=None, event_log=None)
    # no new nodes when already synced
    assert report1["new_nodes"] == 0
    assert report1["new_edges"] == 0


def test_sync_reports(synced_graph):
    history = synced_graph.get_update_history()
    assert any("synchronize_from_registries" in h["action"] for h in history)


# ── Pathfinding for new capabilities ─────────────────────────────────────

def test_chat_path_prefers_free(synced_graph):
    paths = synced_graph.find_capability_path("chat")
    assert paths, "chat path not found"
    first = paths[0]
    assert first.nodes[0] == "pollinations_text"


def test_embedding_path(synced_graph):
    paths = synced_graph.find_capability_path("text_embedding")
    assert paths, "text_embedding path not found"
    assert paths[0].nodes[0] == "sentence_transformers"


def test_translation_path(synced_graph):
    paths = synced_graph.find_capability_path("translation")
    assert paths, "translation path not found"
    assert paths[0].nodes[0] == "helsinki_opus_mt"


def test_upscale_and_bg_removal_paths(synced_graph):
    up = synced_graph.find_capability_path("upscale")
    bg = synced_graph.find_capability_path("background_removal")
    assert up and up[0].nodes[0] == "realesrgan"
    assert bg and bg[0].nodes[0] == "rembg"


def test_storage_and_event_paths(synced_graph):
    storage_paths = synced_graph.find_capability_path("storage")
    event_paths = synced_graph.find_capability_path("event_sourcing")
    assert storage_paths and storage_paths[0].nodes[0] == "sqlite_local"
    assert event_paths and event_paths[0].nodes[0] == "event_log"


# ── SDK integration ──────────────────────────────────────────────────────

def test_sdk_sync_capability_graph(tmp_path):
    from ai_generation import UncleFrappeAI

    ai = UncleFrappeAI(config={
        "storage": {"sqlite": {"db_path": str(tmp_path / "sdk_g.db")},
                    "json": {"root": str(tmp_path / "sdk_gj")}},
        "event_log": {"db_path": str(tmp_path / "sdk_ev.db")},
    })
    report = ai.sync_capability_graph()
    assert report["total_nodes"] >= 50
    stats = ai.get_capability_graph_stats()
    assert stats["node_count"] >= 50


# ── CLI integration ──────────────────────────────────────────────────────

def test_cli_graph_sync(capsys):
    import ai_generation.cli as cli

    result = asyncio.run(cli.cmd_graph_sync())
    out = capsys.readouterr().out
    assert result["total_nodes"] >= 50
    assert "Total nodes" in out


# ── MCP integration ──────────────────────────────────────────────────────

def test_mcp_sync_tool_registered():
    from ai_generation.mcp_tools import MCP_GENERATION_TOOLS, MCPGenerationTools

    assert "sync_capability_graph" in MCP_GENERATION_TOOLS
    handler = MCPGenerationTools()
    assert hasattr(handler, "_handle_sync_capability_graph")


def test_mcp_sync_dispatch():
    from ai_generation.mcp_tools import MCPGenerationTools

    handler = MCPGenerationTools()
    result = asyncio.run(handler.handle("sync_capability_graph", {}))
    assert result["total_nodes"] >= 50
