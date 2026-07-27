"""
Phase 26 Tests — Capability Graph

Tests graph operations, pathfinding, fallback chains, cost estimation, and SDK/MCP exposure.
"""
import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))


def test_node_type_enum():
    from ai_generation.capability_graph import NodeType
    assert NodeType.PROVIDER.value == "provider"
    assert NodeType.CAPABILITY.value == "capability"


def test_edge_type_enum():
    from ai_generation.capability_graph import EdgeType
    assert EdgeType.SUPPORTS.value == "supports"
    assert EdgeType.FALLBACK_TO.value == "fallback_to"


def test_graph_import():
    from ai_generation.capability_graph import CapabilityGraph
    g = CapabilityGraph()
    assert g is not None


def test_graph_has_default_nodes():
    from ai_generation.capability_graph import CapabilityGraph
    g = CapabilityGraph()
    stats = g.get_stats()
    assert stats["node_count"] >= 18  # 12 providers + 6 capabilities
    assert stats["edge_count"] >= 15


def test_get_node():
    from ai_generation.capability_graph import CapabilityGraph
    g = CapabilityGraph()
    node = g.get_node("pollinations")
    assert node is not None
    assert node["name"] == "Pollinations"
    assert g.get_node("nonexistent") is None


def test_get_neighbors():
    from ai_generation.capability_graph import CapabilityGraph
    g = CapabilityGraph()
    neighbors = g.get_neighbors("pollinations")
    assert len(neighbors) >= 1
    names = [n["name"] for n in neighbors]
    assert "Text-to-Image" in names


def test_find_capability_path():
    from ai_generation.capability_graph import CapabilityGraph
    g = CapabilityGraph()
    paths = g.find_capability_path("text_to_image")
    assert len(paths) >= 8
    assert all(len(p.nodes) >= 2 for p in paths)


def test_find_capability_path_with_preference():
    from ai_generation.capability_graph import CapabilityGraph
    g = CapabilityGraph()
    paths = g.find_capability_path("text_to_image", preferred_provider="pollinations")
    assert len(paths) >= 8
    assert paths[0].nodes[0] == "pollinations"


def test_find_fallback_chain():
    from ai_generation.capability_graph import CapabilityGraph
    g = CapabilityGraph()
    chain = g.find_fallback_chain("text_to_image")
    assert len(chain) >= 5
    providers = [c["provider"] for c in chain]
    assert "pollinations" in providers


def test_find_fallback_chain_exclude():
    from ai_generation.capability_graph import CapabilityGraph
    g = CapabilityGraph()
    chain = g.find_fallback_chain("text_to_image", failed_provider="pollinations")
    providers = [c["provider"] for c in chain]
    assert "pollinations" not in providers


def test_estimate_execution_cost():
    from ai_generation.capability_graph import CapabilityGraph
    g = CapabilityGraph()
    cost = g.estimate_execution_cost("pollinations", "text_to_image")
    assert cost["estimated_cost_usd"] == 0.0
    assert cost["tier"] == "free"


def test_estimate_execution_cost_paid():
    from ai_generation.capability_graph import CapabilityGraph
    g = CapabilityGraph()
    cost = g.estimate_execution_cost("stability", "text_to_image")
    assert cost["estimated_cost_usd"] > 0
    assert cost["tier"] == "paid"


def test_validate_path_valid():
    from ai_generation.capability_graph import CapabilityGraph, ExecutionPath
    g = CapabilityGraph()
    path = ExecutionPath(nodes=["pollinations", "text_to_image"])
    result = g.validate_path(path)
    assert result["valid"] is True
    assert len(result["issues"]) == 0


def test_validate_path_invalid():
    from ai_generation.capability_graph import CapabilityGraph, ExecutionPath
    g = CapabilityGraph()
    path = ExecutionPath(nodes=["nonexistent", "text_to_image"])
    result = g.validate_path(path)
    assert result["valid"] is False
    assert len(result["issues"]) > 0


def test_graph_stats():
    from ai_generation.capability_graph import CapabilityGraph
    g = CapabilityGraph()
    stats = g.get_stats()
    assert "node_count" in stats
    assert "edge_count" in stats
    assert "node_types" in stats
    assert "edge_types" in stats


