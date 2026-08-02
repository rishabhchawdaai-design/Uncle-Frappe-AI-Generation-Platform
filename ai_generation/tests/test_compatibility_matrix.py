"""
Tests for the Compatibility Matrix (COMPATIBILITY_MATRIX.md core spec).

Covers the Model x Runtime x Hardware lookup table: seeded matrix data,
lookup with hardware fallback, runtime/model discovery, execution-path
validation (CGR-07), benchmark feedback, refresh schedule, persistence,
and the unified SDK/CLI/MCP surfaces.
"""
import asyncio
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))


@pytest.fixture
def matrix(tmp_path):
    from ai_generation.compatibility_matrix import CompatibilityMatrix
    return CompatibilityMatrix(data_dir=str(tmp_path / "cmat"))


# ── Seeded matrix coverage ──────────────────────────────────────

def test_seed_covers_spec_categories(matrix):
    stats = matrix.get_stats()
    assert stats["total_entries"] >= 150
    assert stats["total_models"] >= 40
    for category in ("llm", "image", "video", "audio", "ocr", "browser", "edge"):
        assert stats["by_category"].get(category, 0) >= 7, f"missing {category} entries"


def test_seed_evidence_classification(matrix):
    stats = matrix.get_stats()
    assert stats["by_evidence"].get("production", 0) >= 100
    assert stats["by_evidence"].get("research", 0) >= 20


def test_runtime_catalog(matrix):
    runtimes = {r["runtime_id"]: r for r in matrix.list_runtimes()}
    for rid in ("vllm", "sglang", "tensorrt_llm", "llama_cpp", "ollama", "tgi",
                "onnx_rt", "deepspeed", "diffusers", "comfyui", "whisper_py",
                "piper", "tesseract", "paddleocr", "transformers_js", "webllm",
                "openvino", "tflite", "coreml", "snpe", "tensorrt_edge"):
        assert rid in runtimes, f"missing runtime {rid}"
    assert "tensor" in runtimes["vllm"]["parallel"]
    assert "nvidia" in runtimes["vllm"]["hardware"]


# ── Lookup ──────────────────────────────────────────────────────

def test_lookup_exact(matrix):
    entry = matrix.lookup("llama3_8b", "vllm", "nvidia")
    assert entry is not None
    assert entry["performance_score"] > 0.8


def test_lookup_hardware_fallback(matrix):
    entry = matrix.lookup("llama3_8b", "llama_cpp", "apple_silicon")
    assert entry is not None
    assert entry["inherited"] is True
    assert entry["hardware_id"] == "apple_silicon"


def test_lookup_missing(matrix):
    assert matrix.lookup("nonexistent_model", "vllm") is None
    assert matrix.lookup("llama3_8b", "nonexistent_runtime") is None


def test_lookup_incompatible_combination(matrix):
    # FLUX.1-dev is NVIDIA-only per the spec; no CPU/llama.cpp entry
    assert matrix.lookup("flux_1_dev", "llama_cpp") is None


# ── Discovery ───────────────────────────────────────────────────

def test_find_runtimes_sorted_by_score(matrix):
    results = matrix.find_runtimes("llama3_8b")
    scores = [r["performance_score"] for r in results]
    assert scores == sorted(scores, reverse=True)
    assert len(results) >= 7
    assert results[0]["runtime_id"] in ("vllm", "tensorrt_llm", "tgi", "sglang")


def test_find_runtimes_hardware_filter(matrix):
    results = matrix.find_runtimes("llama3_8b", hardware_id="nvidia")
    assert results
    assert all(r["hardware_id"] in ("nvidia", "all") for r in results)


def test_find_models_category(matrix):
    video = matrix.find_models("video")
    assert video
    assert all(r["runtime_id"].startswith(("diffusers_video", "comfyui_video", "custom_video"))
               for r in video)
    assert video[0]["model_id"] == "open_sora"


def test_find_models_min_score(matrix):
    results = matrix.find_models("llm", min_score=0.9)
    assert results
    assert all(r["performance_score"] >= 0.9 for r in results)


# ── Path validation (CGR-07) ────────────────────────────────────

def test_validate_path_valid(matrix):
    result = matrix.validate_path("cogvideox_5b", "comfyui_video", "nvidia")
    assert result["valid"] is True
    assert result["reason"] == "compatible"


def test_validate_path_unregistered(matrix):
    result = matrix.validate_path("flux_1_dev", "llama_cpp")
    assert result["valid"] is False
    assert result["reason"] == "combination not registered"


# ── Benchmark feedback + refresh ────────────────────────────────

def test_update_score_clamps_and_persists(matrix):
    result = matrix.update_score("llama3_8b", "vllm", "nvidia", 1.7)
    assert result["updated"] is True
    assert result["entry"]["performance_score"] == 1.0
    # persistence: fresh instance from same dir sees the score
    from ai_generation.compatibility_matrix import CompatibilityMatrix
    reloaded = CompatibilityMatrix(data_dir=matrix.data_dir)
    assert reloaded.lookup("llama3_8b", "vllm", "nvidia")["performance_score"] == 1.0


