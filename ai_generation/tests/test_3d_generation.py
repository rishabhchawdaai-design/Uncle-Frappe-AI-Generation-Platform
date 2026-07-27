"""
Phase 24 Tests — 3D Generation

Tests 3D model profiles, mode selection, format routing, and SDK/MCP exposure.
"""
import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))


def test_generation_3d_mode_enum():
    from ai_generation.generation_3d import Generation3DMode
    assert Generation3DMode.TEXT_TO_3D.value == "text_to_3d"
    assert Generation3DMode.IMAGE_TO_3D.value == "image_to_3d"
    assert Generation3DMode.POINT_CLOUD.value == "point_cloud"


def test_output_format_enum():
    from ai_generation.generation_3d import OutputFormat
    assert OutputFormat.OBJ.value == "obj"
    assert OutputFormat.GLTF.value == "gltf"
    assert OutputFormat.GLB.value == "glb"


def test_generation_3d_profile_serialization():
    from ai_generation.generation_3d import TRELLIS_PROFILE
    d = TRELLIS_PROFILE.to_dict()
    assert d["model_id"] == "microsoft/trellis"
    assert d["name"] == "TRELLIS"
    assert "text_to_3d" in d["supported_modes"]


def test_generation_3d_engine_import():
    from ai_generation.generation_3d import Generation3DEngine
    engine = Generation3DEngine()
    assert engine is not None


def test_3d_engine_has_profiles():
    from ai_generation.generation_3d import Generation3DEngine
    engine = Generation3DEngine()
    models = engine.list_models()
    assert len(models) >= 4
    ids = [m["model_id"] for m in models]
    assert "microsoft/trellis" in ids
    assert "tencent/hunyuan3d" in ids
    assert "openai/point-e" in ids
    assert "openai/shap-e" in ids


def test_3d_engine_get_model():
    from ai_generation.generation_3d import Generation3DEngine
    engine = Generation3DEngine()
    m = engine.get_model("microsoft/trellis")
    assert m is not None
    assert m["developer"] == "Microsoft Research"
    assert engine.get_model("nonexistent") is None


def test_3d_engine_list_by_mode():
    from ai_generation.generation_3d import Generation3DEngine
    engine = Generation3DEngine()
    text_models = engine.list_models(mode="text_to_3d")
    assert len(text_models) >= 3
    all_text = all("text_to_3d" in m["supported_modes"] for m in text_models)
    assert all_text


def test_3d_select_model_default():
    from ai_generation.generation_3d import Generation3DEngine
    engine = Generation3DEngine()
    model = engine.select_model("text_to_3d")
    assert model is not None
    assert model in ["microsoft/trellis", "tencent/hunyuan3d", "openai/point-e", "openai/shap-e"]


def test_3d_select_model_vram_constraint():
    from ai_generation.generation_3d import Generation3DEngine
    engine = Generation3DEngine()
    # With 8GB VRAM, only Point-E and Shap-E fit
    model = engine.select_model("text_to_3d", max_vram_gb=8.0)
    assert model in ["openai/point-e", "openai/shap-e"]


def test_3d_select_model_no_match():
    from ai_generation.generation_3d import Generation3DEngine
    engine = Generation3DEngine()
    # With 1GB VRAM, no model fits
    model = engine.select_model("text_to_3d", max_vram_gb=1.0)
    assert model is None


def test_3d_get_output_formats():
    from ai_generation.generation_3d import Generation3DEngine
    engine = Generation3DEngine()
    formats = engine.get_output_formats("microsoft/trellis")
    assert "gltf" in formats
    assert "glb" in formats


def test_3d_stats():
    from ai_generation.generation_3d import Generation3DEngine
    engine = Generation3DEngine()
    stats = engine.get_stats()
    assert stats["model_count"] >= 4


def test_3d_negotiation_candidates():
    from ai_generation.generation_3d import Generation3DEngine
    engine = Generation3DEngine()
    candidates = engine.to_negotiation_candidates()
    assert len(candidates) >= 3
    assert all(c["layer"] == "3d_generation" for c in candidates)


# ── SDK Integration Tests ─────────────────────────────────────

def test_sdk_3d_import():
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    assert hasattr(ai, 'generation_3d')
    assert hasattr(ai, 'list_3d_models')
    assert hasattr(ai, 'select_3d_model')
    assert hasattr(ai, 'get_3d_output_formats')
    assert hasattr(ai, 'get_3d_stats')


def test_sdk_list_3d_models():
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    models = ai.list_3d_models()
    assert len(models) >= 4


def test_sdk_select_3d_model():
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    model = ai.select_3d_model()
    assert model != ""


def test_sdk_3d_stats():
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    stats = ai.get_3d_stats()
    assert stats["model_count"] >= 4


# ── MCP Tools Tests ──────────────────────────────────────────

def test_mcp_3d_tools_exist():
    from ai_generation.mcp_tools import MCP_GENERATION_TOOLS
    assert "list_3d_models" in MCP_GENERATION_TOOLS
    assert "select_3d_model" in MCP_GENERATION_TOOLS
    assert "get_3d_output_formats" in MCP_GENERATION_TOOLS
    assert "get_3d_stats" in MCP_GENERATION_TOOLS


def test_mcp_3d_handler_import():
    from ai_generation.mcp_tools import MCPGenerationTools
    handler = MCPGenerationTools()
    assert hasattr(handler, '_handle_list_3d_models')
    assert hasattr(handler, '_handle_select_3d_model')
    assert hasattr(handler, '_handle_get_3d_output_formats')
    assert hasattr(handler, '_handle_get_3d_stats')
