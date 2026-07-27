"""
Phase 19 Tests — Edge AI Runtime Detection

Tests edge hardware profiles, detection, template generation,
negotiation integration, and SDK/MCP exposure.
"""
import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))


# ── EdgeHardware Enum Tests ──────────────────────────────────

def test_edge_hardware_enum():
    from ai_generation.edge_ai import EdgeHardware
    assert EdgeHardware.APPLE_ANE.value == "apple_ane"
    assert EdgeHardware.QUALCOMM_NPU.value == "qualcomm_npu"
    assert EdgeHardware.INTEL_NPU.value == "intel_npu"
    assert EdgeHardware.NVIDIA_JETSON.value == "nvidia_jetson"
    assert EdgeHardware.GOOGLE_CORAL.value == "google_coral"
    assert EdgeHardware.CPU_ONLY.value == "cpu_only"


def test_edge_runtime_enum():
    from ai_generation.edge_ai import EdgeRuntime
    assert EdgeRuntime.COREML.value == "coreml"
    assert EdgeRuntime.MLX.value == "mlx"
    assert EdgeRuntime.TENSORRT.value == "tensorrt"
    assert EdgeRuntime.OPENVINO.value == "openvino"


# ── EdgeHardwareProfile Tests ─────────────────────────────────

def test_edge_hardware_profile_import():
    from ai_generation.edge_ai import EdgeHardwareProfile, EdgeHardware
    p = EdgeHardwareProfile(hardware=EdgeHardware.APPLE_ANE, name="Test")
    assert p.hardware == EdgeHardware.APPLE_ANE
    assert p.name == "Test"


def test_edge_hardware_profile_serialization():
    from ai_generation.edge_ai import APPLE_ANE_M4_PROFILE
    d = APPLE_ANE_M4_PROFILE.to_dict()
    assert d["hardware"] == "apple_ane"
    assert d["compute_tops"] == 38.0
    assert d["supports_llm"] is True
    assert "coreml" in d["supported_runtimes"]


# ── EdgeAIManager Tests ───────────────────────────────────────

def test_edge_ai_manager_import():
    from ai_generation.edge_ai import EdgeAIManager
    mgr = EdgeAIManager()
    assert mgr is not None


def test_edge_ai_detect_hardware():
    from ai_generation.edge_ai import EdgeAIManager
    mgr = EdgeAIManager()
    detected = mgr.detect_hardware()
    assert "detections" in detected
    assert "platform" in detected
    assert len(detected["detections"]) >= 1


def test_edge_ai_list_profiles():
    from ai_generation.edge_ai import EdgeAIManager
    mgr = EdgeAIManager()
    profiles = mgr.list_profiles()
    assert len(profiles) >= 6
    assert all("hardware" in p for p in profiles)


def test_edge_ai_list_profiles_by_hardware():
    from ai_generation.edge_ai import EdgeAIManager
    mgr = EdgeAIManager()
    apple_profiles = mgr.list_profiles(hardware="apple_ane")
    assert len(apple_profiles) >= 1
    assert all(p["hardware"] == "apple_ane" for p in apple_profiles)


def test_edge_ai_list_profiles_by_platform():
    from ai_generation.edge_ai import EdgeAIManager
    mgr = EdgeAIManager()
    macos_profiles = mgr.list_profiles(platform_filter="macos")
    assert len(macos_profiles) >= 1
    # All returned profiles should match the filter (macos or "any")
    assert all(p["platform"] in ("macos", "any") for p in macos_profiles)


def test_edge_ai_get_profile():
    from ai_generation.edge_ai import EdgeAIManager
    mgr = EdgeAIManager()
    p = mgr.get_profile("apple_ane")
    assert p is not None
    assert p["hardware"] == "apple_ane"
    assert mgr.get_profile("nonexistent") is None


def test_edge_ai_find_optimal_profile():
    from ai_generation.edge_ai import EdgeAIManager
    mgr = EdgeAIManager()
    profile = mgr.find_optimal_profile("text_generation")
    assert profile is not None
    assert profile["hardware"] is not None


def test_edge_ai_find_optimal_profile_power_constraint():
    from ai_generation.edge_ai import EdgeAIManager
    mgr = EdgeAIManager()
    # Very low power should exclude high-power devices
    profile = mgr.find_optimal_profile("text_generation", max_power_watts=5)
    # Should still find something (CPU-only or Coral)
    if profile:
        assert profile["power_watts"] <= 5


def test_edge_ai_find_optimal_profile_no_match():
    from ai_generation.edge_ai import EdgeAIManager
    mgr = EdgeAIManager()
    # Unsupported task type
    profile = mgr.find_optimal_profile("video_generation")
    assert profile is None


