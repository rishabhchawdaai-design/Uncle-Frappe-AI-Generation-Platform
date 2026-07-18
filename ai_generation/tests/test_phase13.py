"""
Comprehensive tests for Phase 13 — Agent-Native Remote Execution Platform.
"""
import asyncio
import pytest
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))


# ── Execution Engine Tests ───────────────────────────────────────

def test_execution_engine_import():
    from ai_generation.execution_engine import (
        ExecutionEngine, ExecutionLayer, TaskType, ExecutionStatus,
        ExecutionTask, ExecutionResult, ProviderEndpoint, ExecutionRouter,
    )
    assert ExecutionLayer.PUBLIC_API.value == 1
    assert TaskType.TEXT_TO_IMAGE.value == "text_to_image"
    assert ExecutionStatus.COMPLETED.value == "completed"


def test_execution_engine_endpoints():
    from ai_generation.execution_engine import ExecutionEngine
    ee = ExecutionEngine()
    ee.initialize()
    endpoints = ee.get_all_endpoints()
    assert len(endpoints) >= 8  # 8 public API + 1 hosted


def test_execution_engine_layer_endpoints():
    from ai_generation.execution_engine import ExecutionEngine, ExecutionLayer
    ee = ExecutionEngine()
    ee.initialize()
    api_eps = ee.get_layer_endpoints(ExecutionLayer.PUBLIC_API)
    assert len(api_eps) >= 8
    hosted_eps = ee.get_layer_endpoints(ExecutionLayer.HOSTED_OPENSOURCE)
    assert len(hosted_eps) >= 1


def test_execution_engine_router():
    from ai_generation.execution_engine import ExecutionRouter, ProviderEndpoint, ExecutionLayer, TaskType
    router = ExecutionRouter()
    ep = ProviderEndpoint(
        name="test", layer=ExecutionLayer.PUBLIC_API,
        supported_tasks=[TaskType.TEXT_TO_IMAGE],
        healthy=True, free_tier=True,
    )
    router.register_endpoint(ep)
    candidates = router.get_endpoints_for_task(TaskType.TEXT_TO_IMAGE)
    assert len(candidates) == 1
    assert candidates[0].name == "test"


def test_execution_engine_register_user_endpoint():
    from ai_generation.execution_engine import ExecutionEngine
    ee = ExecutionEngine()
    ep = ee.register_user_endpoint("my_comfyui", "http://localhost:8188", endpoint_type="comfyui")
    assert ep.name == "my_comfyui"
    assert ep.layer.value == 3  # USER_CONFIGURED
    all_eps = ee.get_all_endpoints()
    assert any(e["name"] == "my_comfyui" for e in all_eps)


def test_execution_engine_stats():
    from ai_generation.execution_engine import ExecutionEngine
    ee = ExecutionEngine()
    ee.initialize()
    stats = ee.get_stats()
    assert stats["total_endpoints"] >= 9


@pytest.mark.asyncio
async def test_execution_engine_execute_no_provider():
    from ai_generation.execution_engine import ExecutionEngine, ExecutionTask, TaskType
    ee = ExecutionEngine()
    # No handlers registered, should fail gracefully
    task = ExecutionTask(task_type=TaskType.TEXT_TO_AUDIO, prompt="test audio")
    result = await ee.execute(task)
    assert result.status.value in ("no_provider", "failed")


# ── Provider Discovery Tests ─────────────────────────────────────

def test_provider_discovery_import():
    from ai_generation.provider_discovery import ProviderDiscoveryEngine, DiscoveryStatus
    pd = ProviderDiscoveryEngine()
    verified = pd.get_verified()
    assert len(verified) >= 5


def test_provider_discovery_free():
    from ai_generation.provider_discovery import ProviderDiscoveryEngine
    pd = ProviderDiscoveryEngine()
    free = pd.get_free_providers()
    assert len(free) >= 3


