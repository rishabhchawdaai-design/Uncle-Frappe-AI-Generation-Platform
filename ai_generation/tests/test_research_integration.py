"""
Tests for the Research Integration Layer (FINAL CANONICAL CONSOLIDATION).

Covers discovery, capability mapping, index building, traceability, impact
analysis, change detection, sync/queue, cache-only fallback, the
implementation graph, SDK integration, MCP tools, and CLI commands.
"""
import asyncio
import json
import shutil
import os

import pytest

from ai_generation.research_integration import ResearchIntegrationEngine
from pathlib import Path

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
    assert len({d.research_id for d in docs}) == len(docs)
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


def test_research_impact_for_cross_referenced_documents(tmp_path):
    engine = _engine_with_manifest(tmp_path)
    index = engine.build_index()
    satisfaction = index["document_satisfaction"]
    assert "CHAPTER_10_GLOBAL_BENCHMARK_INTELLIGENCE" in satisfaction
    assert "BMK-01" in satisfaction["CHAPTER_10_GLOBAL_BENCHMARK_INTELLIGENCE"]["capabilities"]
    assert "COMPATIBILITY_MATRIX" in satisfaction
    assert "CGR-03" in satisfaction["COMPATIBILITY_MATRIX"]["capabilities"]
    assert "RUN-01" in satisfaction["COMPATIBILITY_MATRIX"]["capabilities"]

    impact = engine.research_impact("CHAPTER_10_GLOBAL_BENCHMARK_INTELLIGENCE")
    assert impact is not None
    assert "BMK-01" in impact.affected_capabilities
    assert "BMK-02" in impact.affected_capabilities
    assert impact.affected_modules
    assert impact.affected_tests

    threat = engine.research_impact("SECURITY_THREAT_MODEL")
    assert threat is not None
    assert "SEC-03" in threat.affected_capabilities
    assert "security" in threat.affected_modules

    scheduler = engine.research_impact("SCHEDULING_POLICY_SPECIFICATION")
    assert scheduler is not None
    assert scheduler.affected_capabilities

    plugin_os = engine.research_impact("CHAPTER_08_PLUGIN_OPERATING_SYSTEM")
    assert plugin_os is not None
    assert "PLG-01" in plugin_os.affected_capabilities
    assert "PLG-10" in plugin_os.affected_capabilities
    assert "SEC-01" in plugin_os.affected_capabilities

    compute_graph = engine.research_impact("CHAPTER_01_UNIVERSAL_COMPUTE_GRAPH")
    assert compute_graph is not None
    assert "CGR-01" in compute_graph.affected_capabilities
    assert "WFL-01" in compute_graph.affected_capabilities

    model_registry = engine.research_impact("MODEL_CAPABILITY_REGISTRY")
    assert model_registry is not None
    assert "CGR-03" in model_registry.affected_capabilities

    workflow_registry = engine.research_impact("WORKFLOW_CAPABILITY_REGISTRY")
    assert workflow_registry is not None
    assert "WFL-01" in workflow_registry.affected_capabilities


def test_sync_classifies_satisfied_research(tmp_path):
    repo = tmp_path / "repo"
    (repo / "docs" / "supporting").mkdir(parents=True)
    (repo / "docs" / "supporting" / "SECURITY_THREAT_MODEL.md").write_text(
        "# ACOS Security Threat Model\n\nNew threat categories added.\n"
    )
    engine = ResearchIntegrationEngine(
        research_repo=str(repo), data_dir=str(tmp_path / "data")
    )
    engine.sync()
    items = engine.execution_queue()
    item = next(i for i in items if i["source_research"] == "SECURITY_THREAT_MODEL")
    assert item["classification"] == "satisfied"
    assert "verified capabilities" in item["reason"]


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
    (repo / "research" / "core_specs").mkdir(parents=True)
    (repo / "research" / "core_specs" / "alpha.md").write_text("# Alpha\n\nImplementable research.\n")
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
    (repo / "research" / "core_specs" / "alpha.md").write_text("# Alpha\n\nUpdated content.\n")
    changes = engine.detect_changes()
    assert any(c["type"] == "modified" and c["research_id"] == "ALPHA" for c in changes)
    assert len(engine.execution_queue()) == 1

    # New research requiring credentials is classified as blocked.
    (repo / "research" / "core_specs" / "beta.md").write_text("# Beta\n\nThis requires api key credentials.\n")
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
    assert "mapped_documents" in stats


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
    threat_neighbors = engine.neighbors("research:SECURITY_THREAT_MODEL")
    assert "capability:SEC-03" in threat_neighbors


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


# ── Sync automation script ─────────────────────────────────────────

def test_research_sync_script_present_and_executable():
    script = Path(__file__).resolve().parents[2] / "scripts" / "research-sync.sh"
    assert script.exists()
    assert os.access(script, os.X_OK)


def test_research_sync_script_check_mode():
    import subprocess
    repo_root = Path(__file__).resolve().parents[2]
    result = subprocess.run(
        ["scripts/research-sync.sh", "--check"],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "synchronized" in result.stdout


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
