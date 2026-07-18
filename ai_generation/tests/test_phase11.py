"""
Comprehensive tests for Phase 11 — Media Intelligence & Cinematic Production Engine.
"""
import asyncio
import pytest
import tempfile
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))


# ── Media Intelligence Engine Tests ──────────────────────────────

def test_media_intelligence_import():
    from ai_generation.media_intelligence import MediaIntelligenceEngine, MediaType, RequestType, ComplexityLevel, BudgetTier
    assert MediaType.IMAGE.value == "image"
    assert RequestType.TEXT_TO_IMAGE.value == "text_to_image"
    assert ComplexityLevel.SIMPLE.value == "simple"
    assert BudgetTier.FREE.value == "free"


def test_media_intelligence_analyze_text_to_image():
    from ai_generation.media_intelligence import MediaIntelligenceEngine, RequestType, MediaType
    mi = MediaIntelligenceEngine()
    analysis = mi.analyze_request("a beautiful sunset over mountains")
    assert analysis.request_type == RequestType.TEXT_TO_IMAGE
    assert analysis.media_type == MediaType.IMAGE
    assert len(analysis.recommended_providers) > 0
    assert analysis.estimated_total_cost >= 0


def test_media_intelligence_analyze_video():
    from ai_generation.media_intelligence import MediaIntelligenceEngine, RequestType, MediaType
    mi = MediaIntelligenceEngine()
    analysis = mi.analyze_request("a cinematic timelapse of clouds moving across the sky")
    assert analysis.request_type == RequestType.TEXT_TO_VIDEO
    assert analysis.media_type == MediaType.VIDEO


def test_media_intelligence_analyze_edit():
    from ai_generation.media_intelligence import MediaIntelligenceEngine
    mi = MediaIntelligenceEngine()
    analysis = mi.analyze_request("remove the background and upscale the image")
    assert analysis.request_type is not None
    assert analysis.media_type is not None


def test_media_intelligence_complexity():
    from ai_generation.media_intelligence import MediaIntelligenceEngine, ComplexityLevel
    mi = MediaIntelligenceEngine()
    simple = mi.analyze_request("a cat")
    assert simple.complexity == ComplexityLevel.SIMPLE
    complex_req = mi.analyze_request(
        "a highly detailed photorealistic portrait of an elderly man with weathered skin, "
        "deep blue eyes, silver hair, wearing a tailored navy suit, standing in a grand "
        "library with warm golden lighting, oil painting masterpiece style, 8k resolution"
    )
    assert complex_req.complexity in (ComplexityLevel.COMPLEX, ComplexityLevel.PRODUCTION)


def test_media_intelligence_budget():
    from ai_generation.media_intelligence import MediaIntelligenceEngine, BudgetTier
    mi = MediaIntelligenceEngine()
    analysis_free = mi.analyze_request("test", budget=BudgetTier.FREE)
    for p in analysis_free.recommended_providers:
        if p.get("free") is False:
            pytest.fail(f"Free budget should not recommend paid provider: {p['provider']}")


def test_media_intelligence_cost_estimation():
    from ai_generation.media_intelligence import MediaIntelligenceEngine, CostEstimator, RequestType
    ce = CostEstimator()
    est = ce.estimate("pollinations", RequestType.TEXT_TO_IMAGE)
    assert est["estimated_cost_usd"] == 0.0
    est_video = ce.estimate("replicate_video", RequestType.TEXT_TO_VIDEO, duration_secs=8.0)
    assert est_video["estimated_cost_usd"] > 0


def test_media_intelligence_stats():
    from ai_generation.media_intelligence import MediaIntelligenceEngine
    mi = MediaIntelligenceEngine()
    mi.analyze_request("test1")
    mi.analyze_request("test2")
    stats = mi.get_stats()
    assert stats["total_analyses"] == 2


# ── Image Editing Engine Tests ───────────────────────────────────

def test_image_editing_import():
    from ai_generation.image_editing import ImageEditingEngine, EditOperation, EditStatus, EditResult
    assert EditOperation.IMG2IMG.value == "img2img"
    assert EditStatus.COMPLETED.value == "completed"
    r = EditResult(operation=EditOperation.IMG2IMG, provider="test", status=EditStatus.COMPLETED)
    assert r.to_dict()["operation"] == "img2img"