def test_provider_discovery_recommendations():
    from ai_generation.provider_discovery import ProviderDiscoveryEngine
    pd = ProviderDiscoveryEngine()
    recs = pd.get_recommendations()
    assert len(recs) >= 5
    assert recs[0]["recommendation_score"] >= recs[-1]["recommendation_score"]


def test_provider_discovery_research_sources():
    from ai_generation.provider_discovery import ProviderDiscoveryEngine
    pd = ProviderDiscoveryEngine()
    sources = pd.research_sources()
    assert len(sources) >= 4
    assert any(s["source"] == "github" for s in sources)


def test_provider_discovery_stats():
    from ai_generation.provider_discovery import ProviderDiscoveryEngine
    pd = ProviderDiscoveryEngine()
    stats = pd.get_stats()
    assert stats["total_discoveries"] >= 7
    assert stats["verified"] >= 5


# ── Provider Verifier Tests ──────────────────────────────────────

def test_provider_verifier_import():
    from ai_generation.provider_verifier import ProviderVerifier
    pv = ProviderVerifier()
    assert pv._reports == {}


@pytest.mark.asyncio
async def test_provider_verifier_verify():
    from ai_generation.provider_verifier import ProviderVerifier
    pv = ProviderVerifier()
    report = await pv.verify_provider(
        "pollinations", "https://image.pollinations.ai/health",
        doc_url="https://pollinations.ai",
    )
    assert report.overall_status in ("verified", "partial", "failed")
    assert report.confidence >= 0


def test_provider_verifier_stats():
    from ai_generation.provider_verifier import ProviderVerifier
    pv = ProviderVerifier()
    stats = pv.get_stats()
    assert stats["total_verified"] == 0


# ── Remote Endpoints Tests ───────────────────────────────────────

def test_remote_endpoints_import():
    from ai_generation.remote_endpoints import RemoteEndpointManager, RemoteEndpoint
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        rm = RemoteEndpointManager(config_path=os.path.join(tmpdir, "endpoints.json"))
        ep = rm.add_endpoint("my_server", "http://localhost:8188", endpoint_type="comfyui")
        assert ep.name == "my_server"
        assert ep.endpoint_type == "comfyui"
        eps = rm.list_endpoints()
        assert len(eps) == 1


def test_remote_endpoints_health():
    from ai_generation.remote_endpoints import RemoteEndpointManager
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        rm = RemoteEndpointManager(config_path=os.path.join(tmpdir, "ep.json"))
        rm.add_endpoint("test", "http://localhost:99999", endpoint_type="api")
        import asyncio
        result = asyncio.run(rm.check_health("test"))
        assert result.get("healthy") is False


def test_remote_endpoints_stats():
    from ai_generation.remote_endpoints import RemoteEndpointManager
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        rm = RemoteEndpointManager(config_path=os.path.join(tmpdir, "ep.json"))
        rm.add_endpoint("a", "http://a.com")
        rm.add_endpoint("b", "http://b.com")
        stats = rm.get_stats()
        assert stats["total_endpoints"] == 2


# ── Capability Registry Tests ────────────────────────────────────

def test_capability_registry_import():
    from ai_generation.capability_registry import CapabilityRegistry
    cr = CapabilityRegistry()
    stats = cr.get_stats()
    assert stats["total_models"] >= 15
    assert stats["providers"] >= 6
    assert stats["tasks"] >= 5


def test_capability_registry_find_models():
    from ai_generation.capability_registry import CapabilityRegistry
    cr = CapabilityRegistry()
    t2i = cr.find_models(task="text_to_image")
    assert len(t2i) >= 10
    free = cr.find_models(free_only=True)
    assert len(free) >= 4


def test_capability_registry_summary():
    from ai_generation.capability_registry import CapabilityRegistry
    cr = CapabilityRegistry()
    summary = cr.get_summary()
    assert summary["total_models"] >= 15
    assert "text_to_image" in summary["tasks"]


