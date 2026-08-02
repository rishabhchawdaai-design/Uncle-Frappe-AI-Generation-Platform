"""
Tests for the Storage & Databases layer (ACOS Storage Architecture).

Covers the local SQLite and JSON backends (stdlib, offline) and the
truthful not_configured status of external profiles (PostgreSQL, Qdrant,
LanceDB, MinIO, Neo4j, Prometheus, Redis), plus SDK/CLI/MCP integration.
"""
import asyncio
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))


@pytest.fixture
def isolated_registry(tmp_path):
    from ai_generation.storage import StorageRegistry

    reg = StorageRegistry({
        "sqlite": {"db_path": str(tmp_path / "test.db")},
        "json": {"root": str(tmp_path / "json")},
    })
    return reg


@pytest.fixture
def isolated_sdk(tmp_path):
    from ai_generation import UncleFrappeAI

    return UncleFrappeAI(config={
        "storage": {"sqlite": {"db_path": str(tmp_path / "sdk.db")},
                    "json": {"root": str(tmp_path / "sdk_json")}},
    })


# ── Registry ─────────────────────────────────────────────────────────────

def test_registry_loads_local_and_external(isolated_registry):
    backends = {b["name"]: b for b in isolated_registry.list_backends()}
    assert backends["sqlite_local"]["status"] == "available"
    assert backends["json_files"]["status"] == "available"
    for name in ("postgresql", "qdrant", "lancedb", "minio", "neo4j",
                 "prometheus", "redis"):
        assert backends[name]["status"] == "not_configured"
        assert backends[name]["available"] is False


def test_select_backend_by_task(isolated_registry):
    assert isolated_registry.select_backend("metadata").name == "sqlite_local"
    assert isolated_registry.select_backend("ledger").name == "sqlite_local"
    assert isolated_registry.select_backend("embeddings").name == "sqlite_local"
    assert isolated_registry.select_backend("unknown").name == "sqlite_local"


def test_negotiation_candidates(isolated_registry):
    candidates = isolated_registry.to_negotiation_candidates()
    assert len(candidates) == 2
    assert {c["provider"] for c in candidates} == {
        "storage_sqlite_local", "storage_json_files"}
    assert all(c["layer"] == "storage" for c in candidates)
    assert all(c["cost_usd"] == 0.0 for c in candidates)


# ── SQLite backend ───────────────────────────────────────────────────────

def test_sqlite_roundtrip(isolated_registry):
    backend = isolated_registry.get_backend("sqlite_local")
    rec = backend.write("ledger", "dec-1", {"action": "route"},
                        metadata={"tier": "free"})
    assert rec.key == "dec-1"
    assert rec.metadata == {"tier": "free"}

    read = backend.read("ledger", "dec-1")
    assert read is not None
    assert read.value == {"action": "route"}
    assert read.metadata == {"tier": "free"}

    rows = backend.query("ledger")
    assert len(rows) == 1

    # overwrite updates in place
    backend.write("ledger", "dec-1", {"action": "fallback"})
    assert backend.read("ledger", "dec-1").value == {"action": "fallback"}
    assert backend.stats()["records"] == 1

    assert backend.delete("ledger", "dec-1") is True
    assert backend.read("ledger", "dec-1") is None


def test_sqlite_health_check(isolated_registry):
    backend = isolated_registry.get_backend("sqlite_local")
    health = backend.health_check()
    assert health["backend"] == "sqlite_local"
    assert health["status"] == "available"
    assert health["available"] is True


# ── JSON backend ─────────────────────────────────────────────────────────

def test_json_roundtrip(isolated_registry):
    backend = isolated_registry.get_backend("json_files")
    backend.write("benchmarks", "bm-1", {"score": 0.9})
    read = backend.read("benchmarks", "bm-1")
    assert read.value == {"score": 0.9}
    rows = backend.query("benchmarks")
    assert len(rows) == 1
    assert backend.stats()["records"] == 1
    assert backend.delete("benchmarks", "bm-1") is True
    assert backend.read("benchmarks", "bm-1") is None


# ── SDK integration ──────────────────────────────────────────────────────

def test_sdk_list_storage_backends(isolated_sdk):
    backends = isolated_sdk.list_storage_backends()
    names = {b["name"] for b in backends}
    assert "sqlite_local" in names
    assert "json_files" in names
    assert "postgresql" in names
    assert "qdrant" in names


