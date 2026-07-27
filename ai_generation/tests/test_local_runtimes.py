"""
Phase 29 Tests — Local Runtime Integrations (vLLM, llama.cpp, Ollama)

Tests runtime detection, routing, profiling, and fallback for local runtimes.
"""
import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))


def test_import_enums():
    from ai_generation.local_runtimes import RuntimeType, RuntimeStatus, RuntimeCategory
    assert RuntimeType.VLLM.value == "vllm"
    assert RuntimeType.LLAMACPP.value == "llamacpp"
    assert RuntimeType.OLLAMA.value == "ollama"
    assert RuntimeStatus.HEALTHY.value == "healthy"
    assert RuntimeStatus.UNAVAILABLE.value == "unavailable"


def test_runtime_profile_defaults():
    from ai_generation.local_runtimes import RuntimeProfile, RuntimeType, RuntimeStatus
    p = RuntimeProfile()
    assert p.runtime_type == RuntimeType.VLLM
    assert p.status == RuntimeStatus.UNKNOWN
    assert p.models == []
    assert p.to_dict()["runtime_type"] == "vllm"


def test_runtime_profile_serialization():
    from ai_generation.local_runtimes import RuntimeProfile, RuntimeType, RuntimeStatus
    p = RuntimeProfile(
        runtime_id="vllm-abc123",
        runtime_type=RuntimeType.VLLM,
        status=RuntimeStatus.HEALTHY,
        url="http://localhost:8000",
        version="0.6.0",
        models=["llama-3-8b", "mistral-7b"],
        latency_ms=42.5,
        requests_served=100,
        avg_tokens_per_sec=35.2,
    )
    d = p.to_dict()
    assert d["runtime_id"] == "vllm-abc123"
    assert d["status"] == "healthy"
    assert d["model_count"] == 2
    assert d["latency_ms"] == 42.5
    assert d["requests_served"] == 100
    assert d["avg_tokens_per_sec"] == 35.2


def test_runtime_request_defaults():
    from ai_generation.local_runtimes import RuntimeRequest
    r = RuntimeRequest(model="llama-3-8b", prompt="Hello")
    assert r.model == "llama-3-8b"
    assert r.max_tokens == 512
    assert r.temperature == 0.7
    assert r.stream is False
    d = r.to_dict()
    assert d["model"] == "llama-3-8b"


def test_runtime_response_defaults():
    from ai_generation.local_runtimes import RuntimeResponse
    r = RuntimeResponse(runtime="vllm", model="test")
    assert r.runtime == "vllm"
    assert r.error is None
    d = r.to_dict()
    assert d["runtime"] == "vllm"
    assert d["tokens_per_sec"] == 0.0


def test_health_checker_init():
    from ai_generation.local_runtimes import RuntimeHealthChecker, RuntimeType
    hc = RuntimeHealthChecker()
    assert hc.DEFAULT_URLS[RuntimeType.VLLM] == "http://localhost:8000"
    assert hc.DEFAULT_URLS[RuntimeType.LLAMACPP] == "http://localhost:8080"
    assert hc.DEFAULT_URLS[RuntimeType.OLLAMA] == "http://localhost:11434"


def test_health_checker_custom_url():
    from ai_generation.local_runtimes import RuntimeHealthChecker, RuntimeType
    hc = RuntimeHealthChecker({"vllm_url": "http://gpu-server:8000"})
    assert hc._urls[RuntimeType.VLLM] == "http://gpu-server:8000"


def test_router_init():
    from ai_generation.local_runtimes import RuntimeRouter
    router = RuntimeRouter()
    stats = router.get_stats()
    assert stats["total_requests"] == 0
    assert stats["successful"] == 0
    assert stats["success_rate"] == 100.0


def test_router_set_url():
    from ai_generation.local_runtimes import RuntimeRouter, RuntimeType
    router = RuntimeRouter()
    router.set_url(RuntimeType.VLLM, "http://custom-server:8000")
    assert router._custom_urls[RuntimeType.VLLM] == "http://custom-server:8000"
    assert router._health_checker._urls[RuntimeType.VLLM] == "http://custom-server:8000"


def test_router_empty_stats():
    from ai_generation.local_runtimes import RuntimeRouter
    router = RuntimeRouter()
    stats = router.get_stats()
    assert stats["total_requests"] == 0
    assert stats["avg_latency_ms"] == 0
    assert stats["avg_tokens_per_sec"] == 0
    assert stats["healthy_runtimes"] == []


def test_router_request_log():
    from ai_generation.local_runtimes import RuntimeRouter
    router = RuntimeRouter()
    log = router.get_request_log()
    assert isinstance(log, list)
    assert len(log) == 0


def test_manager_init():
    from ai_generation.local_runtimes import LocalRuntimeManager
    mgr = LocalRuntimeManager()
    stats = mgr.get_stats()
    assert stats["total_requests"] == 0
    assert stats["discovery_count"] == 0
    assert stats["configured_runtimes"] == []


def test_manager_configure():
    from ai_generation.local_runtimes import LocalRuntimeManager, RuntimeType
    mgr = LocalRuntimeManager()
    mgr.configure_runtime(RuntimeType.VLLM, url="http://gpu:8000")
    assert RuntimeType.VLLM in mgr._runtime_configs
    assert mgr._runtime_configs[RuntimeType.VLLM]["url"] == "http://gpu:8000"


def test_manager_healthy_count():
    from ai_generation.local_runtimes import LocalRuntimeManager
    mgr = LocalRuntimeManager()
    assert mgr.get_healthy_count() == 0


