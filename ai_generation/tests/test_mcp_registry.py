"""
Tests for the unified MCP Server Registry (configs/mcp_servers.json).
"""
import pytest

from ai_generation.mcp_registry import MCPRegistry, get_mcp_registry


def test_registry_loads_canonical_config():
    registry = get_mcp_registry()
    stats = registry.stats()
    assert stats["total_servers"] >= 50
    assert stats["ready"] >= 40
    assert "firecrawl" in registry._servers


def test_registry_list_and_filters():
    registry = get_mcp_registry()
    all_servers = registry.list_servers()
    ids = {s["id"] for s in all_servers}
    for expected in ("filesystem", "git", "github", "docker", "kubernetes",
                     "browser", "playwright", "chrome", "puppeteer",
                     "firecrawl", "crawl4ai", "brave_search", "searxng",
                     "exa", "jina", "context7", "sequential_thinking",
                     "memory", "sqlite", "postgres", "redis", "qdrant",
                     "weaviate", "milvus", "chroma", "lancedb", "neo4j",
                     "openapi", "rest", "slack", "discord", "notion",
                     "google_drive", "figma", "linear", "jira", "obsidian",
                     "cloudflare", "vercel", "railway", "render", "gitlab",
                     "bitbucket", "huggingface", "replicate", "fal",
                     "together", "openrouter", "comfyui", "ollama"):
        assert expected in ids, f"missing server: {expected}"

    vector = registry.list_servers(category="vector-db")
    assert {s["id"] for s in vector} >= {"qdrant", "weaviate", "milvus",
                                         "chroma", "lancedb"}
    blocked = registry.list_servers(status="blocked")
    assert {s["id"] for s in blocked} >= {"faiss", "arangodb", "graphql",
                                          "vllm"}
    found = registry.list_servers(search="firecrawl")
    assert found[0]["id"] == "firecrawl"


def test_registry_server_entries_truthful():
    registry = get_mcp_registry()
    neo4j = registry.get_server("neo4j")
    assert neo4j["package"] == "neo4j-mcp"
    assert neo4j["verified"] is True
    assert neo4j["status"] == "ready"
    # blocked entries must carry a reason
    for s in registry.list_servers(status="blocked"):
        assert s["note"], f"blocked server {s['id']} missing note"
    # ready entries must have install command + package
    for s in registry.list_servers(status="ready"):
        assert s["command"], f"ready server {s['id']} missing command"
        assert s["package"], f"ready server {s['id']} missing package"


def test_registry_runtime_config_subset():
    registry = get_mcp_registry()
    runtime = registry.get_runtime_config()
    assert len(runtime) == registry.stats()["ready"]
    assert "postgres" in runtime
    assert "firecrawl" in runtime
    assert "faiss" not in runtime


def test_registry_categories():
    registry = get_mcp_registry()
    cats = registry.categories()
    for c in ("search", "vector-db", "infrastructure", "ai-platform",
              "version-control", "database", "browser"):
        assert cats.get(c, 0) >= 1


def test_sdk_mcp_registry_surface():
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    servers = ai.list_mcp_servers(category="ai-platform")
    assert {s["id"] for s in servers} >= {"huggingface", "replicate", "fal",
                                          "together", "openrouter", "ollama"}
    assert ai.get_mcp_server("postgres")["package"].endswith("server-postgres")
    stats = ai.get_mcp_registry_stats()
    assert stats["total_servers"] == ai.mcp_registry.stats()["total_servers"]


def test_mcp_tools_registry_exposed():
    from ai_generation.mcp_tools import MCP_GENERATION_TOOLS
    assert "list_mcp_servers" in MCP_GENERATION_TOOLS
    assert "get_mcp_server" in MCP_GENERATION_TOOLS


@pytest.mark.asyncio
async def test_mcp_tool_list_servers_handler():
    from ai_generation.mcp_tools import MCPGenerationTools
    tools = MCPGenerationTools()
    result = await tools.handle("list_mcp_servers", {"search": "firecrawl"})
    assert result["servers"][0]["id"] == "firecrawl"


@pytest.mark.asyncio
async def test_mcp_tool_get_server_handler():
    from ai_generation.mcp_tools import MCPGenerationTools
    tools = MCPGenerationTools()
    result = await tools.handle("get_mcp_server", {"server_id": "github"})
    assert result["server"]["package"] == "github/github-mcp-server"
    missing = await tools.handle("get_mcp_server", {"server_id": "nope"})
    assert "error" in missing


def test_cli_mcp_servers_command(capsys):
    from ai_generation.cli import cmd_mcp_servers
    import asyncio
    asyncio.run(cmd_mcp_servers(search="firecrawl"))
    out = capsys.readouterr().out
    assert "MCP Server Registry" in out
    assert "firecrawl" in out


# ── MCP runtime validation (offline config + live probes) ─────────