def test_refresh_due(matrix):
    from datetime import datetime, timedelta, timezone
    from ai_generation.compatibility_matrix import CompatibilityEntry
    # fresh entries are not due within the refresh window
    assert matrix.refresh_due(max_age_days=90) == []
    # an entry verified 100 days ago is due for re-verification
    old_date = (datetime.now(timezone.utc) - timedelta(days=100)).date().isoformat()
    matrix.register(CompatibilityEntry(
        model_id="old_model", runtime_id="vllm", hardware_id="nvidia",
        performance_score=0.8, verified_date=old_date,
        evidence="production"))
    due = matrix.refresh_due(max_age_days=90)
    assert any(e["model_id"] == "old_model" for e in due)


# ── Persistence ─────────────────────────────────────────────────

def test_persist_and_reload(tmp_path):
    from ai_generation.compatibility_matrix import CompatibilityMatrix
    m1 = CompatibilityMatrix(data_dir=str(tmp_path / "p"))
    n1 = m1.get_stats()["total_entries"]
    m2 = CompatibilityMatrix(data_dir=str(tmp_path / "p"))
    assert m2.get_stats()["total_entries"] == n1
    assert (tmp_path / "p" / "compatibility_matrix.json").exists()


# ── SDK / CLI / MCP integration ─────────────────────────────────

def test_sdk_compat_surfaces(tmp_path, monkeypatch):
    monkeypatch.setenv("ACOS_DATA_DIR", str(tmp_path / "sdk_cmat"))
    from ai_generation import UncleFrappeAI
    ai = UncleFrappeAI()
    assert ai.compat_get_stats()["total_entries"] >= 150
    entry = ai.compat_lookup("sdxl", "comfyui", "nvidia")
    assert entry is not None and entry["performance_score"] > 0.8
    assert ai.compat_validate_path("sdxl", "comfyui", "nvidia")["valid"] is True
    assert ai.compat_validate_path("sdxl", "llama_cpp")["valid"] is False
    runtimes = ai.compat_find_runtimes("sdxl")
    assert runtimes and runtimes[0]["runtime_id"] == "tensorrt_image"
    models = ai.compat_find_models("ocr")
    assert models
    assert ai.compat_list_runtimes("browser")


def test_cli_compat_commands(capsys, tmp_path, monkeypatch):
    monkeypatch.setenv("ACOS_DATA_DIR", str(tmp_path / "cli_cmat"))
    import ai_generation.cli as cli

    asyncio.run(cli.cmd_compat_stats())
    out = capsys.readouterr().out
    assert "Compatibility Matrix" in out and "Entries:" in out

    asyncio.run(cli.cmd_compat_validate("sd_1_5", "comfyui", "cpu"))
    out = capsys.readouterr().out
    assert "[VALID]" in out

    asyncio.run(cli.cmd_compat_lookup("llama3_8b", "vllm", "nvidia"))
    out = capsys.readouterr().out
    assert "Score:" in out

    asyncio.run(cli.cmd_compat_runtimes("llama3_8b"))
    out = capsys.readouterr().out
    assert "vllm" in out

    asyncio.run(cli.cmd_compat_models("video"))
    out = capsys.readouterr().out
    assert "open_sora" in out


def test_mcp_compat_tools(tmp_path, monkeypatch):
    monkeypatch.setenv("ACOS_DATA_DIR", str(tmp_path / "mcp_cmat"))
    from ai_generation.mcp_tools import MCPGenerationTools, MCP_GENERATION_TOOLS
    for tool in ("compatibility_lookup", "compatibility_find_runtimes",
                 "compatibility_find_models", "compatibility_validate_path",
                 "compatibility_stats"):
        assert tool in MCP_GENERATION_TOOLS

    tools = MCPGenerationTools()
    result = asyncio.run(tools.handle("compatibility_validate_path", {
        "model_id": "cogvideox_5b", "runtime_id": "comfyui_video",
        "hardware_id": "nvidia"}))
    assert result["valid"] is True
    stats = asyncio.run(tools.handle("compatibility_stats", {}))
    assert stats["total_entries"] >= 150
    lookup = asyncio.run(tools.handle("compatibility_lookup", {
        "model_id": "piper_v2", "runtime_id": "piper"}))
    assert lookup["performance_score"] > 0.8


# ── Research traceability ───────────────────────────────────────

def test_research_links_for_cgr04_cgr07(tmp_path):
    from ai_generation.research_integration import ResearchIntegrationEngine
    engine = ResearchIntegrationEngine(data_dir=str(tmp_path / "ri"))
    index = engine.build_index()
    for cap_id in ("CGR-04", "CGR-07"):
        links = index["capability_links"].get(cap_id, {})
        assert "compatibility_matrix" in links.get("modules", []), cap_id
        assert "capability_graph" in links.get("modules", []), cap_id
    trace = engine.trace_capability("CGR-07")
    assert trace is not None
    assert "compatibility_matrix" in trace.modules
