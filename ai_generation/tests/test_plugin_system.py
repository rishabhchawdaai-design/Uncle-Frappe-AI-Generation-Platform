"""
Phase 20 Tests — Plugin System Foundation

Tests plugin lifecycle, registration, activation, deactivation,
tool registration, dependency resolution, and SDK/MCP exposure.
"""
import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))


# ── PluginType / PluginState Enum Tests ──────────────────────

def test_plugin_type_enum():
    from ai_generation.plugin_system import PluginType
    assert PluginType.TOOL.value == "tool"
    assert PluginType.RUNTIME.value == "runtime"
    assert PluginType.COMPUTE.value == "compute"
    assert PluginType.WORKFLOW.value == "workflow"
    assert PluginType.EXTENSION.value == "extension"


def test_plugin_state_enum():
    from ai_generation.plugin_system import PluginState
    assert PluginState.REGISTERED.value == "registered"
    assert PluginState.ACTIVE.value == "active"
    assert PluginState.FAILED.value == "failed"


# ── PluginEntry Tests ─────────────────────────────────────────

def test_plugin_entry_import():
    from ai_generation.plugin_system import PluginEntry, PluginMetadata
    entry = PluginEntry()
    assert entry.state.value == "registered"
    assert entry.metadata.plugin_id == ""


def test_plugin_entry_serialization():
    from ai_generation.plugin_system import PluginEntry, PluginMetadata, PluginType
    metadata = PluginMetadata(plugin_id="test-plugin", name="Test", version="1.0.0")
    entry = PluginEntry(metadata=metadata)
    d = entry.to_dict()
    assert d["plugin_id"] == "test-plugin"
    assert d["state"] == "registered"


# ── PluginSystem Lifecycle Tests ──────────────────────────────

def test_plugin_system_import():
    from ai_generation.plugin_system import PluginSystem
    ps = PluginSystem()
    assert ps is not None


def test_plugin_system_has_builtins():
    from ai_generation.plugin_system import PluginSystem, PluginState
    ps = PluginSystem()
    plugins = ps.list_plugins()
    assert len(plugins) >= 2
    ids = [p["plugin_id"] for p in plugins]
    assert "acos-core" in ids
    assert "mcp-tools" in ids
    # Built-ins should be active
    active = [p for p in plugins if p["state"] == "active"]
    assert len(active) >= 2


def test_register_plugin():
    from ai_generation.plugin_system import PluginSystem, PluginType
    ps = PluginSystem()
    entry = ps.register_plugin(
        plugin_id="test-plugin",
        name="Test Plugin",
        version="1.0.0",
        plugin_type=PluginType.TOOL,
        description="A test plugin",
    )
    assert entry.metadata.plugin_id == "test-plugin"
    assert entry.state.value == "registered"


def test_resolve_plugin_no_deps():
    from ai_generation.plugin_system import PluginSystem
    ps = PluginSystem()
    ps.register_plugin(plugin_id="dep-test", name="Dep Test")
    assert ps.resolve_plugin("dep-test") is True


def test_resolve_plugin_with_deps():
    from ai_generation.plugin_system import PluginSystem
    ps = PluginSystem()
    ps.register_plugin(plugin_id="parent-plugin", name="Parent")
    ps.register_plugin(plugin_id="child-plugin", name="Child",
                        dependencies=[{"plugin_id": "parent-plugin"}])
    assert ps.resolve_plugin("child-plugin") is True


def test_resolve_plugin_missing_deps():
    from ai_generation.plugin_system import PluginSystem, PluginState
    ps = PluginSystem()
    ps.register_plugin(plugin_id="orphan-plugin", name="Orphan",
                        dependencies=[{"plugin_id": "nonexistent"}])
    assert ps.resolve_plugin("orphan-plugin") is False
    entry = ps._plugins["orphan-plugin"]
    assert entry.state == PluginState.FAILED
    assert "Missing" in entry.error


def test_resolve_plugin_optional_deps():
    from ai_generation.plugin_system import PluginSystem
    ps = PluginSystem()
    ps.register_plugin(plugin_id="opt-plugin", name="Optional Dep Plugin",
                        dependencies=[{"plugin_id": "nonexistent", "optional": True}])
    assert ps.resolve_plugin("opt-plugin") is True


def test_install_plugin():
    from ai_generation.plugin_system import PluginSystem, PluginState
    ps = PluginSystem()
    ps.register_plugin(plugin_id="install-test", name="Install Test")
    assert ps.install_plugin("install-test") is True
    assert ps._plugins["install-test"].state == PluginState.INSTALLED


def test_activate_plugin():
    from ai_generation.plugin_system import PluginSystem, PluginState
    ps = PluginSystem()
    ps.register_plugin(plugin_id="activate-test", name="Activate Test")
    ps.install_plugin("activate-test")
    assert ps.activate_plugin("activate-test") is True
    assert ps._plugins["activate-test"].state == PluginState.ACTIVE
    assert ps._plugins["activate-test"].activation_count == 1


def test_deactivate_plugin():
    from ai_generation.plugin_system import PluginSystem, PluginState
    ps = PluginSystem()
    ps.register_plugin(plugin_id="deactivate-test", name="Deactivate Test")
    ps.install_plugin("deactivate-test")
    ps.activate_plugin("deactivate-test")
    assert ps.deactivate_plugin("deactivate-test") is True
    assert ps._plugins["deactivate-test"].state == PluginState.DEACTIVATED