def test_edge_ai_generate_apple_template():
    from ai_generation.edge_ai import EdgeAIManager
    mgr = EdgeAIManager()
    tmpl = mgr.generate_deployment_template("apple_ane", "text_generation")
    assert "hardware" in tmpl
    assert "script" in tmpl
    assert "llama" in tmpl["script"].lower() or "metal" in tmpl["script"].lower()


def test_edge_ai_generate_jetson_template():
    from ai_generation.edge_ai import EdgeAIManager
    mgr = EdgeAIManager()
    tmpl = mgr.generate_deployment_template("nvidia_jetson", "text_generation")
    assert "hardware" in tmpl
    assert "script" in tmpl
    assert "tensorrt" in tmpl["script"].lower() or "jetson" in tmpl["script"].lower()


def test_edge_ai_generate_qualcomm_template():
    from ai_generation.edge_ai import EdgeAIManager
    mgr = EdgeAIManager()
    tmpl = mgr.generate_deployment_template("qualcomm_npu", "text_generation")
    assert "hardware" in tmpl
    assert "script" in tmpl


def test_edge_ai_generate_intel_template():
    from ai_generation.edge_ai import EdgeAIManager
    mgr = EdgeAIManager()
    tmpl = mgr.generate_deployment_template("intel_npu", "image_classification")
    assert "hardware" in tmpl
    assert "openvino" in tmpl["script"].lower()


def test_edge_ai_generate_coral_template():
    from ai_generation.edge_ai import EdgeAIManager
    mgr = EdgeAIManager()
    tmpl = mgr.generate_deployment_template("google_coral", "image_classification")
    assert "hardware" in tmpl
    assert "tflite" in tmpl["script"].lower()


def test_edge_ai_generate_cpu_template():
    from ai_generation.edge_ai import EdgeAIManager
    mgr = EdgeAIManager()
    tmpl = mgr.generate_deployment_template("cpu_only", "text_generation")
    assert "hardware" in tmpl
    assert "script" in tmpl


def test_edge_ai_generate_unknown_template():
    from ai_generation.edge_ai import EdgeAIManager
    mgr = EdgeAIManager()
    tmpl = mgr.generate_deployment_template("unknown_hardware", "text_generation")
    assert "error" in tmpl


def test_edge_ai_stats():
    from ai_generation.edge_ai import EdgeAIManager
    mgr = EdgeAIManager()
    stats = mgr.get_stats()
    assert stats["profile_count"] >= 6
    assert stats["tier"] == 3
    assert "detected_hardware" in stats


def test_edge_ai_negotiation_candidates():
    from ai_generation.edge_ai import EdgeAIManager
    mgr = EdgeAIManager()
    candidates = mgr.to_negotiation_candidates("text_generation")
    # Should have at least CPU-only candidate
    assert len(candidates) >= 1
    assert all(c["layer"] == "edge" for c in candidates)
    assert all(c["tier"] == 3 for c in candidates)
    assert all(c["cost_usd"] == 0.0 for c in candidates)


# ── SDK Integration Tests ─────────────────────────────────────

def test_sdk_edge_ai_import():
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    assert hasattr(ai, 'edge_ai')
    assert hasattr(ai, 'detect_edge_hardware')
    assert hasattr(ai, 'list_edge_profiles')
    assert hasattr(ai, 'find_optimal_edge_profile')
    assert hasattr(ai, 'generate_edge_template')
    assert hasattr(ai, 'get_edge_ai_stats')


def test_sdk_detect_edge_hardware():
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    detected = ai.detect_edge_hardware()
    assert "detections" in detected


def test_sdk_list_edge_profiles():
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    profiles = ai.list_edge_profiles()
    assert len(profiles) >= 6


def test_sdk_edge_ai_stats():
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    stats = ai.get_edge_ai_stats()
    assert stats["tier"] == 3


# ── MCP Tools Tests ──────────────────────────────────────────

def test_mcp_edge_ai_tools_exist():
    from ai_generation.mcp_tools import MCP_GENERATION_TOOLS
    assert "detect_edge_hardware" in MCP_GENERATION_TOOLS
    assert "list_edge_profiles" in MCP_GENERATION_TOOLS
    assert "find_edge_profile" in MCP_GENERATION_TOOLS
    assert "generate_edge_template" in MCP_GENERATION_TOOLS
    assert "get_edge_ai_stats" in MCP_GENERATION_TOOLS


def test_mcp_edge_ai_handler_import():
    from ai_generation.mcp_tools import MCPGenerationTools
    handler = MCPGenerationTools()
    assert hasattr(handler, '_handle_detect_edge_hardware')
    assert hasattr(handler, '_handle_list_edge_profiles')
    assert hasattr(handler, '_handle_find_edge_profile')
    assert hasattr(handler, '_handle_generate_edge_template')
    assert hasattr(handler, '_handle_get_edge_ai_stats')
