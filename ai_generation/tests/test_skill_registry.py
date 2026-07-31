"""
Tests for the unified Skill Registry (configs/skills.json).
"""
import pytest

from ai_generation.skill_registry import SkillRegistry, get_skill_registry


def test_registry_loads_canonical_config():
    registry = get_skill_registry()
    stats = registry.stats()
    assert stats["total_skills"] >= 70
    assert stats["ready"] >= 70
    assert "quality_gate_runner" in registry._skills


def test_registry_list_and_filters():
    registry = get_skill_registry()
    all_skills = registry.list_skills()
    ids = {s["id"] for s in all_skills}
    for expected in ("quality_gate_runner", "code_review_specialist",
                     "test_generator", "coverage_gap_analyzer",
                     "refactoring_advisor", "image_prompt_enhancer",
                     "video_script_writer", "secret_scanner",
                     "benchmark_runner", "regression_detector",
                     "failure_recovery_operator", "kimi_k3_runtime_operator",
                     "local_runtime_operator", "plugin_developer"):
        assert expected in ids, f"missing skill: {expected}"

    # all objective categories present
    for cat in ("architecture", "refactoring", "testing", "tdd", "security",
                "benchmarking", "profiling", "performance",
                "memory-optimization", "gpu-optimization",
                "distributed-systems", "image-generation", "video-generation",
                "audio-generation", "prompt-engineering", "research",
                "documentation", "dependency-analysis", "code-review",
                "pr-review", "git", "ci-cd", "docker", "kubernetes",
                "python", "typescript", "fastapi", "pytorch", "diffusers",
                "transformers", "onnx", "tensorrt", "mlx", "llama.cpp",
                "comfyui", "forge", "a1111", "sd-next"):
        assert registry.categories().get(cat, 0) >= 1, f"missing category: {cat}"

    blocked = registry.list_skills(status="blocked")
    assert {s["id"] for s in blocked} >= {"sourcery", "gga"}
    found = registry.list_skills(search="quality_gate")
    assert found[0]["id"] == "quality_gate_runner"


def test_registry_entries_truthful():
    registry = get_skill_registry()
    # native skills map to a real module path
    for s in registry.list_skills(source=None) if False else registry.list_skills():
        pass
    native = [s for s in registry.list_skills() if s.get("source") == "internal"]
    for s in native:
        assert s["status"] == "ready"
        assert s["verified"] is True
        assert s.get("module"), f"native skill {s['id']} missing module"
        assert s.get("usage"), f"native skill {s['id']} missing usage"
    for s in registry.list_skills(status="blocked"):
        assert s["note"], f"blocked skill {s['id']} missing note"
    # external reference entries must not claim verification
    for s in registry.list_skills():
        if s.get("source") != "internal" and s.get("status") == "ready":
            assert s["verified"] is False, f"external skill {s['id']} over-claims verification"
            assert s.get("reference") or s.get("usage"), \
                f"external skill {s['id']} missing reference/usage"


def test_native_skills_reference_real_modules():
    import importlib
    registry = get_skill_registry()
    for s in registry.list_skills():
        if s.get("source") != "internal":
            continue
        module_path = s["module"]  # e.g. ai_generation/quality_engineering.py
        module_name = module_path.replace("/", ".").removesuffix(".py")
        importlib.import_module(module_name)
    # also verify SDK surface module exists
    import ai_generation.skill_registry


def test_sdk_skill_registry_surface():
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    skills = ai.list_skills(category="testing")
    assert {s["id"] for s in skills} >= {"test_generator", "coverage_gap_analyzer"}
    assert ai.get_skill("quality_gate_runner")["module"].endswith("quality_engineering.py")
    stats = ai.get_skill_registry_stats()
    assert stats["total_skills"] == ai.skill_registry.stats()["total_skills"]


def test_mcp_tools_skill_registry_exposed():
    from ai_generation.mcp_tools import MCP_GENERATION_TOOLS
    assert "list_skills" in MCP_GENERATION_TOOLS
    assert "get_skill" in MCP_GENERATION_TOOLS


@pytest.mark.asyncio
async def test_mcp_tool_list_skills_handler():
    from ai_generation.mcp_tools import MCPGenerationTools
    tools = MCPGenerationTools()
    result = await tools.handle("list_skills", {"search": "quality_gate"})
    assert result["skills"][0]["id"] == "quality_gate_runner"


@pytest.mark.asyncio
async def test_mcp_tool_get_skill_handler():
    from ai_generation.mcp_tools import MCPGenerationTools
    tools = MCPGenerationTools()
    result = await tools.handle("get_skill", {"skill_id": "benchmark_runner"})
    assert result["skill"]["category"] == "benchmarking"
    missing = await tools.handle("get_skill", {"skill_id": "nope"})
    assert "error" in missing


def test_cli_skills_command(capsys):
    from ai_generation.cli import cmd_skills
    import asyncio
    asyncio.run(cmd_skills(search="benchmark"))
    out = capsys.readouterr().out
    assert "Skill Registry" in out
    assert "benchmark_runner" in out