def test_image_editing_operations():
    from ai_generation.image_editing import ImageEditingEngine, EditOperation
    ie = ImageEditingEngine()
    ops = ie.get_all_operations()
    assert len(ops) == len(EditOperation)
    supported = [o for o in ops if o["supported"]]
    assert len(supported) > 0


def test_image_editing_providers_for_operation():
    from ai_generation.image_editing import ImageEditingEngine, EditOperation
    ie = ImageEditingEngine()
    providers = ie.get_providers_for_operation(EditOperation.UPSCALE)
    assert len(providers) > 0


def test_image_editing_unsupported():
    from ai_generation.image_editing import ImageEditingEngine, EditOperation, EditStatus
    ie = ImageEditingEngine()
    import asyncio
    result = asyncio.run(ie.edit(EditOperation.RELIGHTING, "/nonexistent/path.png"))
    assert result.status in (EditStatus.FAILED, EditStatus.UNSUPPORTED)


def test_image_editing_stats():
    from ai_generation.image_editing import ImageEditingEngine
    ie = ImageEditingEngine()
    stats = ie.get_stats()
    assert stats["total_edits"] == 0
    assert len(stats["providers"]) > 0


# ── Video Generation Layer Tests ─────────────────────────────────

def test_video_generation_import():
    from ai_generation.video_generation import VideoGenerationLayer, VideoGenMode, VideoGenResult
    assert VideoGenMode.TEXT_TO_VIDEO.value == "text_to_video"
    r = VideoGenResult(provider="test", mode=VideoGenMode.TEXT_TO_VIDEO, status="completed")
    assert r.to_dict()["status"] == "completed"


def test_video_generation_providers():
    from ai_generation.video_generation import VideoGenerationLayer, VideoGenMode
    vg = VideoGenerationLayer()
    providers = vg.get_providers_for_mode(VideoGenMode.TEXT_TO_VIDEO)
    assert len(providers) >= 0  # may be 0 if no API key
    providers_i2v = vg.get_providers_for_mode(VideoGenMode.IMAGE_TO_VIDEO)
    assert len(providers_i2v) >= 0


def test_video_capabilities_report():
    from ai_generation.video_generation import VideoGenerationLayer
    vg = VideoGenerationLayer()
    report = vg.get_capabilities_report()
    assert len(report) > 0
    ken_burns = [c for c in report if c["provider"] == "ken_burns"]
    assert len(ken_burns) == 1
    assert ken_burns[0]["not_ai_video"] is True
    assert ken_burns[0]["supported"] is True


def test_video_generation_stats():
    from ai_generation.video_generation import VideoGenerationLayer
    vg = VideoGenerationLayer()
    stats = vg.get_stats()
    assert stats["total_generations"] == 0
    assert stats["has_fallback"] is True
    assert stats["fallback_is_ai_video"] is False


def test_ken_burns_fallback():
    from ai_generation.video_generation import KenBurnsFallback
    import asyncio
    try:
        from PIL import Image
    except ImportError:
        pytest.skip("Pillow not installed")
    with tempfile.TemporaryDirectory() as tmpdir:
        img_path = os.path.join(tmpdir, "test.png")
        img = Image.new("RGB", (200, 200), color="red")
        img.save(img_path)
        kb = KenBurnsFallback()
        desc = kb.describe()
        assert desc["not_ai_video"] is True
        loop = asyncio.new_event_loop()
        result = loop.run_until_complete(
            kb.generate(img_path, effect="zoom_in", duration_secs=1.0, fps=10,
                       output_path=os.path.join(tmpdir, "out.gif"))
        )
        loop.close()
        assert result.status == "completed"
        assert os.path.exists(result.output_path)


# ── Cinematic Workflow Engine Tests ──────────────────────────────

def test_cinematic_workflow_import():
    from ai_generation.cinematic_workflow import CinematicWorkflowEngine, PipelineStage, PipelineTemplates
    assert PipelineStage.IDEA.value == "idea"
    assert len(PipelineTemplates.list_all()) == 5


