"""
Tests for the Research Integration Layer (FINAL CANONICAL CONSOLIDATION).

Covers discovery, capability mapping, index building, traceability, impact
analysis, change detection, sync/queue, cache-only fallback, the
implementation graph, SDK integration, MCP tools, and CLI commands.
"""
import asyncio
import json
import shutil

import pytest

from ai_generation.research_integration import ResearchIntegrationEngine
from ai_generation.research_integration import DATA_DIR, ResearchIntegrationEngine


RESEARCH_DOC_COUNT = 57
CAPABILITY_COUNT = 251


# ── Discovery & capability mapping ───────────────────────────────

def test_discovery_scans_live_research_repo():
    engine = ResearchIntegrationEngine()
    docs = engine.discover_documents()
    assert len(docs) == RESEARCH_DOC_COUNT
    assert all(len(d.sha256) == 64 for d in docs)
    assert all(d.research_id for d in docs)
    categories = {d.category for d in docs}
    assert "core_spec" in categories
    assert "research_area" in categories
    for doc in docs:
        assert doc.source_url.startswith("https://github.com/")


def test_every_capability_maps_to_exactly_one_research_document():
    engine = ResearchIntegrationEngine()
    docs = engine.discover_documents()
    registry = engine._load_registry()
    assert len(registry) == CAPABILITY_COUNT
    mapped = [cap for doc in docs for cap in doc.related_capabilities]
    assert len(mapped) == CAPABILITY_COUNT
    assert len(set(mapped)) == CAPABILITY_COUNT
    assert set(mapped) == {row["capability_id"] for row in registry}


def _engine_with_manifest(tmp_path):
    """Engine over a temp data dir seeded with the committed manifest cache.

    Mirrors CI, where the live research repo may be absent and discovery
    must fall back to the generated manifest cache.
    """
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    shutil.copy(DATA_DIR / "research_manifest.json", data_dir / "research_manifest.json")
    return ResearchIntegrationEngine(data_dir=str(data_dir))


# ── Index & traceability ─────────────────────────────────────────

def test_build_index_and_trace(tmp_path):
    engine = _engine_with_manifest(tmp_path)
    index = engine.build_index()
    assert index["research_documents"] == RESEARCH_DOC_COUNT
    assert index["capabilities"] == CAPABILITY_COUNT
    assert len(index["modules"]) >= 50
    assert (tmp_path / "data" / "research_index.json").exists()

    trace = engine.trace_capability("SEC-05")
    assert trace is not None
    assert trace.capability_id == "SEC-05"
    assert trace.research_documents[0]["research_id"] == "SECURITY_CANON"
    assert "security_crypto" in trace.modules
    assert "test_security_crypto" in trace.tests
    assert isinstance(trace.sdk_interfaces, list)
    assert isinstance(trace.mcp_tools, list)
    assert trace.vault_page.startswith("knowledge-vault/")
    assert trace.registry_entry.startswith("CAPABILITY_REGISTRY.md#")
    assert trace.introduced_commit

    assert engine.trace_capability("ZZZ-99") is None


def test_research_impact(tmp_path):
    engine = _engine_with_manifest(tmp_path)
    impact = engine.research_impact("SECURITY_CANON")
    assert impact is not None
    assert len(impact.affected_capabilities) >= 10
    assert "security_crypto" in impact.affected_modules
    assert "test_security_crypto" in impact.affected_tests
    assert impact.affected_docs
    assert impact.recommendations

    assert engine.research_impact("NOT_A_REAL_DOC_123") is None


# ── Change detection & sync ──────────────────────────────────────

def test_change_detection_and_sync_queue(tmp_path):
    repo = tmp_path / "repo"
    (repo / "research").mkdir(parents=True)
    (repo / "research" / "alpha.md").write_text("# Alpha\n\nImplementable research.\n")
    engine = ResearchIntegrationEngine(
        research_repo=str(repo), data_dir=str(tmp_path / "data")
    )

    report = engine.sync()
    assert report["documents_indexed"] == 1
    assert any(c["type"] == "new" for c in report["changes"])
    assert len(report["queue_added"]) == 1
    items = engine.execution_queue()
    assert any(i["source_research"] == "ALPHA" for i in items)

    # Modifying content is detected as a change but does not re-queue.
    (repo / "research" / "alpha.md").write_text("# Alpha\n\nUpdated content.\n")
    changes = engine.detect_changes()
    assert any(c["type"] == "modified" and c["research_id"] == "ALPHA" for c in changes)
    assert len(engine.execution_queue()) == 1

    # New research requiring credentials is classified as blocked.
    (repo / "research" / "beta.md").write_text("# Beta\n\nThis requires api key credentials.\n")
    report2 = engine.sync()
    assert any(c["type"] == "new" and c["research_id"] == "BETA" for c in report2["changes"])
    blocked = [i for i in engine.execution_queue() if i["source_research"] == "BETA"]
    assert blocked and blocked[0]["classification"] == "blocked"

    # Re-running sync is idempotent (no duplicate queue items).
    engine.sync()
    items = engine.execution_queue()
    assert len(items) == 2
    assert len({i["item_id"] for i in items}) == 2