def test_deactivate_protected_plugin():
    from ai_generation.plugin_system import PluginSystem
    ps = PluginSystem()
    ps.register_plugin(plugin_id="core-dep", name="Core Dep")
    ps.install_plugin("core-dep")
    ps.activate_plugin("core-dep")
    ps.register_plugin(plugin_id="consumer", name="Consumer",
                        dependencies=[{"plugin_id": "core-dep"}])
    ps.install_plugin("consumer")
    ps.activate_plugin("consumer")
    # Cannot deactivate core-dep because consumer depends on it
    assert ps.deactivate_plugin("core-dep") is False


def test_uninstall_plugin():
    from ai_generation.plugin_system import PluginSystem, PluginState
    ps = PluginSystem()
    ps.register_plugin(plugin_id="uninstall-test", name="Uninstall Test")
    ps.install_plugin("uninstall-test")
    ps.activate_plugin("uninstall-test")
    assert ps.uninstall_plugin("uninstall-test") is True
    assert ps._plugins["uninstall-test"].state == PluginState.UNINSTALLED


def test_list_plugins_by_type():
    from ai_generation.plugin_system import PluginSystem, PluginType
    ps = PluginSystem()
    ps.register_plugin(plugin_id="tool-1", name="Tool 1", plugin_type=PluginType.TOOL)
    ps.register_plugin(plugin_id="runtime-1", name="Runtime 1", plugin_type=PluginType.RUNTIME)
    tools = ps.list_plugins(plugin_type=PluginType.TOOL)
    assert all(p["plugin_type"] == "tool" for p in tools)


def test_list_plugins_by_state():
    from ai_generation.plugin_system import PluginSystem, PluginState
    ps = PluginSystem()
    ps.register_plugin(plugin_id="state-test", name="State Test")
    ps.install_plugin("state-test")
    installed = ps.list_plugins(state=PluginState.INSTALLED)
    assert any(p["plugin_id"] == "state-test" for p in installed)


def test_plugin_tool_registration():
    from ai_generation.plugin_system import PluginSystem
    ps = PluginSystem()
    ps.register_plugin(plugin_id="tool-plugin", name="Tool Plugin")
    ps.install_plugin("tool-plugin")
    ps.activate_plugin("tool-plugin")

    def my_handler(args):
        return {"result": "success"}

    ps.register_tool("tool-plugin", "my_custom_tool", my_handler,
                       description="A custom tool")
    tools = ps.list_tools()
    assert len(tools) >= 1
    assert tools[0]["name"] == "my_custom_tool"
    assert tools[0]["active"] is True


def test_plugin_event_emission():
    from ai_generation.plugin_system import PluginSystem
    ps = PluginSystem()
    events = []
    ps.on("registered", lambda pid: events.append(("registered", pid)))
    ps.on("activated", lambda pid: events.append(("activated", pid)))
    ps.register_plugin(plugin_id="event-test", name="Event Test")
    ps.install_plugin("event-test")
    ps.activate_plugin("event-test")
    assert len(events) == 2
    assert events[0] == ("registered", "event-test")
    assert events[1] == ("activated", "event-test")


def test_plugin_stats():
    from ai_generation.plugin_system import PluginSystem
    ps = PluginSystem()
    stats = ps.get_stats()
    assert "total_plugins" in stats
    assert stats["total_plugins"] >= 2
    assert "by_type" in stats
    assert "by_state" in stats


def test_plugin_version_compatibility():
    from ai_generation.plugin_system import PluginSystem
    ps = PluginSystem()
    ps.register_plugin(plugin_id="base-v2", name="Base V2", version="2.0.0")
    ps.register_plugin(plugin_id="consumer-v1", name="Consumer V1",
                        dependencies=[{"plugin_id": "base-v2", "version_range": ">=1.0.0"}])
    assert ps.resolve_plugin("consumer-v1") is True


# ── SDK Integration Tests ─────────────────────────────────────

def test_sdk_plugin_system_import():
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    assert hasattr(ai, 'plugin_system')
    assert hasattr(ai, 'register_plugin')
    assert hasattr(ai, 'activate_plugin')
    assert hasattr(ai, 'deactivate_plugin')
    assert hasattr(ai, 'uninstall_plugin')
    assert hasattr(ai, 'list_plugins')
    assert hasattr(ai, 'get_plugin')
    assert hasattr(ai, 'list_plugin_tools')
    assert hasattr(ai, 'get_plugin_stats')


def test_sdk_list_plugins():
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    plugins = ai.list_plugins()
    assert len(plugins) >= 2


def test_sdk_plugin_stats():
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    stats = ai.get_plugin_stats()
    assert stats["total_plugins"] >= 2


# ── MCP Tools Tests ──────────────────────────────────────────

def test_mcp_plugin_tools_exist():
    from ai_generation.mcp_tools import MCP_GENERATION_TOOLS
    assert "list_plugins" in MCP_GENERATION_TOOLS
    assert "get_plugin" in MCP_GENERATION_TOOLS
    assert "list_plugin_tools" in MCP_GENERATION_TOOLS
    assert "get_plugin_stats" in MCP_GENERATION_TOOLS


def test_mcp_plugin_handler_import():
    from ai_generation.mcp_tools import MCPGenerationTools
    handler = MCPGenerationTools()
    assert hasattr(handler, '_handle_list_plugins')
    assert hasattr(handler, '_handle_get_plugin')
    assert hasattr(handler, '_handle_list_plugin_tools')
    assert hasattr(handler, '_handle_get_plugin_stats')
