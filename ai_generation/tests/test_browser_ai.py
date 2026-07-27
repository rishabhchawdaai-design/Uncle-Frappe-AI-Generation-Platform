"""
Phase 18 Tests — Browser AI Inference Layer

Tests browser runtime profiles, model profiles, template generation,
negotiation integration, and SDK/MCP exposure.
"""
import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))


# ── BrowserRuntime Enum Tests ────────────────────────────────

def test_browser_runtime_enum():
    from ai_generation.browser_ai import BrowserRuntime
    assert BrowserRuntime.TRANSFORMERS_JS.value == "transformers_js"
    assert BrowserRuntime.WEBLLM.value == "webllm"
    assert BrowserRuntime.ONNX_WEB.value == "onnx_web"
    assert BrowserRuntime.TFJS.value == "tensorflow_js"
    assert BrowserRuntime.WEBNN.value == "webnn"


def test_browser_backend_enum():
    from ai_generation.browser_ai import BrowserBackend
    assert BrowserBackend.WASM.value == "wasm"
    assert BrowserBackend.WEBGPU.value == "webgpu"
    assert BrowserBackend.WEBGL.value == "webgl"


# ── BrowserModelProfile Tests ─────────────────────────────────

def test_browser_model_profile_import():
    from ai_generation.browser_ai import BrowserModelProfile
    m = BrowserModelProfile(model_id="test", name="Test Model")
    assert m.model_id == "test"
    assert m.name == "Test Model"


def test_browser_model_profile_serialization():
    from ai_generation.browser_ai import BrowserModelProfile, BrowserRuntime, BrowserBackend
    m = BrowserModelProfile(
        model_id="Xenova/gpt2", name="GPT-2",
        runtime=BrowserRuntime.TRANSFORMERS_JS,
        backend=BrowserBackend.WASM,
        parameter_count_b=0.124, memory_mb=500,
        category="llm",
    )
    d = m.to_dict()
    assert d["model_id"] == "Xenova/gpt2"
    assert d["runtime"] == "transformers_js"
    assert d["backend"] == "wasm"
    assert d["parameter_count_b"] == 0.124


# ── BrowserCapabilityProfile Tests ────────────────────────────

def test_browser_capability_profile():
    from ai_generation.browser_ai import TRANSFORMERS_JS_PROFILE
    d = TRANSFORMERS_JS_PROFILE.to_dict()
    assert d["runtime"] == "transformers_js"
    assert d["capabilities"]["text_generation"] is True
    assert d["capabilities"]["image_generation"] is True
    assert d["requires_webgpu"] is False
    assert d["mobile_support"] is True


def test_webllm_requires_webgpu():
    from ai_generation.browser_ai import WEBLLM_PROFILE
    d = WEBLLM_PROFILE.to_dict()
    assert d["requires_webgpu"] is True


# ── BrowserAIManager Tests ────────────────────────────────────

def test_browser_ai_manager_import():
    from ai_generation.browser_ai import BrowserAIManager
    mgr = BrowserAIManager()
    assert mgr is not None


def test_browser_ai_list_runtimes():
    from ai_generation.browser_ai import BrowserAIManager
    mgr = BrowserAIManager()
    runtimes = mgr.list_runtimes()
    assert len(runtimes) == 4
    names = [r["runtime"] for r in runtimes]
    assert "transformers_js" in names
    assert "webllm" in names
    assert "onnx_web" in names
    assert "tensorflow_js" in names


def test_browser_ai_get_runtime():
    from ai_generation.browser_ai import BrowserAIManager
    mgr = BrowserAIManager()
    r = mgr.get_runtime("transformers_js")
    assert r is not None
    assert r["runtime"] == "transformers_js"
    assert mgr.get_runtime("nonexistent") is None


def test_browser_ai_list_models():
    from ai_generation.browser_ai import BrowserAIManager
    mgr = BrowserAIManager()
    models = mgr.list_models()
    assert len(models) >= 4
    assert all("model_id" in m for m in models)


def test_browser_ai_list_models_by_category():
    from ai_generation.browser_ai import BrowserAIManager
    mgr = BrowserAIManager()
    llm_models = mgr.list_models(category="llm")
    assert len(llm_models) >= 2
    assert all(m["category"] == "llm" for m in llm_models)


def test_browser_ai_list_models_by_runtime():
    from ai_generation.browser_ai import BrowserAIManager
    mgr = BrowserAIManager()
    webllm_models = mgr.list_models(runtime="webllm")
    assert len(webllm_models) >= 1
    assert all(m["runtime"] == "webllm" for m in webllm_models)


def test_browser_ai_find_models_for_task():
    from ai_generation.browser_ai import BrowserAIManager
    mgr = BrowserAIManager()
    llm_models = mgr.find_models_for_task("text_generation")
    assert len(llm_models) >= 1
    assert all(m["category"] == "llm" for m in llm_models)


