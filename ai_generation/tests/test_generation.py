"""
Comprehensive tests for AI Generation Platform.
"""
import asyncio
import pytest
import tempfile
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))


# ── Provider Base Tests ──────────────────────────────────────────

def test_provider_base_import():
    from ai_generation.providers.base import (
        Provider, ImageProvider, VideoProvider, EditProvider,
        ProviderType, ProviderTier, ProviderStatus,
        GenerationResult, ProviderCapability,
    )
    assert ProviderType.IMAGE.value == "image"
    assert ProviderType.VIDEO.value == "video"
    assert ProviderTier.FREE.value == "free"
    assert ProviderStatus.AVAILABLE.value == "available"


def test_generation_result():
    from ai_generation.providers.base import GenerationResult
    r = GenerationResult(provider="test", status="success", latency_ms=100.0)
    assert r.success is True
    d = r.to_dict()
    assert d["provider"] == "test"
    assert d["latency_ms"] == 100.0


def test_generation_result_failure():
    from ai_generation.providers.base import GenerationResult
    r = GenerationResult(provider="test", status="error", error="failed")
    assert r.success is False


def test_provider_stats():
    from ai_generation.providers.base import ImageProvider, ProviderTier, ProviderCapability
    class TestProvider(ImageProvider):
        name = "test_stat"
        tier = ProviderTier.FREE
        requires_api_key = False
        supported_models = ["test-v1"]
        capabilities = [ProviderCapability(name="text_to_image")]
        async def generate_image(self, **kwargs):
            from ai_generation.providers.base import GenerationResult
            return GenerationResult()
    p = TestProvider()
    p.record_success(100.0)
    p.record_success(200.0)
    assert p._success_count == 2
    assert p.avg_latency_ms == 150.0
    assert p.success_rate == 100.0
    stats = p.get_stats()
    assert stats["name"] == "test_stat"
    assert stats["success_count"] == 2


def test_provider_error_tracking():
    from ai_generation.providers.base import ImageProvider, ProviderTier, ProviderStatus, ProviderCapability
    class TestProvider(ImageProvider):
        name = "test_err"
        tier = ProviderTier.FREE
        requires_api_key = False
        supported_models = []
        capabilities = [ProviderCapability(name="text_to_image")]
        async def generate_image(self, **kwargs):
            pass
    p = TestProvider()
    for _ in range(12):
        p.record_error("fail")
    assert p._status == ProviderStatus.UNAVAILABLE


def test_provider_rate_limit():
    from ai_generation.providers.base import ImageProvider, ProviderTier, ProviderStatus, ProviderCapability
    class TestProvider(ImageProvider):
        name = "test_rl"
        tier = ProviderTier.FREE
        requires_api_key = False
        supported_models = []
        capabilities = [ProviderCapability(name="text_to_image")]
        async def generate_image(self, **kwargs):
            pass
    p = TestProvider()
    p.record_error("rate limited", is_rate_limit=True)
    assert p._status == ProviderStatus.RATE_LIMITED


# ── Registry Tests ───────────────────────────────────────────────

def test_registry_auto_discover():
    from ai_generation.providers.registry import get_registry
    registry = get_registry()
    providers = registry.get_all()
    assert len(providers) >= 9


def test_registry_by_type():
    from ai_generation.providers.registry import get_registry
    from ai_generation.providers.base import ProviderType
    registry = get_registry()
    image_providers = registry.get_by_type(ProviderType.IMAGE)
    assert len(image_providers) >= 8
    video_providers = registry.get_by_type(ProviderType.VIDEO)
    assert len(video_providers) >= 1


def test_registry_best_provider():
    from ai_generation.providers.registry import get_registry
    from ai_generation.providers.base import ProviderType
    registry = get_registry()
    best = registry.get_best_provider(ProviderType.IMAGE, prefer_free=True)
    assert best is not None
    assert best.tier.value == "free"


def test_registry_summary():
    from ai_generation.providers.registry import get_registry
    registry = get_registry()
    summary = registry.summary()
    assert summary["total_providers"] >= 9
    assert summary["by_type"]["image"] >= 7
    assert summary["free"] >= 2


# ── Prompt Engine Tests ──────────────────────────────────────────