def test_sdk_storage_write_read_query_delete(isolated_sdk):
    result = isolated_sdk.storage_write(
        "ledger", "dec-42", {"provider": "pollinations"}, task="ledger")
    assert result["key"] == "dec-42"
    assert result["collection"] == "ledger"

    read = isolated_sdk.storage_read("ledger", "dec-42", task="ledger")
    assert read["value"]["provider"] == "pollinations"

    rows = isolated_sdk.storage_query("ledger", task="ledger")
    assert len(rows) == 1
    assert rows[0]["key"] == "dec-42"

    assert isolated_sdk.storage_delete("ledger", "dec-42", task="ledger") is True
    assert isolated_sdk.storage_read("ledger", "dec-42", task="ledger") == {}


def test_sdk_select_storage_backend(isolated_sdk):
    selected = isolated_sdk.select_storage_backend("metadata")
    assert selected["name"] == "sqlite_local"
    assert selected["status"] == "available"


def test_sdk_get_storage_stats(isolated_sdk):
    stats = isolated_sdk.get_storage_stats()
    assert stats["backends_total"] >= 9
    assert stats["backends_local"] == 3
    assert stats["backends_configured"] >= 2
    assert "sqlite_local" in stats["live"]


# ── CLI integration ──────────────────────────────────────────────────────

def test_cli_storage_list(capsys):
    import ai_generation.cli as cli

    result = asyncio.run(cli.cmd_storage_list())
    out = capsys.readouterr().out
    assert len(result) >= 9
    assert "sqlite_local" in out
    assert "postgresql" in out
    assert "not_configured" in out


def test_cli_storage_write_read(tmp_path, capsys):
    import ai_generation.cli as cli

    # Use a temp db via env so we don't touch the repo data dir
    os.environ["ACOS_DB_PATH"] = str(tmp_path / "cli.db")
    try:
        result = asyncio.run(cli.cmd_storage_write("ledger", "cli-1", '{"ok": true}'))
        assert result["key"] == "cli-1"
        capsys.readouterr().out
        read = asyncio.run(cli.cmd_storage_read("ledger", "cli-1"))
        out = capsys.readouterr().out
        assert read["value"] == {"ok": True}
        assert "cli-1" in out
    finally:
        os.environ.pop("ACOS_DB_PATH", None)


def test_cli_storage_stats(capsys):
    import ai_generation.cli as cli

    result = asyncio.run(cli.cmd_storage_stats())
    out = capsys.readouterr().out
    assert result["backends_total"] >= 9
    assert "sqlite_local" in out


# ── MCP integration ──────────────────────────────────────────────────────

def test_mcp_storage_tools_registered():
    from ai_generation.mcp_tools import MCP_GENERATION_TOOLS, MCPGenerationTools

    for tool in ("list_storage_backends", "storage_write", "storage_read",
                 "storage_query", "get_storage_stats"):
        assert tool in MCP_GENERATION_TOOLS, f"missing {tool}"
        assert "inputSchema" in MCP_GENERATION_TOOLS[tool]
    handler = MCPGenerationTools()
    for tool in ("list_storage_backends", "storage_write", "storage_read",
                 "storage_query", "get_storage_stats"):
        assert hasattr(handler, f"_handle_{tool}"), f"missing handler {tool}"


def test_mcp_storage_write_read(tmp_path):
    from ai_generation.mcp_tools import MCP_GENERATION_TOOLS, MCPGenerationTools
    import ai_generation.mcp_tools as mt

    original = None
    # isolate SDK db via env before creating the handler
    os.environ["ACOS_DB_PATH"] = str(tmp_path / "mcp.db")
    try:
        handler = MCPGenerationTools()
        result = asyncio.run(handler.handle("storage_write", {
            "collection": "audit", "key": "evt-1",
            "value": {"event": "generated"}, "task": "audit"}))
        assert result["key"] == "evt-1"
        read = asyncio.run(handler.handle("storage_read", {
            "collection": "audit", "key": "evt-1", "task": "audit"}))
        assert read["value"] == {"event": "generated"}
        stats = asyncio.run(handler.handle("get_storage_stats", {}))
        assert stats["backends_total"] >= 9
    finally:
        os.environ.pop("ACOS_DB_PATH", None)