def test_path_serialization():
    from ai_generation.capability_graph import CapabilityGraph
    g = CapabilityGraph()
    paths = g.find_capability_path("text_to_image")
    d = paths[0].to_dict()
    assert "path_id" in d
    assert "nodes" in d
    assert "confidence" in d


# ── SDK Integration Tests ─────────────────────────────────────

def test_sdk_capability_graph_import():
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    assert hasattr(ai, 'capability_graph')
    assert hasattr(ai, 'find_capability_path')
    assert hasattr(ai, 'find_fallback_chain')
    assert hasattr(ai, 'estimate_execution_cost')
    assert hasattr(ai, 'get_capability_graph_stats')


def test_sdk_find_capability_path():
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    paths = ai.find_capability_path("text_to_image")
    assert len(paths) >= 8


def test_sdk_find_fallback_chain():
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    chain = ai.find_fallback_chain("text_to_image")
    assert len(chain) >= 5


def test_sdk_capability_graph_stats():
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    stats = ai.get_capability_graph_stats()
    assert stats["node_count"] >= 18


# ── MCP Tools Tests ──────────────────────────────────────────

def test_mcp_capability_graph_tools_exist():
    from ai_generation.mcp_tools import MCP_GENERATION_TOOLS
    assert "find_capability_path" in MCP_GENERATION_TOOLS
    assert "find_fallback_chain" in MCP_GENERATION_TOOLS
    assert "estimate_execution_cost" in MCP_GENERATION_TOOLS
    assert "get_capability_graph_stats" in MCP_GENERATION_TOOLS


def test_mcp_capability_graph_handler_import():
    from ai_generation.mcp_tools import MCPGenerationTools
    handler = MCPGenerationTools()
    assert hasattr(handler, '_handle_find_capability_path')
    assert hasattr(handler, '_handle_find_fallback_chain')
    assert hasattr(handler, '_handle_estimate_execution_cost')
    assert hasattr(handler, '_handle_get_capability_graph_stats')

# ── Dynamic Graph Updates (CGR-08) Tests ──

def test_dynamic_add_node():
    from ai_generation.capability_graph import CapabilityGraph, NodeType
    g = CapabilityGraph()
    result = g.dynamic_add_node("new-runtime", NodeType.RUNTIME, "Test Runtime")
    assert result["success"] is True
    assert result["node"]["node_id"] == "new-runtime"
    assert g.get_node("new-runtime") is not None


def test_dynamic_add_node_duplicate():
    from ai_generation.capability_graph import CapabilityGraph, NodeType
    g = CapabilityGraph()
    g.dynamic_add_node("test-node", NodeType.CAPABILITY, "Test")
    result = g.dynamic_add_node("test-node", NodeType.CAPABILITY, "Duplicate")
    assert result["success"] is False


def test_dynamic_add_edge():
    from ai_generation.capability_graph import CapabilityGraph, NodeType, EdgeType
    g = CapabilityGraph()
    g.dynamic_add_node("src", NodeType.PROVIDER, "Source")
    g.dynamic_add_node("tgt", NodeType.CAPABILITY, "Target")
    result = g.dynamic_add_edge("src", "tgt", EdgeType.SUPPORTS, 0.9)
    assert result["success"] is True
    assert result["edge"]["weight"] == 0.9


def test_dynamic_add_edge_missing_source():
    from ai_generation.capability_graph import CapabilityGraph, NodeType, EdgeType
    g = CapabilityGraph()
    g.dynamic_add_node("tgt", NodeType.CAPABILITY, "Target")
    result = g.dynamic_add_edge("missing", "tgt", EdgeType.SUPPORTS)
    assert result["success"] is False


def test_dynamic_add_edge_missing_target():
    from ai_generation.capability_graph import CapabilityGraph, NodeType, EdgeType
    g = CapabilityGraph()
    g.dynamic_add_node("src", NodeType.PROVIDER, "Source")
    result = g.dynamic_add_edge("src", "missing", EdgeType.SUPPORTS)
    assert result["success"] is False