def test_manager_get_profile_none():
    from ai_generation.local_runtimes import LocalRuntimeManager, RuntimeType
    mgr = LocalRuntimeManager()
    profile = mgr.get_runtime_profile(RuntimeType.VLLM)
    assert profile is None


def test_manager_list_models_empty():
    from ai_generation.local_runtimes import LocalRuntimeManager
    import asyncio
    mgr = LocalRuntimeManager()
    models = asyncio.run(mgr.list_all_models())
    assert models == {}


def test_router_no_healthy_runtimes():
    import asyncio
    from ai_generation.local_runtimes import RuntimeRouter, RuntimeRequest, RuntimeResponse
    router = RuntimeRouter()
    request = RuntimeRequest(model="test", prompt="Hello")
    result = asyncio.run(router.route_request(request))
    assert result.error is not None
    assert "No healthy" in result.error
    assert result.runtime == "none"


def test_health_checker_check_all():
    import asyncio
    from ai_generation.local_runtimes import RuntimeHealthChecker
    hc = RuntimeHealthChecker()
    results = asyncio.run(hc.check_all())
    assert len(results) == 3  # vllm, llamacpp, ollama
    for rt, profile in results.items():
        assert profile.runtime_type == rt
        assert profile.status.value in ["healthy", "degraded", "unavailable", "unknown"]


def test_health_checker_custom_timeout():
    from ai_generation.local_runtimes import RuntimeHealthChecker, RuntimeType
    hc = RuntimeHealthChecker({"vllm_timeout": 1.0, "ollama_timeout": 5.0})
    assert hc._timeouts[RuntimeType.VLLM] == 1.0
    assert hc._timeouts[RuntimeType.OLLAMA] == 5.0


def test_runtime_type_all_values():
    from ai_generation.local_runtimes import RuntimeType
    types = list(RuntimeType)
    assert len(types) == 3
    assert set(t.value for t in types) == {"vllm", "llamacpp", "ollama"}


def test_runtime_status_all_values():
    from ai_generation.local_runtimes import RuntimeStatus
    statuses = list(RuntimeStatus)
    assert len(statuses) == 4
    values = set(s.value for s in statuses)
    assert "healthy" in values
    assert "unavailable" in values


# ── SDK Integration Tests ──

def test_sdk_local_runtimes_import():
    from ai_generation.sdk import UncleFrappeAI
    sdk = UncleFrappeAI({"test_mode": True})
    assert sdk.local_runtimes is not None


def test_sdk_local_runtimes_stats():
    from ai_generation.sdk import UncleFrappeAI
    sdk = UncleFrappeAI({"test_mode": True})
    stats = sdk.get_local_runtime_stats()
    assert stats["total_requests"] == 0
    assert stats["discovery_count"] == 0


def test_sdk_configure_local_runtime():
    from ai_generation.sdk import UncleFrappeAI
    sdk = UncleFrappeAI({"test_mode": True})
    result = sdk.configure_local_runtime("vllm", "http://gpu-server:8000")
    assert result["success"] is True
    assert result["runtime"] == "vllm"


def test_sdk_get_local_runtime_profile():
    from ai_generation.sdk import UncleFrappeAI
    sdk = UncleFrappeAI({"test_mode": True})
    result = sdk.get_local_runtime_profile("vllm")
    assert "error" in result  # Not discovered yet


# ── MCP Tool Tests ──

def test_mcp_local_runtime_tools_exist():
    from ai_generation.mcp_tools import MCP_GENERATION_TOOLS
    assert "discover_local_runtimes" in MCP_GENERATION_TOOLS
    assert "configure_local_runtime" in MCP_GENERATION_TOOLS
    assert "get_local_runtime_stats" in MCP_GENERATION_TOOLS
    assert "get_local_runtime_profile" in MCP_GENERATION_TOOLS
    assert "generate_local" in MCP_GENERATION_TOOLS


def test_mcp_local_runtime_handler_import():
    from ai_generation.mcp_tools import MCPGenerationTools
    tools = MCPGenerationTools()
    assert hasattr(tools, "_handle_discover_local_runtimes")
    assert hasattr(tools, "_handle_configure_local_runtime")
    assert hasattr(tools, "_handle_get_local_runtime_stats")
    assert hasattr(tools, "_handle_get_local_runtime_profile")
    assert hasattr(tools, "_handle_generate_local")


def test_mcp_tool_schemas():
    from ai_generation.mcp_tools import MCP_GENERATION_TOOLS
    schema = MCP_GENERATION_TOOLS["discover_local_runtimes"]
    assert schema["name"] == "discover_local_runtimes"
    assert "inputSchema" in schema

    schema = MCP_GENERATION_TOOLS["configure_local_runtime"]
    assert "runtime_type" in schema["inputSchema"]["properties"]
    assert "url" in schema["inputSchema"]["properties"]
    assert "runtime_type" in schema["inputSchema"]["required"]

    schema = MCP_GENERATION_TOOLS["generate_local"]
    assert "model" in schema["inputSchema"]["required"]
    assert "prompt" in schema["inputSchema"]["required"]


# ── Edge Cases ──

def test_profile_empty_models():
    from ai_generation.local_runtimes import RuntimeProfile
    p = RuntimeProfile(models=[])
    assert p.to_dict()["model_count"] == 0


def test_response_long_text():
    from ai_generation.local_runtimes import RuntimeResponse
    r = RuntimeResponse(text="x" * 1000)
    d = r.to_dict()
    assert len(d["text"]) <= 503  # 500 chars + "..."


def test_request_long_prompt():
    from ai_generation.local_runtimes import RuntimeRequest
    r = RuntimeRequest(prompt="y" * 500)
    d = r.to_dict()
    assert len(d["prompt"]) <= 203  # 200 chars + "..."