def test_cache_only_mode_when_research_repo_missing(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    documents = [{
        "research_id": "ALPHA",
        "title": "Alpha Research",
        "path": "research/alpha.md",
        "category": "index",
        "sha256": "a" * 64,
        "status": "active",
        "source_url": "",
        "commit": "",
        "related_capabilities": [],
    }]
    (data_dir / "research_manifest.json").write_text(
        json.dumps({"documents": documents})
    )
    engine = ResearchIntegrationEngine(
        research_repo=str(tmp_path / "missing"), data_dir=str(data_dir)
    )
    discovered = engine.discover_documents()
    assert len(discovered) == 1
    assert discovered[0].research_id == "ALPHA"
    stats = engine.get_stats()
    assert stats["live_research_repo"] is False
    assert stats["research_documents"] == 1


# ── Implementation graph ─────────────────────────────────────────

def test_implementation_graph_and_neighbors(tmp_path):
    engine = _engine_with_manifest(tmp_path)
    graph = engine.implementation_graph()
    assert graph["node_count"] > 100
    assert graph["edge_count"] > 100
    node_ids = {node["id"] for node in graph["nodes"]}
    assert "research:SECURITY_CANON" in node_ids
    assert "capability:SEC-05" in node_ids
    assert "module:security_crypto" in node_ids
    neighbors = engine.neighbors("research:SECURITY_CANON")
    assert "capability:SEC-01" in neighbors
    assert "capability:SEC-05" in neighbors


# ── Unified SDK integration ──────────────────────────────────────

def test_sdk_research_integration():
    from ai_generation.sdk import UncleFrappeAI

    ai = UncleFrappeAI({"acos_research_repo": None})
    stats = ai.get_stats()["research_integration"]
    assert stats["research_documents"] == RESEARCH_DOC_COUNT
    assert stats["capabilities"] == CAPABILITY_COUNT
    assert isinstance(stats["live_research_repo"], bool)

    trace = ai.trace_capability("SEC-05")
    assert trace is not None
    assert trace.research_documents
    impact = ai.research_impact("SECURITY_CANON")
    assert impact is not None
    assert impact.affected_capabilities
    sync_status = ai.research_sync_status()
    assert "changes" in sync_status
    assert "stats" in sync_status
    graph = ai.research_graph()
    assert graph["node_count"] > 100


# ── MCP tools ────────────────────────────────────────────────────

def test_mcp_research_tools_registered():
    from ai_generation.mcp_tools import MCP_GENERATION_TOOLS

    for tool in (
        "research_index",
        "trace_capability",
        "research_impact_analysis",
        "research_sync_status",
        "research_graph",
    ):
        assert tool in MCP_GENERATION_TOOLS


@pytest.mark.asyncio
async def test_mcp_research_handlers():
    from ai_generation.mcp_tools import MCPGenerationTools

    mcp = MCPGenerationTools()
    index = await mcp.handle("research_index", {})
    assert index["research_documents"] == RESEARCH_DOC_COUNT

    trace = await mcp.handle("trace_capability", {"capability_id": "SEC-05"})
    assert isinstance(trace, dict)
    assert trace["research_documents"][0]["research_id"] == "SECURITY_CANON"

    impact = await mcp.handle("research_impact_analysis", {"research_id": "SECURITY_CANON"})
    assert isinstance(impact, dict)
    assert impact["affected_capabilities"]

    sync = await mcp.handle("research_sync_status", {})
    assert isinstance(sync, dict)
    assert "changes" in sync
    assert "stats" in sync

    graph = await mcp.handle("research_graph", {})
    assert isinstance(graph, dict)
    assert graph["node_count"] > 100


# ── CLI commands ─────────────────────────────────────────────────

def test_cli_research_commands(capsys):
    from ai_generation.cli import (
        cmd_research_graph,
        cmd_research_impact,
        cmd_research_index,
        cmd_research_sync,
        cmd_research_trace,
    )

    asyncio.run(cmd_research_index())
    out = capsys.readouterr().out
    assert "Research Documents: 57" in out
    assert "251" in out

    asyncio.run(cmd_research_trace("SEC-05"))
    out = capsys.readouterr().out
    assert "Traceability: SEC-05" in out
    assert "SECURITY_CANON" in out

    asyncio.run(cmd_research_impact("SECURITY_CANON"))
    out = capsys.readouterr().out
    assert "Impact Analysis: SECURITY_CANON" in out

    asyncio.run(cmd_research_sync())
    out = capsys.readouterr().out
    assert "Research Sync" in out
    assert "Documents Indexed: 57" in out

    asyncio.run(cmd_research_graph())
    out = capsys.readouterr().out
    assert "Nodes:" in out
    assert "capability" in out