def test_browser_ai_select_optimal_runtime():
    from ai_generation.browser_ai import BrowserAIManager
    mgr = BrowserAIManager()
    # For text generation, should prefer transformers_js (broader support)
    runtime = mgr.select_optimal_runtime("text_generation")
    assert runtime is not None
    assert runtime in ["transformers_js", "onnx_web", "webllm"]

    # For offline mobile, should avoid webllm (requires webgpu)
    runtime = mgr.select_optimal_runtime("text_generation", needs_offline=True, needs_mobile=True)
    assert runtime is not None


def test_browser_ai_select_optimal_runtime_no_match():
    from ai_generation.browser_ai import BrowserAIManager
    mgr = BrowserAIManager()
    # Unsupported task type
    runtime = mgr.select_optimal_runtime("video_generation")
    assert runtime is None


def test_browser_ai_generate_transformers_js_template():
    from ai_generation.browser_ai import BrowserAIManager
    mgr = BrowserAIManager()
    tmpl = mgr.generate_inference_template("transformers_js", "text_generation")
    assert "html" in tmpl
    assert "javascript" in tmpl
    assert "transformers" in tmpl["javascript"].lower()
    assert "<!DOCTYPE html>" in tmpl["html"]


def test_browser_ai_generate_webllm_template():
    from ai_generation.browser_ai import BrowserAIManager
    mgr = BrowserAIManager()
    tmpl = mgr.generate_inference_template("webllm", "text_generation")
    assert "html" in tmpl
    assert "javascript" in tmpl
    assert "web-llm" in tmpl["javascript"]


def test_browser_ai_generate_onnx_template():
    from ai_generation.browser_ai import BrowserAIManager
    mgr = BrowserAIManager()
    tmpl = mgr.generate_inference_template("onnx_web", "image_classification")
    assert "html" in tmpl
    assert "onnxruntime" in tmpl["javascript"]


def test_browser_ai_generate_tfjs_template():
    from ai_generation.browser_ai import BrowserAIManager
    mgr = BrowserAIManager()
    tmpl = mgr.generate_inference_template("tensorflow_js", "image_classification")
    assert "html" in tmpl
    assert "tensorflow" in tmpl["javascript"]


def test_browser_ai_generate_unknown_runtime():
    from ai_generation.browser_ai import BrowserAIManager
    mgr = BrowserAIManager()
    tmpl = mgr.generate_inference_template("unknown_runtime", "text_generation")
    assert "error" in tmpl


def test_browser_ai_stats():
    from ai_generation.browser_ai import BrowserAIManager
    mgr = BrowserAIManager()
    stats = mgr.get_stats()
    assert stats["runtime_count"] == 4
    assert stats["model_count"] >= 4
    assert stats["tier"] == 4
    assert "llm" in stats["categories"]


def test_browser_ai_negotiation_candidates():
    from ai_generation.browser_ai import BrowserAIManager
    mgr = BrowserAIManager()
    candidates = mgr.to_negotiation_candidates("text_generation")
    assert len(candidates) >= 1
    assert all(c["layer"] == "browser" for c in candidates)
    assert all(c["tier"] == 4 for c in candidates)
    assert all(c["cost_usd"] == 0.0 for c in candidates)


# ── SDK Integration Tests ─────────────────────────────────────

def test_sdk_browser_ai_import():
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    assert hasattr(ai, 'browser_ai')
    assert hasattr(ai, 'list_browser_runtimes')
    assert hasattr(ai, 'list_browser_models')
    assert hasattr(ai, 'find_browser_models')
    assert hasattr(ai, 'select_browser_runtime')
    assert hasattr(ai, 'generate_browser_template')
    assert hasattr(ai, 'get_browser_ai_stats')


def test_sdk_list_browser_runtimes():
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    runtimes = ai.list_browser_runtimes()
    assert len(runtimes) == 4


def test_sdk_list_browser_models():
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    models = ai.list_browser_models()
    assert len(models) >= 4


def test_sdk_browser_ai_stats():
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    stats = ai.get_browser_ai_stats()
    assert stats["tier"] == 4


def test_sdk_generate_browser_template():
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    tmpl = ai.generate_browser_template("transformers_js", "text_generation")
    assert "html" in tmpl
    assert "javascript" in tmpl


# ── MCP Tools Tests ──────────────────────────────────────────

def test_mcp_browser_ai_tools_exist():
    from ai_generation.mcp_tools import MCP_GENERATION_TOOLS
    assert "list_browser_runtimes" in MCP_GENERATION_TOOLS
    assert "list_browser_models" in MCP_GENERATION_TOOLS
    assert "find_browser_models" in MCP_GENERATION_TOOLS
    assert "select_browser_runtime" in MCP_GENERATION_TOOLS
    assert "generate_browser_template" in MCP_GENERATION_TOOLS
    assert "get_browser_ai_stats" in MCP_GENERATION_TOOLS


def test_mcp_browser_ai_handler_import():
    from ai_generation.mcp_tools import MCPGenerationTools
    handler = MCPGenerationTools()
    assert hasattr(handler, '_handle_list_browser_runtimes')
    assert hasattr(handler, '_handle_list_browser_models')
    assert hasattr(handler, '_handle_find_browser_models')
    assert hasattr(handler, '_handle_select_browser_runtime')
    assert hasattr(handler, '_handle_generate_browser_template')
    assert hasattr(handler, '_handle_get_browser_ai_stats')