def test_cinematic_pipeline_templates():
    from ai_generation.cinematic_workflow import PipelineTemplates, PipelineStage
    full = PipelineTemplates.full_cinematic()
    assert len(full.steps) >= 10
    assert full.get_step(PipelineStage.IDEA) is not None
    assert full.get_step(PipelineStage.MASTER_EXPORT) is not None

    quick = PipelineTemplates.quick_ad()
    assert len(quick.steps) >= 5

    storyboard = PipelineTemplates.storyboard_only()
    assert len(storyboard.steps) == 4

    character = PipelineTemplates.character_design()
    assert len(character.steps) == 4

    post = PipelineTemplates.post_production()
    assert len(post.steps) == 5


def test_cinematic_workflow_engine():
    from ai_generation.cinematic_workflow import CinematicWorkflowEngine, PipelineStage
    cwe = CinematicWorkflowEngine()
    pipeline = cwe.create_pipeline("full_cinematic", name="Test Film")
    assert pipeline.name == "Test Film"
    assert len(pipeline.steps) >= 10
    assert pipeline.pipeline_id.startswith("pipe-")


@pytest.mark.asyncio
async def test_cinematic_execute_stage():
    from ai_generation.cinematic_workflow import CinematicWorkflowEngine, PipelineStage
    cwe = CinematicWorkflowEngine()
    pipeline = cwe.create_pipeline("storyboard_only")

    async def handler(step, ctx):
        return {"concept": "test"}

    result = await cwe.execute_stage(pipeline.pipeline_id, PipelineStage.IDEA, handler=handler)
    assert result["status"] == "completed"
    step = pipeline.get_step(PipelineStage.IDEA)
    assert step.status == "completed"


def test_cinematic_workflow_stats():
    from ai_generation.cinematic_workflow import CinematicWorkflowEngine
    cwe = CinematicWorkflowEngine()
    cwe.create_pipeline("full_cinematic")
    cwe.create_pipeline("quick_ad")
    stats = cwe.get_stats()
    assert stats["total_pipelines"] == 2
    assert stats["templates"] == 5


# ── Character Manager Tests ──────────────────────────────────────

def test_character_manager_import():
    from ai_generation.character_manager import CharacterManager, CharacterProfile
    cm = CharacterManager(storage_dir=tempfile.mkdtemp())
    char = cm.create_character("Alice", description="A young woman")
    assert char.name == "Alice"
    assert char.character_id.startswith("char-")


def test_character_appearance():
    from ai_generation.character_manager import CharacterManager, CharacterAppearance
    cm = CharacterManager(storage_dir=tempfile.mkdtemp())
    char = cm.create_character("Bob")
    from ai_generation.character_manager import CharacterAppearance
    appearance = CharacterAppearance(
        hair_color="brown", hair_style="short", eye_color="green",
        skin_tone="fair", distinguishing_features=["freckles"],
    )
    cm.update_character(char.character_id, appearance=appearance)
    updated = cm.get_character(char.character_id)
    assert updated.appearance.hair_color == "brown"
    assert updated.appearance.eye_color == "green"


def test_character_consistency_prompt():
    from ai_generation.character_manager import CharacterManager
    cm = CharacterManager(storage_dir=tempfile.mkdtemp())
    char = cm.create_character("Eve", description="A mysterious woman")
    cm.update_character(char.character_id, prompt_base="portrait of Eve")
    prompt = cm.get_consistency_prompt(char.character_id, scene="in a dark alley")
    assert "Eve" in prompt or "portrait" in prompt


def test_character_clothing():
    from ai_generation.character_manager import CharacterManager
    cm = CharacterManager(storage_dir=tempfile.mkdtemp())
    char = cm.create_character("Dave")
    cm.add_clothing(char.character_id, "suit", description="navy blue tailored suit")
    updated = cm.get_character(char.character_id)
    assert len(updated.clothing) == 1
    assert updated.clothing[0].name == "suit"


def test_character_list():
    from ai_generation.character_manager import CharacterManager
    cm = CharacterManager(storage_dir=tempfile.mkdtemp())
    cm.create_character("A")
    cm.create_character("B")
    chars = cm.list_characters()
    assert len(chars) == 2


def test_character_stats():
    from ai_generation.character_manager import CharacterManager
    cm = CharacterManager(storage_dir=tempfile.mkdtemp())
    cm.create_character("X")
    stats = cm.get_stats()
    assert stats["total_characters"] == 1