def test_prompt_enhance():
    from ai_generation.prompt_engine import PromptEngine
    pe = PromptEngine()
    result = pe.enhance("a coffee cup", style="photorealistic")
    assert "coffee cup" in result.enhanced
    assert "photorealistic" in result.enhanced
    assert len(result.negative_prompt) > 0
    assert "style:photorealistic" in result.techniques_applied


def test_prompt_enhance_no_style():
    from ai_generation.prompt_engine import PromptEngine
    pe = PromptEngine()
    result = pe.enhance("a sunset over mountains")
    assert "sunset" in result.enhanced
    assert "high quality" in result.enhanced or "masterpiece" in result.enhanced


def test_prompt_templates():
    from ai_generation.prompt_engine import PromptEngine
    pe = PromptEngine()
    templates = pe.list_templates()
    assert len(templates) >= 6
    names = [t["name"] for t in templates]
    assert "product_showcase" in names
    assert "restaurant_menu" in names
    assert "brand_visual" in names


def test_render_template():
    from ai_generation.prompt_engine import PromptEngine
    pe = PromptEngine()
    result = pe.render_template("restaurant_menu", dish_name="Butter Chicken", cuisine="Indian", presentation="elegant plating", style="food_photo")
    assert "Butter Chicken" in result
    assert "Indian" in result


def test_prompt_analyze():
    from ai_generation.prompt_engine import PromptEngine
    pe = PromptEngine()
    analysis = pe.analyze_prompt("a beautiful sunset over the ocean with dramatic clouds and golden light, photorealistic")
    assert analysis["word_count"] > 10
    assert analysis["complexity"] in ("moderate", "complex")


def test_negative_prompt_generation():
    from ai_generation.prompt_engine import PromptEngine
    pe = PromptEngine()
    neg = pe.generate_negative("a portrait", style="anime", extra_avoid=["nsfw", "violence"])
    assert "low quality" in neg
    assert "nsfw" in neg


def test_prompt_deduplication():
    from ai_generation.prompt_engine import PromptEngine
    pe = PromptEngine()
    result = pe.enhance("test, test, unique")
    assert result.enhanced.count("test") <= 2


# ── Quality Engine Tests ─────────────────────────────────────────

def test_quality_evaluate_generation():
    from ai_generation.quality_engine import QualityEngine
    from ai_generation.providers.base import GenerationResult
    qe = QualityEngine()
    result = GenerationResult(
        provider="test", status="success", output_bytes=b"x" * 100000,
        width=1024, height=1024, latency_ms=5000,
    )
    report = qe.evaluate_generation(result, prompt="a detailed landscape")
    assert report.overall_score > 0
    assert "technical_quality" in report.dimensions


def test_quality_evaluate_prompt():
    from ai_generation.quality_engine import QualityEngine
    qe = QualityEngine()
    report = qe.evaluate_prompt(
        "a highly detailed photorealistic portrait of a woman",
        enhanced="a highly detailed photorealistic portrait of a woman, masterpiece, 8k",
        negative="blurry, low quality",
    )
    assert report.overall_score > 0
    assert "specificity" in report.dimensions


def test_quality_compare_results():
    from ai_generation.quality_engine import QualityEngine
    from ai_generation.providers.base import GenerationResult
    qe = QualityEngine()
    results = [
        GenerationResult(provider="a", status="success", output_bytes=b"x" * 50000, width=1024),
        GenerationResult(provider="b", status="success", output_bytes=b"y" * 20000, width=512),
    ]
    ranked = qe.compare_results(results)
    assert len(ranked) == 2
    assert ranked[0]["score"] >= ranked[1]["score"]


# ── Workflow Engine Tests ────────────────────────────────────────

def test_workflow_create():
    from ai_generation.workflow_engine import WorkflowEngine
    we = WorkflowEngine()
    wf = we.create_workflow("test", [
        {"name": "step1", "action": "enhance_prompt", "params": {"prompt": "test"}},
        {"name": "step2", "action": "evaluate", "params": {}, "depends_on": ["step1"]},
    ])
    assert wf.workflow_id.startswith("wf-")
    assert len(wf.steps) == 2