def test_capability_registry_providers():
    from ai_generation.capability_registry import CapabilityRegistry
    cr = CapabilityRegistry()
    providers = cr.get_providers()
    assert "pollinations" in providers
    assert "stability" in providers
    assert "replicate" in providers


# ── Auto Router Tests ────────────────────────────────────────────

def test_auto_router_import():
    from ai_generation.auto_router import AutoRouter
    ar = AutoRouter()
    decision = ar.classify_task("generate a beautiful sunset")
    assert decision.task_type == "text_to_image"
    assert decision.confidence > 0


def test_auto_router_video():
    from ai_generation.auto_router import AutoRouter
    ar = AutoRouter()
    decision = ar.classify_task("create a cinematic video of clouds")
    assert decision.task_type == "text_to_video"


def test_auto_router_edit():
    from ai_generation.auto_router import AutoRouter
    ar = AutoRouter()
    decision = ar.classify_task("remove the background from this image")
    assert decision.task_type == "background_removal"


def test_auto_router_upscale():
    from ai_generation.auto_router import AutoRouter
    ar = AutoRouter()
    decision = ar.classify_task("upscale this image to 4k resolution")
    assert decision.task_type == "upscale"


def test_auto_router_with_registry():
    from ai_generation.auto_router import AutoRouter
    from ai_generation.capability_registry import CapabilityRegistry
    ar = AutoRouter(capability_registry=CapabilityRegistry())
    decision = ar.classify_task("generate an image of a coffee cup")
    assert len(decision.recommended_providers) > 0


def test_auto_router_stats():
    from ai_generation.auto_router import AutoRouter
    ar = AutoRouter()
    ar.classify_task("test1 image")
    ar.classify_task("test2 video")
    stats = ar.get_stats()
    assert stats["total_routes"] == 2


# ── Health Monitor Tests ─────────────────────────────────────────

def test_health_monitor_import():
    from ai_generation.health_monitor import HealthMonitor
    hm = HealthMonitor()
    hm.register_provider("test", "http://example.com")
    status = hm.get_status("test")
    assert status is not None


def test_health_monitor_healthy_list():
    from ai_generation.health_monitor import HealthMonitor
    hm = HealthMonitor()
    hm.register_provider("a")
    hm.register_provider("b")
    healthy = hm.get_healthy_providers()
    assert len(healthy) == 2  # default is healthy=True


def test_health_monitor_stats():
    from ai_generation.health_monitor import HealthMonitor
    hm = HealthMonitor()
    hm.register_provider("a")
    stats = hm.get_stats()
    assert stats["total_monitored"] == 1
    assert stats["healthy"] == 1


@pytest.mark.asyncio
async def test_health_monitor_check():
    from ai_generation.health_monitor import HealthMonitor
    hm = HealthMonitor()
    status = await hm.check_provider("test", "http://localhost:99999")
    assert status.healthy is False


# ── Agent Interface Tests ────────────────────────────────────────

def test_agent_interface_import():
    from ai_generation.agent_interface import AgentInterface
    ai = AgentInterface()
    assert ai.execution_engine is not None
    assert ai.capability_registry is not None
    assert ai.provider_discovery is not None


def test_agent_interface_classify():
    from ai_generation.agent_interface import AgentInterface
    ai = AgentInterface()
    decision = ai.classify_request("generate a luxury cafe advertisement")
    assert decision["task_type"] is not None


def test_agent_interface_providers():
    from ai_generation.agent_interface import AgentInterface
    ai = AgentInterface()
    providers = ai.get_available_providers()
    assert len(providers) >= 9


def test_agent_interface_capability_matrix():
    from ai_generation.agent_interface import AgentInterface
    ai = AgentInterface()
    matrix = ai.get_capability_matrix()
    assert matrix["total_models"] >= 15


def test_agent_interface_add_remote():
    from ai_generation.agent_interface import AgentInterface
    ai = AgentInterface()
    ep = ai.add_remote_endpoint("my_comfyui", "http://localhost:8188", endpoint_type="comfyui")
    assert ep["name"] == "my_comfyui"