def test_dynamic_update_node():
    from ai_generation.capability_graph import CapabilityGraph, NodeType
    g = CapabilityGraph()
    g.dynamic_add_node("test", NodeType.CAPABILITY, "Test", {"health": 0.5})
    result = g.dynamic_update_node("test", {"health": 0.9, "benchmark": 0.85})
    assert result["success"] is True
    assert result["new"]["health"] == 0.9
    assert result["new"]["benchmark"] == 0.85


def test_dynamic_update_node_missing():
    from ai_generation.capability_graph import CapabilityGraph
    g = CapabilityGraph()
    result = g.dynamic_update_node("missing", {"health": 0.9})
    assert result["success"] is False


def test_dynamic_remove_node():
    from ai_generation.capability_graph import CapabilityGraph, NodeType
    g = CapabilityGraph()
    g.dynamic_add_node("removable", NodeType.CAPABILITY, "Remove")
    result = g.dynamic_remove_node("removable")
    assert result["success"] is True
    assert g.get_node("removable") is None


def test_dynamic_remove_node_missing():
    from ai_generation.capability_graph import CapabilityGraph
    g = CapabilityGraph()
    result = g.dynamic_remove_node("missing")
    assert result["success"] is False


def test_dynamic_remove_edge():
    from ai_generation.capability_graph import CapabilityGraph, NodeType, EdgeType
    g = CapabilityGraph()
    g.dynamic_add_node("a", NodeType.PROVIDER, "A")
    g.dynamic_add_node("b", NodeType.CAPABILITY, "B")
    g.dynamic_add_edge("a", "b", EdgeType.SUPPORTS)
    result = g.dynamic_remove_edge("a", "b")
    assert result["success"] is True
    assert result["removed_count"] == 1


def test_dynamic_remove_edge_missing():
    from ai_generation.capability_graph import CapabilityGraph, NodeType, EdgeType
    g = CapabilityGraph()
    g.dynamic_add_node("a", NodeType.PROVIDER, "A")
    result = g.dynamic_remove_edge("a", "b")
    assert result["success"] is False


def test_batch_update_benchmark():
    from ai_generation.capability_graph import CapabilityGraph, NodeType
    g = CapabilityGraph()
    g.dynamic_add_node("p1", NodeType.PROVIDER, "P1")
    g.dynamic_add_node("p2", NodeType.PROVIDER, "P2")
    result = g.batch_update_benchmark([
        {"node_id": "p1", "benchmark_score": 0.95},
        {"node_id": "p2", "latency_ms": 42.0, "quality_score": 0.88},
        {"node_id": "missing", "benchmark_score": 0.5},
    ])
    assert result["success"] is True
    assert result["updated"] == 2
    assert len(result["errors"]) == 1


def test_batch_update_health():
    from ai_generation.capability_graph import CapabilityGraph, NodeType
    g = CapabilityGraph()
    g.dynamic_add_node("h1", NodeType.HARDWARE, "GPU1")
    g.dynamic_add_node("h2", NodeType.HARDWARE, "GPU2")
    result = g.batch_update_health({"h1": 0.95, "h2": 0.3, "missing": 0.8})
    assert result["success"] is True
    assert result["updated"] == 2
    assert len(result["errors"]) == 1


def test_get_update_history():
    from ai_generation.capability_graph import CapabilityGraph, NodeType
    g = CapabilityGraph()
    g.dynamic_add_node("n1", NodeType.CAPABILITY, "N1")
    g.dynamic_add_node("n2", NodeType.CAPABILITY, "N2")
    history = g.get_update_history()
    assert len(history) == 2
    assert history[0]["action"] == "add_node"


def test_get_update_history_limit():
    from ai_generation.capability_graph import CapabilityGraph, NodeType
    g = CapabilityGraph()
    for i in range(10):
        g.dynamic_add_node(f"n{i}", NodeType.CAPABILITY, f"N{i}")
    history = g.get_update_history(limit=3)
    assert len(history) == 3


def test_dynamic_get_stats():
    from ai_generation.capability_graph import CapabilityGraph, NodeType
    g = CapabilityGraph()
    g.dynamic_add_node("test", NodeType.CAPABILITY, "Test")
    stats = g.dynamic_get_stats()
    assert stats["update_count"] == 1
    assert stats["node_count"] >= 1