@pytest.mark.asyncio
async def test_workflow_execute():
    from ai_generation.workflow_engine import WorkflowEngine
    we = WorkflowEngine()
    wf = we.create_workflow("test_exec", [
        {"name": "enhance", "action": "enhance_prompt", "params": {"prompt": "a sunset", "style": "cinematic"}},
        {"name": "eval", "action": "evaluate", "params": {}},
    ])
    result = await we.execute(wf.workflow_id)
    assert result["status"] in ("completed", "partial")
    assert len(result["steps"]) == 2


@pytest.mark.asyncio
async def test_workflow_condition():
    from ai_generation.workflow_engine import WorkflowEngine
    we = WorkflowEngine()
    wf = we.create_workflow("cond_test", [
        {"name": "always", "action": "evaluate", "params": {}},
        {"name": "never", "action": "evaluate", "params": {}, "condition": "False"},
    ])
    result = await we.execute(wf.workflow_id)
    statuses = {s["name"]: s["status"] for s in result["steps"]}
    assert statuses["always"] == "completed"
    assert statuses["never"] == "skipped"


# ── Benchmark Engine Tests ───────────────────────────────────────

def test_benchmark_stats():
    from ai_generation.benchmark_engine import BenchmarkEngine
    be = BenchmarkEngine()
    stats = be.get_stats()
    assert stats["total_benchmarks"] == 0


def test_benchmark_rankings():
    from ai_generation.benchmark_engine import BenchmarkEngine, BenchmarkResult
    be = BenchmarkEngine()
    be._results = [
        BenchmarkResult(provider="a", prompt="test", success=True, latency_ms=1000, output_bytes=50000),
        BenchmarkResult(provider="a", prompt="test", success=True, latency_ms=1500, output_bytes=40000),
        BenchmarkResult(provider="b", prompt="test", success=False, latency_ms=5000, error="fail"),
    ]
    be._update_score("a")
    be._update_score("b")
    rankings = be.get_rankings()
    assert len(rankings) == 2
    assert rankings[0].provider == "a"


# ── Asset Intelligence Tests ─────────────────────────────────────

def test_asset_intelligence():
    from ai_generation.asset_intelligence import AssetIntelligence
    with tempfile.TemporaryDirectory() as tmpdir:
        ai = AssetIntelligence(storage_dir=tmpdir)
        test_file = os.path.join(tmpdir, "test_image.png")
        with open(test_file, "wb") as f:
            f.write(b"fake image data " * 100)
        asset = ai.register_asset(test_file, prompt="a test image", provider="test")
        assert asset.asset_id.startswith("asset-")
        assert asset.file_size > 0
        stats = ai.get_stats()
        assert stats["total_assets"] == 1


def test_asset_search():
    from ai_generation.asset_intelligence import AssetIntelligence
    with tempfile.TemporaryDirectory() as tmpdir:
        ai = AssetIntelligence(storage_dir=tmpdir)
        f1 = os.path.join(tmpdir, "a.png")
        f2 = os.path.join(tmpdir, "b.png")
        with open(f1, "wb") as f:
            f.write(b"data1" * 100)
        with open(f2, "wb") as f:
            f.write(b"data2" * 100)
        ai.register_asset(f1, prompt="sunset photo", provider="pollinations")
        ai.register_asset(f2, prompt="coffee cup", provider="huggingface")
        results = ai.search(query="sunset")
        assert len(results) == 1


def test_asset_duplicates():
    from ai_generation.asset_intelligence import AssetIntelligence
    with tempfile.TemporaryDirectory() as tmpdir:
        ai = AssetIntelligence(storage_dir=tmpdir)
        f1 = os.path.join(tmpdir, "copy1.png")
        f2 = os.path.join(tmpdir, "copy2.png")
        data = b"identical content " * 100
        with open(f1, "wb") as f:
            f.write(data)
        with open(f2, "wb") as f:
            f.write(data)
        ai.register_asset(f1, prompt="test")
        ai.register_asset(f2, prompt="test")
        dups = ai.find_duplicates()
        assert len(dups) == 1
        assert len(dups[0]) == 2


# ── Research Agent Tests ─────────────────────────────────────────

def test_research_known_providers():
    from ai_generation.research_agent import ResearchAgent
    ra = ResearchAgent()
    providers = ra.get_known_providers()
    assert len(providers) >= 9