FAKE_SERVERS = {
    "mcp_servers": {
        "ok_server": {
            "id": "ok_server", "name": "OK", "category": "test",
            "status": "ready", "verified": True, "command": "python",
            "args": ["-c", "import time; time.sleep(30)"],
            "env": {"TEST_VAR": "${TEST_VAR}"}, "package": "fake-ok",
        },
        "exit_server": {
            "id": "exit_server", "name": "Exits", "category": "test",
            "status": "ready", "verified": True, "command": "python",
            "args": ["-c", "import sys; sys.exit(3)"],
            "env": {}, "package": "fake-exit",
        },
        "blocked_server": {
            "id": "blocked_server", "name": "Blocked", "category": "test",
            "status": "blocked", "verified": False, "command": "python",
            "args": ["-c", "pass"], "env": {}, "note": "no stable distribution",
        },
    }
}


def _fake_registry(tmp_path, monkeypatch=None, env=None):
    import json as _json
    cfg = tmp_path / "mcp_servers.json"
    cfg.write_text(_json.dumps(FAKE_SERVERS))
    from ai_generation.mcp_registry import MCPRegistry
    registry = MCPRegistry(config_path=cfg)
    if env:
        for k, v in env.items():
            monkeypatch.setenv(k, v)
    return registry


def test_validate_config_offline(tmp_path, monkeypatch):
    registry = _fake_registry(tmp_path, monkeypatch, env={"TEST_VAR": "x"})
    ok = registry.validate_config("ok_server")
    assert ok["status"] == "valid" and ok["valid"] is True
    assert ok["errors"] == []


def test_validate_config_missing_env(tmp_path, monkeypatch):
    registry = _fake_registry(tmp_path, monkeypatch)  # TEST_VAR not set
    result = registry.validate_config("ok_server")
    assert result["status"] == "invalid"
    assert any("TEST_VAR" in e for e in result["errors"])


def test_validate_config_unknown_and_blocked(tmp_path):
    registry = _fake_registry(tmp_path)
    assert registry.validate_config("nope")["status"] == "error"
    blocked = registry.validate_config("blocked_server")
    assert blocked["status"] == "blocked" and blocked["valid"] is False
    assert "no stable distribution" in blocked["error"]


def test_health_check_live_healthy(tmp_path):
    registry = _fake_registry(tmp_path)
    report = registry.health_check("ok_server", timeout=1.0)
    assert report["status"] == "healthy" and report["healthy"] is True
    assert report.get("running") is True


def test_health_check_live_unhealthy(tmp_path):
    registry = _fake_registry(tmp_path)
    report = registry.health_check("exit_server", timeout=2.0)
    assert report["status"] == "unhealthy" and report["healthy"] is False
    assert report["exit_code"] == 3


def test_health_check_unknown_and_blocked(tmp_path):
    registry = _fake_registry(tmp_path)
    assert registry.health_check("nope")["status"] == "error"
    blocked = registry.health_check("blocked_server")
    assert blocked["status"] == "blocked" and blocked["healthy"] is False


def test_run_validation_all(tmp_path, monkeypatch):
    monkeypatch.setenv("TEST_VAR", "x")
    registry = _fake_registry(tmp_path)
    results = registry.run_validation()
    by_id = {r["server_id"]: r for r in results}
    assert by_id["ok_server"]["status"] == "valid"
    assert by_id["blocked_server"]["status"] == "blocked"
    # live mode probes only launch-ready servers
    live = registry.run_validation(live=True, timeout=0.5)
    live_by_id = {r["server_id"]: r for r in live}
    assert live_by_id["ok_server"]["status"] == "healthy"
    assert live_by_id["blocked_server"]["status"] == "blocked"


def test_sdk_mcp_validation_surface(tmp_path):
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    assert ai.validate_mcp_server("postgres")["server_id"] == "postgres"
    assert ai.validate_mcp_server("faiss")["status"] == "blocked"
    assert ai.run_mcp_validation(live=False)


@pytest.mark.asyncio
async def test_mcp_tool_validation_handlers():
    from ai_generation.mcp_tools import MCPGenerationTools
    tools = MCPGenerationTools()
    result = await tools.handle("validate_mcp_server", {"server_id": "ollama"})
    assert result["server_id"] == "ollama"
    missing = await tools.handle("validate_mcp_server", {"server_id": "nope"})
    assert missing["status"] == "error"


def test_cli_mcp_check_command(capsys):
    from ai_generation.cli import cmd_mcp_check
    import asyncio
    asyncio.run(cmd_mcp_check(server_id="ollama"))
    out = capsys.readouterr().out
    assert "MCP config validation" in out


def test_cli_mcp_check_all_command(capsys):
    from ai_generation.cli import cmd_mcp_check_all
    import asyncio
    asyncio.run(cmd_mcp_check_all(live=False))
    out = capsys.readouterr().out
    assert "MCP validation — 59 servers" in out
    assert "[FAIL] faiss: blocked" in out