def test_sdk_dynamic_graph_add_node():
    from ai_generation.sdk import UncleFrappeAI
    sdk = UncleFrappeAI({"test_mode": True})
    result = sdk.dynamic_graph_add_node("sdk-node", "runtime", "SDK Node")
    assert result["success"] is True


def test_sdk_dynamic_graph_add_edge():
    from ai_generation.sdk import UncleFrappeAI
    sdk = UncleFrappeAI({"test_mode": True})
    sdk.dynamic_graph_add_node("sdk-a", "provider", "A")
    sdk.dynamic_graph_add_node("sdk-b", "capability", "B")
    result = sdk.dynamic_graph_add_edge("sdk-a", "sdk-b", "supports", 0.95)
    assert result["success"] is True


def test_sdk_dynamic_graph_update_node():
    from ai_generation.sdk import UncleFrappeAI
    sdk = UncleFrappeAI({"test_mode": True})
    sdk.dynamic_graph_add_node("sdk-u", "provider", "U")
    result = sdk.dynamic_graph_update_node("sdk-u", {"score": 0.9})
    assert result["success"] is True
    assert result["new"]["score"] == 0.9


def test_sdk_dynamic_graph_remove_node():
    from ai_generation.sdk import UncleFrappeAI
    sdk = UncleFrappeAI({"test_mode": True})
    sdk.dynamic_graph_add_node("sdk-r", "provider", "R")
    result = sdk.dynamic_graph_remove_node("sdk-r")
    assert result["success"] is True


def test_sdk_dynamic_graph_batch_benchmark():
    from ai_generation.sdk import UncleFrappeAI
    sdk = UncleFrappeAI({"test_mode": True})
    sdk.dynamic_graph_add_node("sdk-b", "provider", "B")
    result = sdk.dynamic_graph_batch_benchmark([{"node_id": "sdk-b", "benchmark_score": 0.88}])
    assert result["success"] is True


def test_sdk_dynamic_graph_batch_health():
    from ai_generation.sdk import UncleFrappeAI
    sdk = UncleFrappeAI({"test_mode": True})
    sdk.dynamic_graph_add_node("sdk-h", "hardware", "H")
    result = sdk.dynamic_graph_batch_health({"sdk-h": 0.95})
    assert result["success"] is True


def test_sdk_dynamic_graph_get_history():
    from ai_generation.sdk import UncleFrappeAI
    sdk = UncleFrappeAI({"test_mode": True})
    history = sdk.dynamic_graph_get_history()
    assert isinstance(history, list)


def test_sdk_dynamic_graph_get_stats():
    from ai_generation.sdk import UncleFrappeAI
    sdk = UncleFrappeAI({"test_mode": True})
    stats = sdk.dynamic_graph_get_stats()
    assert "update_count" in stats
    assert "node_count" in stats


def test_mcp_dynamic_graph_tools_exist():
    from ai_generation.mcp_tools import MCP_GENERATION_TOOLS
    assert "dynamic_graph_add_node" in MCP_GENERATION_TOOLS
    assert "dynamic_graph_add_edge" in MCP_GENERATION_TOOLS
    assert "dynamic_graph_update_node" in MCP_GENERATION_TOOLS
    assert "dynamic_graph_remove_node" in MCP_GENERATION_TOOLS
    assert "dynamic_graph_batch_benchmark" in MCP_GENERATION_TOOLS
    assert "dynamic_graph_batch_health" in MCP_GENERATION_TOOLS
    assert "dynamic_graph_get_history" in MCP_GENERATION_TOOLS
    assert "dynamic_graph_get_stats" in MCP_GENERATION_TOOLS


def test_mcp_dynamic_graph_handler_import():
    from ai_generation.mcp_tools import MCPGenerationTools
    handler = MCPGenerationTools()
    assert hasattr(handler, '_handle_dynamic_add_node')
    assert hasattr(handler, '_handle_dynamic_add_edge')
    assert hasattr(handler, '_handle_dynamic_update_node')
    assert hasattr(handler, '_handle_dynamic_remove_node')
    assert hasattr(handler, '_handle_dynamic_batch_benchmark')
    assert hasattr(handler, '_handle_dynamic_batch_health')
    assert hasattr(handler, '_handle_dynamic_get_history')
    assert hasattr(handler, '_handle_dynamic_get_stats')