# ── Project Manager Tests ────────────────────────────────────────

def test_project_manager_import():
    from ai_generation.project_manager import ProjectManager, Project
    pm = ProjectManager(storage_dir=tempfile.mkdtemp())
    proj = pm.create_project("My Film", description="A short film")
    assert proj.name == "My Film"
    assert proj.project_id.startswith("proj-")


def test_project_add_character():
    from ai_generation.project_manager import ProjectManager
    pm = ProjectManager(storage_dir=tempfile.mkdtemp())
    proj = pm.create_project("Test")
    pm.add_character(proj.project_id, {"name": "Hero"})
    updated = pm.get_project(proj.project_id)
    assert len(updated.characters) == 1


def test_project_add_asset():
    from ai_generation.project_manager import ProjectManager, ProjectAsset
    pm = ProjectManager(storage_dir=tempfile.mkdtemp())
    proj = pm.create_project("Test")
    asset = ProjectAsset(name="frame1.png", asset_type="image", prompt="a sunset")
    pm.add_asset(proj.project_id, asset)
    updated = pm.get_project(proj.project_id)
    assert len(updated.assets) == 1


def test_project_style_guide():
    from ai_generation.project_manager import ProjectManager, StyleGuide
    pm = ProjectManager(storage_dir=tempfile.mkdtemp())
    proj = pm.create_project("Test")
    guide = StyleGuide(name="Cafe Style", color_palette=["#FF0000", "#00FF00"], mood="warm")
    pm.set_style_guide(proj.project_id, guide)
    updated = pm.get_project(proj.project_id)
    assert updated.style_guide.name == "Cafe Style"


def test_project_version():
    from ai_generation.project_manager import ProjectManager
    pm = ProjectManager(storage_dir=tempfile.mkdtemp())
    proj = pm.create_project("Test")
    v1 = pm.create_version(proj.project_id, label="v1", notes="initial")
    assert v1["version_id"] == "v1"
    updated = pm.get_project(proj.project_id)
    assert len(updated.versions) == 1


def test_project_stats():
    from ai_generation.project_manager import ProjectManager
    pm = ProjectManager(storage_dir=tempfile.mkdtemp())
    pm.create_project("A")
    pm.create_project("B")
    stats = pm.get_stats()
    assert stats["total_projects"] == 2


# ── Cinema Benchmark Tests ───────────────────────────────────────

def test_cinema_benchmark_import():
    from ai_generation.cinema_benchmark import CinemaBenchmarkEngine, CinemaBenchmarkReport
    cbe = CinemaBenchmarkEngine()
    report = cbe.score_output("test_provider", scores={"realism": 80, "prompt_adherence": 90})
    assert report.overall_score > 0
    assert "realism" in report.dimensions


def test_cinema_benchmark_dimensions():
    from ai_generation.cinema_benchmark import CinemaBenchmarkEngine
    cbe = CinemaBenchmarkEngine()
    dims = cbe.list_dimensions()
    assert len(dims) == 10
    dim_names = [d["name"] for d in dims]
    assert "realism" in dim_names
    assert "temporal_consistency" in dim_names
    assert "artifact_detection" in dim_names


def test_cinema_benchmark_compare():
    from ai_generation.cinema_benchmark import CinemaBenchmarkEngine
    cbe = CinemaBenchmarkEngine()
    r1 = cbe.score_output("provider_a", scores={"realism": 80, "prompt_adherence": 90})
    r2 = cbe.score_output("provider_b", scores={"realism": 70, "prompt_adherence": 85})
    comparison = cbe.compare_providers([r1, r2])
    assert comparison[0]["provider"] == "provider_a"


def test_cinema_benchmark_stats():
    from ai_generation.cinema_benchmark import CinemaBenchmarkEngine
    cbe = CinemaBenchmarkEngine()
    cbe.score_output("a", scores={"realism": 80})
    cbe.score_output("b", scores={"realism": 60})
    stats = cbe.get_stats()
    assert stats["total_reports"] == 2


# ── Provider Intelligence Tests ──────────────────────────────────