def test_research_free_providers():
    from ai_generation.research_agent import ResearchAgent
    ra = ResearchAgent()
    free = ra.get_free_providers(provider_type="image")
    assert len(free) >= 3
    for p in free:
        assert p["tier"] == "free"


def test_research_by_type():
    from ai_generation.research_agent import ResearchAgent
    ra = ResearchAgent()
    video = ra.get_known_providers(provider_type="video")
    assert len(video) >= 1


def test_research_stats():
    from ai_generation.research_agent import ResearchAgent
    ra = ResearchAgent()
    stats = ra.get_stats()
    assert stats["total_discoveries"] >= 8
    assert stats["verified"] >= 6


# ── SDK Tests ────────────────────────────────────────────────────

def test_sdk_init():
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    assert ai.list_providers() is not None
    assert len(ai.list_providers()) >= 9


def test_sdk_enhance():
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    result = ai.enhance_prompt("a coffee cup")
    assert "coffee cup" in result.enhanced


def test_sdk_analyze():
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    analysis = ai.analyze_prompt("a detailed sunset with mountains")
    assert "word_count" in analysis


def test_sdk_templates():
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    templates = ai.list_templates()
    assert len(templates) >= 6


def test_sdk_styles():
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    styles = ai.list_styles()
    assert "photorealistic" in styles
    assert "cinematic" in styles
    assert len(styles) >= 10


def test_sdk_stats():
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    stats = ai.get_stats()
    assert "generation" in stats
    assert "prompts" in stats
    assert "quality" in stats


# ── MCP Tools Tests ──────────────────────────────────────────────

def test_mcp_tools_registered():
    from ai_generation.mcp_tools import get_mcp_generation_tools
    tools = get_mcp_generation_tools()
    assert "generate_image" in tools
    assert "generate_video" in tools
    assert "enhance_prompt" in tools
    assert "list_providers" in tools
    assert len(tools) >= 10


@pytest.mark.asyncio
async def test_mcp_enhance():
    from ai_generation.mcp_tools import MCPGenerationTools
    mcp = MCPGenerationTools()
    result = await mcp.handle("enhance_prompt", {"prompt": "a sunset", "style": "cinematic"})
    assert "enhanced" in result
    assert "negative_prompt" in result


@pytest.mark.asyncio
async def test_mcp_list_providers():
    from ai_generation.mcp_tools import MCPGenerationTools
    mcp = MCPGenerationTools()
    result = await mcp.handle("list_providers", {})
    assert "providers" in result
    assert len(result["providers"]) >= 9


@pytest.mark.asyncio
async def test_mcp_list_styles():
    from ai_generation.mcp_tools import MCPGenerationTools
    mcp = MCPGenerationTools()
    result = await mcp.handle("list_styles", {})
    assert "styles" in result
    assert "photorealistic" in result["styles"]


@pytest.mark.asyncio
async def test_mcp_analyze():
    from ai_generation.mcp_tools import MCPGenerationTools
    mcp = MCPGenerationTools()
    result = await mcp.handle("analyze_prompt", {"prompt": "a beautiful sunset"})
    assert "word_count" in result


@pytest.mark.asyncio
async def test_mcp_known_providers():
    from ai_generation.mcp_tools import MCPGenerationTools
    mcp = MCPGenerationTools()
    result = await mcp.handle("get_known_providers", {"tier": "free"})
    assert "providers" in result
    assert len(result["providers"]) >= 2


@pytest.mark.asyncio
async def test_mcp_evaluate():
    from ai_generation.mcp_tools import MCPGenerationTools
    mcp = MCPGenerationTools()
    result = await mcp.handle("evaluate_generation", {"prompt": "a highly detailed photorealistic scene"})
    assert "overall_score" in result


@pytest.mark.asyncio
async def test_mcp_render_template():
    from ai_generation.mcp_tools import MCPGenerationTools
    mcp = MCPGenerationTools()
    result = await mcp.handle("render_template", {
        "template_name": "restaurant_menu",
        "variables": {"dish_name": "Biryani", "cuisine": "Hyderabadi", "presentation": "layered"},
    })
    assert "Biryani" in result["rendered"]
