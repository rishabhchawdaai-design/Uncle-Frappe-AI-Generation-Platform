"""
Tests for the unified Tool Registry (configs/tools.json).
"""
import pytest

from ai_generation.tool_registry import ToolRegistry, get_tool_registry


def test_registry_loads_canonical_config():
    registry = get_tool_registry()
    stats = registry.stats()
    assert stats["total_tools"] >= 15
    assert stats["ready"] >= 10
    assert stats["blocked"] >= 5
    assert "ruff" in registry._tools


def test_registry_list_and_filters():
    registry = get_tool_registry()
    ids = {t["id"] for t in registry.list_tools()}
    for expected in ("ruff", "black", "isort", "pyright", "mypy", "bandit",
                     "semgrep", "import_linter", "eslint", "prettier"):
        assert expected in ids, f"missing tool: {expected}"
    blocked = {t["id"] for t in registry.list_tools(status="blocked")}
    for expected in ("codeql", "trivy", "hadolint", "archunit", "sonarqube"):
        assert expected in blocked, f"missing blocked tool: {expected}"
    security = registry.list_tools(category="security")
    assert {t["id"] for t in security} >= {"bandit", "semgrep"}
    found = registry.list_tools(search="formatter")
    assert any(t["id"] == "black" for t in found)
    assert registry.get_tool("ruff")["package"] == "ruff"


def test_registry_entries_truthful():
    registry = get_tool_registry()
    for t in registry.list_tools(status="ready"):
        assert t["verified"] is True
        assert t["package"], f"ready tool {t['id']} missing package"
        assert t["command"], f"ready tool {t['id']} missing command"
    for t in registry.list_tools(status="blocked"):
        assert t["verified"] is False
        assert t["note"], f"blocked tool {t['id']} missing note"


def test_sdk_tool_registry_surface():
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    tools = ai.list_tools(category="security")
    assert {t["id"] for t in tools} >= {"bandit", "semgrep"}
    assert ai.get_tool("ruff")["install_type"] == "pip"
    stats = ai.get_tool_registry_stats()
    assert stats["total_tools"] == ai.tool_registry.stats()["total_tools"]


def test_mcp_tools_tool_registry_exposed():
    from ai_generation.mcp_tools import MCP_GENERATION_TOOLS
    assert "list_tools" in MCP_GENERATION_TOOLS
    assert "get_tool" in MCP_GENERATION_TOOLS


@pytest.mark.asyncio
async def test_mcp_tool_list_tools_handler():
    from ai_generation.mcp_tools import MCPGenerationTools
    tools = MCPGenerationTools()
    result = await tools.handle("list_tools", {"search": "semgrep"})
    assert result["tools"][0]["id"] == "semgrep"


@pytest.mark.asyncio
async def test_mcp_tool_get_tool_handler():
    from ai_generation.mcp_tools import MCPGenerationTools
    tools = MCPGenerationTools()
    result = await tools.handle("get_tool", {"tool_id": "black"})
    assert result["tool"]["category"] == "format"
    missing = await tools.handle("get_tool", {"tool_id": "nope"})
    assert "error" in missing


def test_cli_tools_command(capsys):
    from ai_generation.cli import cmd_tools
    import asyncio
    asyncio.run(cmd_tools(category="security"))
    out = capsys.readouterr().out
    assert "Tool Registry" in out
    assert "semgrep" in out