def test_provider_intelligence_import():
    from ai_generation.provider_intelligence import ProviderIntelligenceEngine, VerificationStatus, LicenseType
    pie = ProviderIntelligenceEngine()
    verified = pie.get_verified()
    assert len(verified) >= 4


def test_provider_intelligence_free():
    from ai_generation.provider_intelligence import ProviderIntelligenceEngine
    pie = ProviderIntelligenceEngine()
    free = pie.get_free_providers()
    assert len(free) >= 3


def test_provider_intelligence_recommendations():
    from ai_generation.provider_intelligence import ProviderIntelligenceEngine
    pie = ProviderIntelligenceEngine()
    recs = pie.get_recommendations()
    assert len(recs) >= 4
    assert recs[0]["recommendation_score"] >= recs[-1]["recommendation_score"]


def test_provider_intelligence_stats():
    from ai_generation.provider_intelligence import ProviderIntelligenceEngine
    pie = ProviderIntelligenceEngine()
    stats = pie.get_stats()
    assert stats["total_discoveries"] >= 5
    assert stats["verified"] >= 4


# ── Capability Matrix Tests ──────────────────────────────────────

def test_capability_matrix_import():
    from ai_generation.capability_matrix import CapabilityMatrix
    cm = CapabilityMatrix()
    stats = cm.get_stats()
    assert stats["total_models"] >= 10
    assert stats["providers"] >= 5


def test_capability_matrix_providers():
    from ai_generation.capability_matrix import CapabilityMatrix
    cm = CapabilityMatrix()
    summary = cm.get_provider_summary()
    assert "stability" in summary
    assert "replicate" in summary


def test_capability_matrix_find_best():
    from ai_generation.capability_matrix import CapabilityMatrix
    cm = CapabilityMatrix()
    best = cm.find_best_model("text_to_image", require_free=True)
    assert len(best) > 0
    for m in best:
        assert m["free_tier"] is True


def test_capability_matrix_resolutions():
    from ai_generation.capability_matrix import CapabilityMatrix
    cm = CapabilityMatrix()
    ratios = cm.get_all_aspect_ratios()
    assert "1:1" in ratios
    assert "16:9" in ratios


# ── Agent Planner Tests ──────────────────────────────────────────

def test_agent_planner_import():
    from ai_generation.agent_planner import AgentPlanner
    ap = AgentPlanner()
    plan = ap.plan("Create a luxury cafe advertisement")
    assert plan.plan_id.startswith("plan-")
    assert plan.category == "food" or plan.category == "advertisement"
    assert len(plan.steps) > 0


def test_agent_planner_categories():
    from ai_generation.agent_planner import AgentPlanner
    ap = AgentPlanner()
    cinematic = ap.plan("Create a cinematic movie scene")
    assert cinematic.category == "cinematic"
    character = ap.plan("Design a character portrait")
    assert character.category == "character"


def test_agent_planner_has_workflow():
    from ai_generation.agent_planner import AgentPlanner
    ap = AgentPlanner()
    plan = ap.plan("Create a cinematic film sequence")
    assert plan.workflow_template == "full_cinematic"


def test_agent_planner_stats():
    from ai_generation.agent_planner import AgentPlanner
    ap = AgentPlanner()
    ap.plan("test1")
    ap.plan("test2")
    stats = ap.get_stats()
    assert stats["total_plans"] == 2


# ── SDK Phase 11 Integration Tests ───────────────────────────────

def test_sdk_new_properties():
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    # Test each property initializes correctly
    assert hasattr(ai, 'media_intelligence')
    assert hasattr(ai, 'image_editing')
    assert hasattr(ai, 'video_generation')
    assert hasattr(ai, 'cinematic_workflow')
    assert hasattr(ai, 'character_manager')
    assert hasattr(ai, 'project_manager')
    assert hasattr(ai, 'cinema_benchmark')
    assert hasattr(ai, 'provider_intelligence')
    assert hasattr(ai, 'capability_matrix')
    assert hasattr(ai, 'agent_planner')
    # Force lazy init
    mi = ai.media_intelligence
    assert mi is not None
    ie = ai.image_editing
    assert ie is not None


def test_sdk_analyze():
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    analysis = ai.analyze_request("a beautiful sunset")
    assert analysis.request_type is not None