def test_agent_interface_stats():
    from ai_generation.agent_interface import AgentInterface
    ai = AgentInterface()
    stats = ai.get_stats()
    assert "execution_engine" in stats
    assert "capability_registry" in stats
    assert "health_monitor" in stats


@pytest.mark.asyncio
async def test_agent_interface_health_check():
    from ai_generation.agent_interface import AgentInterface
    ai = AgentInterface()
    result = await ai.health_check()
    assert isinstance(result, dict)


# ── SDK Phase 13 Integration Tests ───────────────────────────────

def test_sdk_phase13_properties():
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    assert hasattr(ai, 'agent_interface')
    assert hasattr(ai, 'execution_engine')
    assert hasattr(ai, 'auto_router')
    assert hasattr(ai, 'capability_registry')
    assert hasattr(ai, 'provider_discovery_engine')
    assert hasattr(ai, 'provider_verifier')
    assert hasattr(ai, 'health_monitor')
    assert hasattr(ai, 'remote_endpoint_manager')


def test_sdk_agent_classify():
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    decision = ai.agent_classify("generate a luxury cafe advertisement")
    assert decision["task_type"] is not None


def test_sdk_agent_providers():
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    providers = ai.agent_providers()
    assert len(providers) >= 9


def test_sdk_agent_capability_matrix():
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    matrix = ai.agent_capability_matrix()
    assert matrix["total_models"] >= 15


def test_sdk_agent_add_remote():
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    ep = ai.agent_add_remote_endpoint("test_remote", "http://localhost:8188")
    assert ep["name"] == "test_remote"


# ── MCP Phase 13 Integration Tests ───────────────────────────────

@pytest.mark.asyncio
async def test_mcp_agent_generate():
    from ai_generation.mcp_tools import MCPGenerationTools
    mcp = MCPGenerationTools()
    result = await mcp.handle("agent_generate", {"request": "generate a sunset"})
    assert "route" in result or "execution" in result


@pytest.mark.asyncio
async def test_mcp_classify():
    from ai_generation.mcp_tools import MCPGenerationTools
    mcp = MCPGenerationTools()
    result = await mcp.handle("classify_request", {"request": "create a cinematic video"})
    assert "task_type" in result


@pytest.mark.asyncio
async def test_mcp_list_endpoints():
    from ai_generation.mcp_tools import MCPGenerationTools
    mcp = MCPGenerationTools()
    result = await mcp.handle("list_execution_endpoints", {})
    assert "endpoints" in result
    assert len(result["endpoints"]) >= 9


@pytest.mark.asyncio
async def test_mcp_health_check():
    from ai_generation.mcp_tools import MCPGenerationTools
    mcp = MCPGenerationTools()
    result = await mcp.handle("health_check_providers", {})
    assert isinstance(result, dict)


@pytest.mark.asyncio
async def test_mcp_cap_registry():
    from ai_generation.mcp_tools import MCPGenerationTools
    mcp = MCPGenerationTools()
    result = await mcp.handle("get_capability_registry", {})
    assert result["total_models"] >= 15


@pytest.mark.asyncio
async def test_mcp_add_endpoint():
    from ai_generation.mcp_tools import MCPGenerationTools
    mcp = MCPGenerationTools()
    result = await mcp.handle("add_remote_endpoint", {"name": "mcp_remote", "url": "http://localhost:8188"})
    assert result["name"] == "mcp_remote"


@pytest.mark.asyncio
async def test_mcp_discovery():
    from ai_generation.mcp_tools import MCPGenerationTools
    mcp = MCPGenerationTools()
    result = await mcp.handle("get_provider_discovery", {})
    assert "recommendations" in result


def test_mcp_total_tools():
    from ai_generation.mcp_tools import get_mcp_generation_tools
    tools = get_mcp_generation_tools()
    assert len(tools) >= 33  # 24 + 9 Phase 13 tools