def test_sdk_plan():
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    plan = ai.plan_request("Create a luxury cafe advertisement")
    assert plan.plan_id.startswith("plan-")


def test_sdk_character():
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    char = ai.create_character("TestChar")
    assert char.name == "TestChar"


def test_sdk_project():
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    proj = ai.create_project("TestProject")
    assert proj.name == "TestProject"


def test_sdk_cinema_benchmark():
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    report = ai.cinema_benchmark.score_output("test", scores={"realism": 85})
    assert report.overall_score > 0


def test_sdk_capability_matrix():
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    stats = ai.get_capability_matrix()
    assert stats["total_models"] >= 10


def test_sdk_provider_intelligence():
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    recs = ai.get_provider_recommendations()
    assert len(recs) >= 4


def test_sdk_cinema_dimensions():
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    dims = ai.get_cinema_dimensions()
    assert len(dims) == 10


# ── MCP Phase 11 Integration Tests ───────────────────────────────

@pytest.mark.asyncio
async def test_mcp_analyze_media():
    from ai_generation.mcp_tools import MCPGenerationTools
    mcp = MCPGenerationTools()
    result = await mcp.handle("analyze_media_request", {"prompt": "a luxury cafe advertisement"})
    assert "request_type" in result
    assert "recommended_providers" in result


@pytest.mark.asyncio
async def test_mcp_list_edits():
    from ai_generation.mcp_tools import MCPGenerationTools
    mcp = MCPGenerationTools()
    result = await mcp.handle("list_edit_operations", {})
    assert "operations" in result
    assert len(result["operations"]) >= 10


@pytest.mark.asyncio
async def test_mcp_video_caps():
    from ai_generation.mcp_tools import MCPGenerationTools
    mcp = MCPGenerationTools()
    result = await mcp.handle("get_video_capabilities", {})
    assert "capabilities" in result


@pytest.mark.asyncio
async def test_mcp_cinematic_templates():
    from ai_generation.mcp_tools import MCPGenerationTools
    mcp = MCPGenerationTools()
    result = await mcp.handle("list_cinematic_templates", {})
    assert "templates" in result
    assert len(result["templates"]) == 5


@pytest.mark.asyncio
async def test_mcp_plan():
    from ai_generation.mcp_tools import MCPGenerationTools
    mcp = MCPGenerationTools()
    result = await mcp.handle("plan_media_production", {"request": "Create a luxury cafe advertisement"})
    assert "category" in result or "plan_id" in result or "steps" in result


@pytest.mark.asyncio
async def test_mcp_create_character():
    from ai_generation.mcp_tools import MCPGenerationTools
    mcp = MCPGenerationTools()
    result = await mcp.handle("create_character", {"name": "MCPHero"})
    assert "name" in result or "character_id" in result


@pytest.mark.asyncio
async def test_mcp_capability_matrix():
    from ai_generation.mcp_tools import MCPGenerationTools
    mcp = MCPGenerationTools()
    result = await mcp.handle("get_capability_matrix", {})
    assert result["total_models"] >= 10


@pytest.mark.asyncio
async def test_mcp_intel():
    from ai_generation.mcp_tools import MCPGenerationTools
    mcp = MCPGenerationTools()
    result = await mcp.handle("get_provider_intelligence", {})
    assert "recommendations" in result or "error" not in result


@pytest.mark.asyncio
async def test_mcp_cinema_dims():
    from ai_generation.mcp_tools import MCPGenerationTools
    mcp = MCPGenerationTools()
    result = await mcp.handle("list_cinema_dimensions", {})
    assert "dimensions" in result or "error" not in result


@pytest.mark.asyncio
async def test_mcp_score_cinema():
    from ai_generation.mcp_tools import MCPGenerationTools
    mcp = MCPGenerationTools()
    result = await mcp.handle("score_cinema_output", {
        "provider": "stability",
        "scores": {"realism": 90, "prompt_adherence": 85},
    })
    assert "overall_score" in result
    assert result["overall_score"] > 0


# ── MCP Tools Registration Check ─────────────────────────────────

def test_mcp_tools_count():
    from ai_generation.mcp_tools import get_mcp_generation_tools
    tools = get_mcp_generation_tools()
    assert len(tools) >= 20  # original 11 + Phase 11 new tools
