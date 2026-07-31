"""
Kimi K3 Integration Tests — Moonshot AI Kimi K3 execution runtime.

Covers the canonical verified spec, message building, response parsing,
official launch command builders, cloud/vLLM/SGLang clients, the unified
manager (fallback, stats, benchmark, health), execution-engine routing,
capability registry/matrix, auto-router chat classification, SDK, CLI,
MCP tools, health-monitor registration, knowledge-graph nodes, and the
quality-engine chat evaluator. All tests run offline (no live network).
"""
import asyncio
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))


# ── Helpers ───────────────────────────────────────────────────────

def fake_chat_response(text="Hello from Kimi K3", reasoning="verified reasoning",
                       model="kimi-k3"):
    return {
        "choices": [{
            "message": {"content": text, "reasoning_content": reasoning},
            "finish_reason": "stop",
        }],
        "model": model,
        "usage": {
            "prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15,
            "prompt_tokens_details": {"cached_tokens": 0},
        },
    }


def make_post(cloud_ok=False):
    """Build a fake _post_json. By default fails on cloud and succeeds elsewhere."""
    async def _post(url, api_key, payload, timeout=120.0):
        if not cloud_ok and "api.moonshot.ai" in url:
            from ai_generation.kimi_k3 import KimiK3Error
            raise KimiK3Error("HTTP 401: invalid api key")
        assert isinstance(payload, dict)
        assert payload["model"] == "kimi-k3"
        assert payload["reasoning_effort"] in ("low", "high", "max")
        return fake_chat_response()
    return _post


# ── Canonical verified spec ───────────────────────────────────────

def test_kimi_k3_spec_constants():
    from ai_generation.kimi_k3 import KIMI_K3_SPEC
    arch = KIMI_K3_SPEC["architecture"]
    assert KIMI_K3_SPEC["model"] == "kimi-k3"
    assert KIMI_K3_SPEC["model_id"] == "moonshotai/Kimi-K3"
    assert KIMI_K3_SPEC["model_type"] == "kimi_k3"
    assert KIMI_K3_SPEC["context_length"] == 1048576
    assert arch["total_params"] == "2.8T"
    assert arch["active_params"] == "104B"
    assert arch["layers"] == 93
    assert arch["experts"] == 896
    assert arch["experts_per_token"] == 16
    assert arch["hidden_size"] == 7168
    assert arch["multimodal"] is True
    assert arch["weights_dtype"] == "MXFP4"
    assert arch["activations_dtype"] == "MXFP8"
    tok = KIMI_K3_SPEC["tokenizer"]
    assert tok["name"] == "TikTokenTokenizer"
    assert tok["vocab_size"] == 163840
    assert KIMI_K3_SPEC["thinking"]["reasoning_effort"] == ["low", "high", "max"]
    assert KIMI_K3_SPEC["thinking"]["always_on"] is True


def test_kimi_k3_supported_engines():
    from ai_generation.kimi_k3 import KIMI_K3_SPEC
    engines = KIMI_K3_SPEC["engines"]
    assert engines["cloud_api"]["supported"] is True
    assert engines["cloud_api"]["base_url"] == "https://api.moonshot.ai/v1"
    assert engines["vllm"]["supported"] is True
    assert engines["vllm"]["min_version"] == "0.27.0"
    assert "kimi_k3" in engines["vllm"]["parsers"][0]
    assert engines["sglang"]["supported"] is True
    assert engines["tokenspeed"]["supported"] is True


def test_kimi_k3_unsupported_runtimes_recorded():
    from ai_generation.kimi_k3 import KIMI_K3_SPEC
    unsupported = KIMI_K3_SPEC["unsupported_runtimes"]
    for name in ("tensorrt_llm", "deepspeed", "llamacpp", "ollama",
                 "huggingface_inference", "huggingface_endpoints", "gguf"):
        assert name in unsupported
        assert unsupported[name]


def test_kimi_k3_deployment_facts():
    from ai_generation.kimi_k3 import KIMI_K3_SPEC
    dep = KIMI_K3_SPEC["deployment"]
    assert dep["min_gpus"] == 8
    assert dep["min_vram_gb"] == 1680
    assert dep["docker"] is True
    assert dep["kubernetes"] is True


# ── Message building ──────────────────────────────────────────────

def test_build_chat_messages_text_only():
    from ai_generation.kimi_k3 import build_chat_messages
    messages = build_chat_messages("hello", system_prompt="be brief")
    assert messages[0] == {"role": "system", "content": "be brief"}
    assert messages[1] == {"role": "user", "content": "hello"}


def test_build_chat_messages_with_images():
    from ai_generation.kimi_k3 import build_chat_messages
    messages = build_chat_messages("describe this", images=["https://x/img.png"])
    content = messages[-1]["content"]
    assert isinstance(content, list)
    assert content[0]["type"] == "text"
    assert content[1] == {"type": "image_url", "image_url": {"url": "https://x/img.png"}}


def test_build_chat_messages_preserved_thinking():
    from ai_generation.kimi_k3 import build_chat_messages
    history = [
        {"role": "user", "content": "q1"},
        {"role": "assistant", "content": "a1", "reasoning_content": "r1", "tool_calls": []},
    ]
    messages = build_chat_messages("q2", history=history)
    assistant = messages[1]
    assert assistant["reasoning_content"] == "r1"
    assert assistant["tool_calls"] == []
    # preserve_thinking=False strips reasoning_content
    messages = build_chat_messages("q2", history=history, preserve_thinking=False)
    assert "reasoning_content" not in messages[1]


def test_build_chat_payload_reasoning_effort():
    from ai_generation.kimi_k3 import build_chat_payload
    payload = build_chat_payload("hi", reasoning_effort="high")
    assert payload["reasoning_effort"] == "high"
    assert payload["model"] == "kimi-k3"
    payload = build_chat_payload("hi", reasoning_effort="bogus")
    assert payload["reasoning_effort"] == "max"
    payload = build_chat_payload("hi")
    assert payload["reasoning_effort"] == "max"
    assert payload["stream"] is False


def test_build_chat_payload_optional_params():
    from ai_generation.kimi_k3 import build_chat_payload
    payload = build_chat_payload("hi", max_tokens=100, temperature=0.3,
                                 top_p=0.9, tools=[{"type": "function"}])
    assert payload["max_tokens"] == 100
    assert payload["temperature"] == 0.3
    assert payload["top_p"] == 0.9
    assert payload["tools"] == [{"type": "function"}]


# ── Response parsing ──────────────────────────────────────────────

def test_parse_chat_response():
    from ai_generation.kimi_k3 import parse_chat_response
    parsed = parse_chat_response(fake_chat_response())
    assert parsed["text"] == "Hello from Kimi K3"
    assert parsed["reasoning"] == "verified reasoning"
    assert parsed["total_tokens"] == 15
    assert parsed["completion_tokens"] == 5


def test_parse_chat_response_no_choices():
    from ai_generation.kimi_k3 import KimiK3Error, parse_chat_response
    with pytest.raises(KimiK3Error):
        parse_chat_response({"choices": []})


# ── Official launch command builders ──────────────────────────────

def test_build_vllm_command_blackwell():
    from ai_generation.kimi_k3 import build_vllm_command
    cmd = build_vllm_command(hardware="blackwell")
    assert cmd["image"] == "vllm/vllm-openai:kimi-k3"
    args = cmd["command"]
    assert "--trust-remote-code" in args
    assert "--reasoning-parser" in args and "kimi_k3" in args
    assert "--tensor-parallel-size" in args
    assert "8" in args
    assert "--expert-parallel-size" in args and "16" in args
    assert cmd["env"]["VLLM_ENABLE_K3_LATENT_MOE_TAIL_FUSION"] == "1"
    assert cmd["min_vram_gb"] == 1680


def test_build_vllm_command_hopper():
    from ai_generation.kimi_k3 import build_vllm_command
    cmd = build_vllm_command(hardware="hopper")
    args = " ".join(cmd["command"])
    assert "--moe-backend marlin" in args
    assert "--attention-backend FLASHMLA" in args
    assert cmd["env"]["PYTORCH_CUDA_ALLOC_CONF"] == "expandable_segments:True"


def test_build_vllm_command_amd():
    from ai_generation.kimi_k3 import build_vllm_command
    cmd = build_vllm_command(hardware="amd")
    assert cmd["image"] == "vllm/vllm-openai-rocm:kimi-k3"
    assert cmd["env"]["VLLM_ROCM_USE_AITER"] == "1"
    assert "--mm-encoder-tp-mode" in cmd["command"]


def test_build_vllm_command_spec_decode():
    from ai_generation.kimi_k3 import build_vllm_command
    cmd = build_vllm_command(hardware="blackwell", spec_decode=True)
    spec_idx = cmd["command"].index("--speculative-config")
    spec = json.loads(cmd["command"][spec_idx + 1])
    assert spec["model"] == "Inferact/Kimi-K3-DSpark"
    assert spec["num_speculative_tokens"] == 7
    assert spec["method"] == "dspark"


def test_build_vllm_command_language_model_only():
    from ai_generation.kimi_k3 import build_vllm_command
    cmd = build_vllm_command(language_model_only=True)
    assert "--language-model-only" in cmd["command"]


def test_build_sglang_command():
    from ai_generation.kimi_k3 import build_sglang_command
    cmd = build_sglang_command(hardware="b200")
    assert cmd["image"] == "lmsysorg/sglang:kimi-k3"
    args = cmd["command"]
    assert "--reasoning-parser" in args and "kimi_k3" in args
    assert "--tp-size" in args and "16" in args
    assert "--dp-size" in args and "16" in args
    assert "--host" in args and "--port" in args and "30000" in args
    assert "--kv-cache-dtype" in args and "fp8_e4m3" in args


def test_build_sglang_command_pd_disaggregation():
    from ai_generation.kimi_k3 import build_sglang_command
    cmd = build_sglang_command(hardware="h100", pp_size=8)
    args = cmd["command"]
    assert "--pp-size" in args and "8" in args


# ── Clients (mocked HTTP) ─────────────────────────────────────────

@pytest.mark.asyncio
async def test_cloud_client_chat(monkeypatch):
    from ai_generation.kimi_k3 import _post_json, KimiK3CloudClient

    captured = {}

    async def fake_post(url, api_key, payload, timeout=120.0):
        captured["url"] = url
        captured["api_key"] = api_key
        captured["payload"] = payload
        return fake_chat_response()

    monkeypatch.setattr("ai_generation.kimi_k3._post_json", fake_post)
    client = KimiK3CloudClient(api_key="test-key")
    result = await client.chat("hello", reasoning_effort="high", max_tokens=64)
    assert result["text"] == "Hello from Kimi K3"
    assert result["reasoning"] == "verified reasoning"
    assert captured["url"].endswith("/chat/completions")
    assert captured["api_key"] == "test-key"
    assert captured["payload"]["reasoning_effort"] == "high"
    assert captured["payload"]["max_tokens"] == 64


@pytest.mark.asyncio
async def test_client_health(monkeypatch):
    from ai_generation.kimi_k3 import KimiK3VllmServer

    async def fake_get(url, api_key="", timeout=15.0):
        assert url.endswith("/models")
        return {"data": [{"id": "moonshotai/Kimi-K3"}]}

    monkeypatch.setattr("ai_generation.kimi_k3._get_json", fake_get)
    client = KimiK3VllmServer(base_url="http://localhost:8000")
    health = await client.health()
    assert health["healthy"] is True
    assert health["serves_kimi_k3"] is True


@pytest.mark.asyncio
async def test_client_http_error(monkeypatch):
    from ai_generation.kimi_k3 import KimiK3Error, KimiK3SglangServer

    async def fake_post(url, api_key, payload, timeout=120.0):
        raise KimiK3Error("HTTP 429: rate limited")

    monkeypatch.setattr("ai_generation.kimi_k3._post_json", fake_post)
    client = KimiK3SglangServer(base_url="http://localhost:30000")
    with pytest.raises(KimiK3Error):
        await client.chat("hello")


# ── Manager ───────────────────────────────────────────────────────

def test_manager_info():
    from ai_generation.kimi_k3 import KimiK3Manager
    manager = KimiK3Manager()
    info = manager.info()
    assert info["spec"]["model"] == "kimi-k3"
    supported = {p["name"] for p in info["supported_paths"]}
    assert supported == {"cloud_api", "vllm", "sglang", "tokenspeed"}
    unsupported = {p["name"] for p in info["unsupported_paths"]}
    assert "llamacpp" in unsupported and "ollama" in unsupported
    assert len(info["configured_endpoints"]) == 3


def test_manager_provider_order():
    from ai_generation.kimi_k3 import KimiK3Manager
    manager = KimiK3Manager()
    order = manager.provider_order("auto")
    assert [e["name"] for e in order] == ["kimi_k3_cloud", "kimi_k3_vllm", "kimi_k3_sglang"]
    order = manager.provider_order("kimi_k3_vllm")
    assert [e["name"] for e in order] == ["kimi_k3_vllm"]


def test_manager_provider_order_unknown():
    from ai_generation.kimi_k3 import KimiK3Error, KimiK3Manager
    manager = KimiK3Manager()
    with pytest.raises(KimiK3Error):
        manager.provider_order("nope")


@pytest.mark.asyncio
async def test_manager_chat_success(monkeypatch):
    from ai_generation.kimi_k3 import KimiK3Manager
    monkeypatch.setattr("ai_generation.kimi_k3._post_json", make_post())
    manager = KimiK3Manager()
    result = await manager.chat("Explain MoE", provider="kimi_k3_vllm",
                                reasoning_effort="high")
    assert result.error is None
    assert result.text == "Hello from Kimi K3"
    assert result.reasoning == "verified reasoning"
    assert result.provider == "kimi_k3_vllm"
    assert result.latency_ms >= 0
    assert result.quality_score > 0
    stats = manager.get_stats()
    assert stats["total_requests"] == 1
    assert stats["successful"] == 1
    assert stats["by_provider"]["kimi_k3_vllm"]["requests"] == 1


@pytest.mark.asyncio
async def test_manager_chat_fallback(monkeypatch):
    from ai_generation.kimi_k3 import KimiK3Manager
    monkeypatch.setattr("ai_generation.kimi_k3._post_json", make_post())
    manager = KimiK3Manager()
    result = await manager.chat("fallback test")
    # Cloud fails (fake) -> falls back to vLLM (localhost:8000)
    assert result.error is None
    assert result.provider in ("kimi_k3_vllm", "kimi_k3_sglang")
    assert "kimi_k3_cloud" in result.fallbacks


@pytest.mark.asyncio
async def test_manager_all_providers_fail(monkeypatch):
    from ai_generation.kimi_k3 import KimiK3Error, KimiK3Manager

    async def always_fail(url, api_key, payload, timeout=120.0):
        raise KimiK3Error("down")

    monkeypatch.setattr("ai_generation.kimi_k3._post_json", always_fail)
    manager = KimiK3Manager()
    result = await manager.chat("boom")
    assert result.error is not None
    assert result.text == ""
    stats = manager.get_stats()
    assert stats["failed"] >= 1


@pytest.mark.asyncio
async def test_manager_benchmark(monkeypatch):
    from ai_generation.kimi_k3 import KimiK3Manager
    monkeypatch.setattr("ai_generation.kimi_k3._post_json", make_post())
    manager = KimiK3Manager()
    report = await manager.benchmark("benchmark me", runs=2, provider="kimi_k3_vllm")
    assert len(report["runs"]) == 2
    assert all(r["success"] for r in report["runs"])
    assert all(r["quality_score"] > 0 for r in report["runs"])


@pytest.mark.asyncio
async def test_manager_health(monkeypatch):
    from ai_generation.kimi_k3 import KimiK3Manager

    async def fake_get(url, api_key="", timeout=15.0):
        return {"data": [{"id": "moonshotai/Kimi-K3"}]}

    monkeypatch.setattr("ai_generation.kimi_k3._get_json", fake_get)
    manager = KimiK3Manager()
    health = await manager.health()
    assert "kimi_k3_cloud" in health
    assert "kimi_k3_vllm" in health
    assert "kimi_k3_sglang" in health
    assert health["kimi_k3_cloud"]["healthy"] is True


# ── Execution Engine integration ──────────────────────────────────

def test_execution_engine_kimi_endpoints():
    from ai_generation.execution_engine import ExecutionEngine, TaskType
    ee = ExecutionEngine()
    ee.initialize()
    endpoints = {e["name"]: e for e in ee.get_all_endpoints()}
    assert "kimi_k3_cloud" in endpoints
    assert "chat" in endpoints["kimi_k3_cloud"]["supported_tasks"]
    assert "kimi-k3" in endpoints["kimi_k3_cloud"]["models"]
    assert endpoints["kimi_k3_cloud"]["layer"] == 1  # ExecutionLayer.PUBLIC_API


def test_execution_engine_kimi_handlers():
    from ai_generation.execution_engine import ExecutionEngine
    ee = ExecutionEngine()
    ee.initialize()
    assert "kimi_k3_cloud" in ee.router._handlers


@pytest.mark.asyncio
async def test_execution_engine_chat_execute(monkeypatch):
    from ai_generation.execution_engine import (
        ExecutionEngine, ExecutionTask, TaskType,
    )
    monkeypatch.setattr("ai_generation.kimi_k3._post_json", make_post(cloud_ok=True))
    ee = ExecutionEngine()
    task = ExecutionTask(
        task_type=TaskType.CHAT, prompt="Explain MoE",
        preferred_provider="kimi_k3_cloud",
        params={"reasoning_effort": "high"},
    )
    result = await ee.execute(task)
    assert result.status.value == "completed"
    assert result.metadata["text"] == "Hello from Kimi K3"
    assert result.metadata["reasoning"] == "verified reasoning"
    assert result.metadata["provider"] == "kimi_k3_cloud"


@pytest.mark.asyncio
async def test_execution_engine_chat_execute_failure(monkeypatch):
    from ai_generation.execution_engine import (
        ExecutionEngine, ExecutionTask, TaskType,
    )
    from ai_generation.kimi_k3 import KimiK3Error

    async def fail(url, api_key, payload, timeout=120.0):
        raise KimiK3Error("down")

    monkeypatch.setattr("ai_generation.kimi_k3._post_json", fail)
    ee = ExecutionEngine()
    task = ExecutionTask(
        task_type=TaskType.CHAT, prompt="boom",
        preferred_provider="kimi_k3_cloud",
    )
    result = await ee.execute(task)
    assert result.status.value in ("failed", "no_provider")


# ── Capability registry / matrix / auto router ────────────────────

def test_capability_registry_has_kimi_k3():
    from ai_generation.capability_registry import CapabilityRegistry
    registry = CapabilityRegistry()
    models = registry.find_models(task="chat")
    providers = {m["provider"] for m in models}
    assert "kimi_k3_cloud" in providers
    assert "kimi_k3_vllm" in providers
    assert "kimi_k3_sglang" in providers
    kimi = registry.get_model("kimi-k3-cloud")
    assert kimi["known_limits"]["context_length"] == 1048576


def test_capability_matrix_chat():
    from ai_generation.capability_matrix import CapabilityMatrix
    matrix = CapabilityMatrix()
    best = matrix.find_best_model("chat")
    assert len(best) >= 3
    providers = {m["provider"] for m in best}
    assert "kimi_k3_vllm" in providers
    caps = matrix.get_capabilities(provider="kimi_k3_sglang")
    assert len(caps) == 1
    assert caps[0]["type"] == "text"
    assert caps[0]["streaming"] is True


def test_auto_router_classifies_chat():
    from ai_generation.auto_router import AutoRouter
    router = AutoRouter()
    decision = router.classify_task("Explain why the sky is blue in detail")
    assert decision.task_type == "chat"
    assert decision.confidence > 0


def test_auto_router_chat_recommends_kimi():
    from ai_generation.auto_router import AutoRouter
    from ai_generation.capability_registry import CapabilityRegistry
    router = AutoRouter(capability_registry=CapabilityRegistry())
    decision = router.classify_task("Write a poem about the ocean")
    assert decision.task_type == "chat"
    recommended = {r["provider"] for r in decision.recommended_providers}
    assert "kimi_k3_cloud" in recommended


# ── SDK ───────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_sdk_chat(monkeypatch):
    from ai_generation.sdk import UncleFrappeAI
    monkeypatch.setattr("ai_generation.kimi_k3._post_json", make_post())
    ai = UncleFrappeAI()
    result = await ai.chat("hello kimi", provider="kimi_k3_vllm",
                           reasoning_effort="low")
    assert result["text"] == "Hello from Kimi K3"
    assert result["provider"] == "kimi_k3_vllm"
    assert "reasoning" in result
    assert result["quality_score"] > 0


def test_sdk_kimi_info():
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    info = ai.kimi_k3_info()
    assert info["spec"]["context_length"] == 1048576
    assert len(info["unsupported_paths"]) == 7


def test_sdk_stats_include_kimi():
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    stats = ai.get_stats()
    assert "kimi_k3" in stats
    assert stats["kimi_k3"]["total_requests"] == 0


# ── CLI ───────────────────────────────────────────────────────────

def test_cli_kimi_info(capsys):
    from ai_generation.cli import cmd_kimi_info
    asyncio.run(cmd_kimi_info())
    out = capsys.readouterr().out
    assert "Kimi K3" in out
    assert "1048576" in out.replace(",", "")
    assert "2.8T" in out
    assert "unsupported" in out.lower()


@pytest.mark.asyncio
async def test_cli_kimi_chat(monkeypatch, capsys):
    from ai_generation.cli import cmd_kimi_chat
    monkeypatch.setattr("ai_generation.kimi_k3._post_json", make_post())
    await cmd_kimi_chat("hello", provider="kimi_k3_vllm")
    out = capsys.readouterr().out
    assert "Provider:" in out
    assert "Hello from Kimi K3" in out


# ── MCP tools ─────────────────────────────────────────────────────

def test_mcp_kimi_tools_registered():
    from ai_generation.mcp_tools import MCP_GENERATION_TOOLS
    for name in ("kimi_k3_chat", "kimi_k3_spec", "kimi_k3_info"):
        assert name in MCP_GENERATION_TOOLS
        assert MCP_GENERATION_TOOLS[name]["name"] == name


@pytest.mark.asyncio
async def test_mcp_kimi_chat_handler(monkeypatch):
    from ai_generation.mcp_tools import MCPGenerationTools
    monkeypatch.setattr("ai_generation.kimi_k3._post_json", make_post())
    tools = MCPGenerationTools()
    result = await tools.handle("kimi_k3_chat", {
        "prompt": "hello", "provider": "kimi_k3_vllm",
        "reasoning_effort": "low",
    })
    assert result["text"] == "Hello from Kimi K3"
    assert result["provider"] == "kimi_k3_vllm"


@pytest.mark.asyncio
async def test_mcp_kimi_spec_and_info_handlers():
    from ai_generation.mcp_tools import MCPGenerationTools
    tools = MCPGenerationTools()
    spec = await tools.handle("kimi_k3_spec", {})
    assert spec["spec"]["context_length"] == 1048576
    info = await tools.handle("kimi_k3_info", {})
    assert info["spec"]["model"] == "kimi-k3"


# ── Health monitor registration ───────────────────────────────────

def test_register_kimi_k3_health():
    from ai_generation.health_monitor import HealthMonitor
    from ai_generation.kimi_k3 import register_kimi_k3_health
    monitor = HealthMonitor()
    registered = register_kimi_k3_health(monitor)
    assert set(registered) == {"kimi_k3_cloud", "kimi_k3_vllm", "kimi_k3_sglang"}
    assert monitor.get_status("kimi_k3_cloud") is not None


# ── Knowledge graph ───────────────────────────────────────────────

def test_register_kimi_k3_graph(tmp_path):
    from ai_generation.knowledge_graph import KnowledgeGraph
    from ai_generation.kimi_k3 import register_kimi_k3_graph
    graph = KnowledgeGraph(data_dir=str(tmp_path))
    added = register_kimi_k3_graph(graph)
    assert added >= 3
    provider = graph.get_node("provider:kimi_k3")
    assert provider is not None
    assert graph.get_node("model:kimi-k3") is not None
    assert graph.get_node("capability:chat") is not None
    assert "provider:kimi_k3" in graph.query_providers_by_capability("chat")
    # Idempotent: second registration adds nothing new
    added_again = register_kimi_k3_graph(graph)
    assert added_again == 0


# ── Quality engine chat evaluation ────────────────────────────────

def test_quality_engine_evaluate_chat():
    from ai_generation.quality_engine import QualityEngine
    engine = QualityEngine()
    report = engine.evaluate_chat("Explain MoE in detail please",
                                  "Mixture of Experts is a technique where...")
    assert report.overall_score > 0
    assert "prompt_relevance" in report.dimensions
    assert "completeness" in report.dimensions
    stats = engine.get_stats()
    assert stats["total_evaluations"] == 1


# ── Decision ledger chat records ──────────────────────────────────

def test_decision_ledger_record_chat(ledger_isolated):
    from ai_generation.decision_ledger import DecisionLedger, DecisionOutcome
    ledger = DecisionLedger({"ledger_path": ledger_isolated})
    entry = ledger.record_chat(
        request_id="req-1", prompt="hello", provider="kimi_k3_cloud",
        latency_ms=123.4, quality_score=88.0,
    )
    d = entry.to_dict()
    assert d["task_type"] == "chat"
    assert d["selected_provider"] == "kimi_k3_cloud"
    assert d["outcome"] == "success"
    failed = ledger.record_chat(
        request_id="req-2", prompt="boom", provider="kimi_k3_vllm",
        outcome=DecisionOutcome.FAILURE, error="timeout",
    )
    assert failed.to_dict()["outcome"] == "failure"


# ── K3 launch commands expose supported/unsupported truthfully ────

def test_kimi_info_endpoint_truthfulness():
    from ai_generation.kimi_k3 import KimiK3Manager
    info = KimiK3Manager().info()
    for path in info["unsupported_paths"]:
        assert path["supported"] is False
    for path in info["supported_paths"]:
        assert path["supported"] is True


# ── Negotiation Engine candidates ────────────────────────────────

def test_kimi_k3_negotiation_candidates():
    from ai_generation.kimi_k3 import kimi_k3_candidates
    from ai_generation.negotiation_engine import (
        NegotiationEngine, NegotiationRequest, Modality, TaskType,
    )
    candidates = kimi_k3_candidates()
    assert len(candidates) == 3
    names = {c.provider_name for c in candidates}
    assert names == {"kimi_k3_cloud", "kimi_k3_vllm", "kimi_k3_sglang"}
    cloud = next(c for c in candidates if c.provider_name == "kimi_k3_cloud")
    assert cloud.verified is True
    assert cloud.metadata["context_length"] == 1048576
    # Negotiation engine can rank the K3 candidates without any network access
    engine = NegotiationEngine()
    request = NegotiationRequest(
        task_type=TaskType.CHAT, modality=Modality.TEXT,
        prompt="explain", required_capabilities=["chat"],
    )
    result = engine.negotiate(request, candidates)
    assert result.selected_candidate is not None
    assert result.selected_candidate.provider_name in names
    assert len(result.fallback_chain) >= 1


# ── Docker run builders ───────────────────────────────────────────

def test_build_vllm_docker_run():
    from ai_generation.kimi_k3 import build_vllm_docker_run
    plan = build_vllm_docker_run(hardware="blackwell")
    assert plan["engine"] == "vllm"
    assert "docker run --gpus all" in plan["docker_run"]
    assert "vllm/vllm-openai:kimi-k3" in plan["docker_run"]
    assert "--tensor-parallel-size" in plan["docker_run"]
    assert "-e VLLM_ENABLE_K3_LATENT_MOE_TAIL_FUSION=1" in plan["docker_run"]
    assert plan["requires_gpus"] == 128


def test_build_sglang_docker_run():
    from ai_generation.kimi_k3 import build_sglang_docker_run
    plan = build_sglang_docker_run(hardware="b200")
    assert plan["engine"] == "sglang"
    assert "lmsysorg/sglang:kimi-k3" in plan["docker_run"]
    assert "--tp-size 16" in plan["docker_run"]
    assert "-p 30000:30000" in plan["docker_run"]


# ── Capability Graph integration ──────────────────────────────────

def test_capability_graph_has_kimi_k3():
    from ai_generation.capability_graph import CapabilityGraph
    graph = CapabilityGraph()
    assert graph.get_node("kimi_k3_cloud") is not None
    assert graph.get_node("kimi_k3_vllm") is not None
    assert graph.get_node("kimi_k3_sglang") is not None
    paths = graph.find_capability_path("chat")
    providers = {p.nodes[0] for p in paths}
    assert providers == {"kimi_k3_cloud", "kimi_k3_vllm", "kimi_k3_sglang"}
    chain = graph.find_fallback_chain("chat", failed_provider="kimi_k3_cloud")
    assert chain and chain[0]["provider"] in ("kimi_k3_vllm", "kimi_k3_sglang")


def test_register_kimi_k3_capability_graph_idempotent():
    from ai_generation.capability_graph import CapabilityGraph
    from ai_generation.kimi_k3 import register_kimi_k3_capability_graph
    graph = CapabilityGraph()
    before = graph.get_stats()
    added = register_kimi_k3_capability_graph(graph)
    after = graph.get_stats()
    # Default graph already contains K3 -> nothing new added
    assert added == 0
    assert before["node_count"] == after["node_count"]


def test_register_kimi_k3_capability_graph_dynamic():
    from ai_generation.capability_graph import CapabilityGraph
    from ai_generation.kimi_k3 import register_kimi_k3_capability_graph
    graph = CapabilityGraph()
    # Remove K3 nodes to simulate a fresh/dynamic graph
    for pid in ("kimi_k3_cloud", "kimi_k3_vllm", "kimi_k3_sglang", "chat"):
        graph._nodes.pop(pid, None)
    added = register_kimi_k3_capability_graph(graph)
    assert added >= 4  # 3 provider nodes + chat capability node
    assert len(graph.find_capability_path("chat")) == 3


# ── Benchmark Lab integration ─────────────────────────────────────

@pytest.mark.asyncio
async def test_manager_benchmark_lab(monkeypatch, tmp_path):
    from ai_generation.benchmark_lab import BenchmarkLab
    from ai_generation.kimi_k3 import KimiK3Manager
    monkeypatch.setattr("ai_generation.kimi_k3._post_json", make_post())
    lab = BenchmarkLab(data_dir=str(tmp_path))
    manager = KimiK3Manager(benchmark_lab=lab)
    report = await manager.benchmark("lab benchmark", runs=2, provider="kimi_k3_vllm")
    assert len(report["runs"]) == 2
    stats = lab.get_stats()
    assert stats["total_results"] == 2
    assert stats["total_providers"] == 1
    score = lab.get_provider_score("kimi_k3_vllm")
    assert score is not None
    assert score["total_benchmarks"] == 2


# ── Provider Intelligence ─────────────────────────────────────────

def test_provider_intelligence_has_kimi_k3():
    from ai_generation.provider_intelligence import ProviderIntelligenceEngine
    engine = ProviderIntelligenceEngine()
    intel = engine.get_all(provider_type="text")
    names = {i["name"] for i in intel}
    assert "kimi_k3" in names
    k3 = next(i for i in intel if i["name"] == "kimi_k3")
    assert k3["verification_status"] == "verified"
    assert k3["api_key_required"] is True
    assert "chat" in k3["capabilities"]
    assert k3["models_count"] == 3
    recommendations = engine.get_recommendations()
    rec_names = {r["name"] for r in recommendations}
    assert "kimi_k3" in rec_names


# ── Negotiation-based runtime selection ───────────────────────────

@pytest.mark.asyncio
async def test_manager_chat_negotiated(monkeypatch):
    from ai_generation.kimi_k3 import KimiK3Manager
    monkeypatch.setattr("ai_generation.kimi_k3._post_json", make_post())
    manager = KimiK3Manager()
    result = await manager.chat_negotiated("explain transformers",
                                           quality_priority="high")
    assert result.error is None
    assert result.provider.startswith("kimi_k3_")
    assert result.text == "Hello from Kimi K3"


@pytest.mark.asyncio
async def test_sdk_chat_negotiate_strategy(monkeypatch):
    from ai_generation.sdk import UncleFrappeAI
    monkeypatch.setattr("ai_generation.kimi_k3._post_json", make_post())
    ai = UncleFrappeAI()
    result = await ai.chat("hello", strategy="negotiate")
    assert result["text"] == "Hello from Kimi K3"
    assert result["provider"].startswith("kimi_k3_")


# ── Officially-not-published records ──────────────────────────────

def test_kimi_k3_not_officially_published():
    from ai_generation.kimi_k3 import KIMI_K3_SPEC
    nop = KIMI_K3_SPEC["not_officially_published"]
    for key in ("kubernetes_manifest", "memory_offload_guidance",
                "runtime_profiling_guide", "scheduler_integration",
                "continuous_batching"):
        assert key in nop
        assert nop[key]


# ── MCP health + benchmark tools ──────────────────────────────────

def test_mcp_kimi_health_and_benchmark_registered():
    from ai_generation.mcp_tools import MCP_GENERATION_TOOLS
    for name in ("kimi_k3_health", "kimi_k3_benchmark"):
        assert name in MCP_GENERATION_TOOLS


@pytest.mark.asyncio
async def test_mcp_kimi_health_handler(monkeypatch):
    from ai_generation.mcp_tools import MCPGenerationTools

    async def fake_get(url, api_key="", timeout=15.0):
        return {"data": [{"id": "moonshotai/Kimi-K3"}]}

    monkeypatch.setattr("ai_generation.kimi_k3._get_json", fake_get)
    tools = MCPGenerationTools()
    result = await tools.handle("kimi_k3_health", {})
    assert "kimi_k3_cloud" in result["health"]
    assert result["health"]["kimi_k3_cloud"]["healthy"] is True


@pytest.mark.asyncio
async def test_mcp_kimi_benchmark_handler(monkeypatch):
    from ai_generation.mcp_tools import MCPGenerationTools
    monkeypatch.setattr("ai_generation.kimi_k3._post_json", make_post())
    tools = MCPGenerationTools()
    result = await tools.handle("kimi_k3_benchmark", {
        "prompt": "hello", "runs": 1, "provider": "kimi_k3_vllm",
    })
    assert len(result["runs"]) == 1
    assert result["runs"][0]["success"] is True


# ── Kubernetes deployment manifests ───────────────────────────────

def test_build_vllm_k8s_yaml():
    from ai_generation.kimi_k3 import build_vllm_k8s_yaml
    yaml_text = build_vllm_k8s_yaml(gpus=8)
    assert "kind: Deployment" in yaml_text
    assert "name: kimi-k3-vllm" in yaml_text
    assert "image: vllm/vllm-openai:kimi-k3" in yaml_text
    assert "nvidia.com/gpu: 8" in yaml_text
    assert "--tensor-parallel-size" in yaml_text
    assert "kind: Service" in yaml_text


def test_build_sglang_k8s_yaml():
    from ai_generation.kimi_k3 import build_sglang_k8s_yaml
    yaml_text = build_sglang_k8s_yaml(gpus=8)
    assert "kind: Deployment" in yaml_text
    assert "name: kimi-k3-sglang" in yaml_text
    assert "lmsysorg/sglang:kimi-k3" in yaml_text
    assert "--reasoning-parser" in yaml_text
    assert "containerPort: 30000" in yaml_text


# ── Observability integration ─────────────────────────────────────

@pytest.mark.asyncio
async def test_manager_observability_metrics(monkeypatch):
    from ai_generation.kimi_k3 import KimiK3Manager
    from ai_generation.observability import ObservabilityManager
    monkeypatch.setattr("ai_generation.kimi_k3._post_json", make_post())
    obs = ObservabilityManager()
    manager = KimiK3Manager(observability=obs)
    await manager.chat("hello", provider="kimi_k3_vllm")
    labels = {"provider": "kimi_k3_vllm", "model": "kimi-k3"}
    assert obs.get_counter("kimi_k3.requests.total", labels) == 1
    assert obs.get_counter("kimi_k3.requests.success", labels) == 1
    latency_stats = obs.get_histogram_stats("kimi_k3.latency_ms", labels)
    assert latency_stats["count"] == 1
    assert "kimi_k3" in {l["source"] for l in obs.get_logs()}


@pytest.mark.asyncio
async def test_manager_observability_failure(monkeypatch):
    from ai_generation.kimi_k3 import KimiK3Error, KimiK3Manager
    from ai_generation.observability import ObservabilityManager

    async def fail(url, api_key, payload, timeout=120.0):
        raise KimiK3Error("down")

    monkeypatch.setattr("ai_generation.kimi_k3._post_json", fail)
    obs = ObservabilityManager()
    manager = KimiK3Manager(observability=obs)
    await manager.chat("boom")
    cloud_labels = {"provider": "kimi_k3_cloud", "model": "kimi-k3"}
    assert obs.get_counter("kimi_k3.requests.total", cloud_labels) == 1
    assert obs.get_counter("kimi_k3.requests.failed", cloud_labels) == 1


# ── Event Bus integration ────────────────────────────────────────

@pytest.mark.asyncio
async def test_manager_event_bus_success(monkeypatch):
    from ai_generation.event_bus import EventBus
    from ai_generation.kimi_k3 import KimiK3Manager
    monkeypatch.setattr("ai_generation.kimi_k3._post_json", make_post())
    bus = EventBus()
    received = []
    bus.subscribe("kimi_k3.request.complete", lambda msg: received.append(msg))
    manager = KimiK3Manager(event_bus=bus)
    result = await manager.chat("hello", provider="auto")
    assert result.error is None
    assert len(received) == 1
    payload = received[0].payload
    assert payload["provider"] == "kimi_k3_vllm"
    assert payload["quality_score"] > 0
    assert payload["reasoning_present"] is True
    # cloud attempt fails (401) -> provider.failed, vLLM -> request.complete
    assert bus.get_stats()["total_published"] == 2


@pytest.mark.asyncio
async def test_manager_event_bus_failure(monkeypatch):
    from ai_generation.event_bus import EventBus
    from ai_generation.kimi_k3 import KimiK3Error, KimiK3Manager

    async def fail(url, api_key, payload, timeout=120.0):
        raise KimiK3Error("down")

    monkeypatch.setattr("ai_generation.kimi_k3._post_json", fail)
    bus = EventBus()
    failed = []
    bus.subscribe("kimi_k3.provider.failed", lambda msg: failed.append(msg))
    manager = KimiK3Manager(event_bus=bus)
    result = await manager.chat("boom")
    assert result.error is not None
    assert [m.payload["provider"] for m in failed] == [
        "kimi_k3_cloud", "kimi_k3_vllm", "kimi_k3_sglang",
    ]
    history = bus.get_history("kimi_k3.request.failed")
    assert len(history) == 1
    assert history[0]["subject"] == "kimi_k3.request.failed"
    assert "providers_attempted" in history[0]["payload"]


@pytest.mark.asyncio
async def test_manager_event_bus_kernel(monkeypatch):
    from ai_generation.event_bus import EventDrivenKernel
    from ai_generation.kimi_k3 import KimiK3Manager
    monkeypatch.setattr("ai_generation.kimi_k3._post_json", make_post())
    kernel = EventDrivenKernel()
    received = []
    kernel.subscribe_event("kimi_k3.request.complete", lambda msg: received.append(msg))
    manager = KimiK3Manager(event_bus=kernel)
    result = await manager.chat("hello", provider="auto")
    assert result.error is None
    assert len(received) == 1
    assert received[0].headers.get("source") == "kimi_k3"
    assert kernel.get_stats()["total_events_emitted"] == 2


@pytest.mark.asyncio
async def test_sdk_chat_publishes_event_bus_events(monkeypatch):
    from ai_generation.sdk import UncleFrappeAI
    monkeypatch.setattr("ai_generation.kimi_k3._post_json", make_post())
    ai = UncleFrappeAI()
    result = await ai.chat("hello", provider="kimi_k3_vllm")
    assert result.get("error") is None
    history = ai.event_bus.get_history("kimi_k3.request.complete")
    assert len(history) == 1
    assert "kimi_k3_vllm" in history[0]["payload"]


# ── Agent Interface ──────────────────────────────────────────────

@pytest.mark.asyncio
async def test_agent_interface_chat(monkeypatch):
    from ai_generation.agent_interface import AgentInterface
    monkeypatch.setattr("ai_generation.kimi_k3._post_json", make_post())
    agent = AgentInterface()
    result = await agent.chat("hello kimi", provider="kimi_k3_vllm",
                              reasoning_effort="low")
    assert result["text"] == "Hello from Kimi K3"
    assert result["provider"] == "kimi_k3_vllm"
    assert result["quality_score"] > 0


@pytest.mark.asyncio
async def test_agent_interface_chat_negotiate(monkeypatch):
    from ai_generation.agent_interface import AgentInterface
    monkeypatch.setattr("ai_generation.kimi_k3._post_json", make_post())
    agent = AgentInterface()
    result = await agent.chat("hello", strategy="negotiate")
    assert result["text"] == "Hello from Kimi K3"
    assert result["provider"].startswith("kimi_k3_")


def test_agent_interface_kimi_info_and_stats():
    from ai_generation.agent_interface import AgentInterface
    agent = AgentInterface()
    info = agent.kimi_k3_info()
    assert info["spec"]["context_length"] == 1048576
    stats = agent.get_stats()
    assert "kimi_k3" in stats
    assert stats["kimi_k3"]["total_requests"] == 0


@pytest.mark.asyncio
async def test_agent_interface_event_bus_events(monkeypatch):
    from ai_generation.agent_interface import AgentInterface
    monkeypatch.setattr("ai_generation.kimi_k3._post_json", make_post())
    agent = AgentInterface()
    result = await agent.chat("hello", provider="kimi_k3_vllm")
    assert result.get("error") is None
    history = agent.event_bus.get_history("kimi_k3.request.complete")
    assert len(history) == 1
    assert "kimi_k3_vllm" in history[0]["payload"]


# ── Local Runtime Registry (Kimi K3 awareness) ───────────────────

def test_local_runtimes_kimi_k3_vllm_plan():
    from ai_generation.local_runtimes import LocalRuntimeManager, RuntimeType
    mgr = LocalRuntimeManager()
    plan = mgr.configure_kimi_k3_runtime(
        RuntimeType.VLLM, url="http://gpu-01:8000", hardware="blackwell",
        tensor_parallel=8, expert_parallel=16, spec_decode=True,
    )
    assert plan["model"] == "kimi-k3"
    assert plan["model_id"] == "moonshotai/Kimi-K3"
    assert plan["context_length"] == 1048576
    assert plan["min_gpus"] == 8
    assert plan["min_vram_gb"] == 1680
    assert plan["launch"]["engine"] == "vllm"
    assert "kimi-k3" in plan["launch"]["image"]
    assert "--tensor-parallel-size" in plan["launch"]["command"]
    cmd = plan["launch"]["command"]
    spec_idx = cmd.index("--speculative-config")
    assert "Inferact/Kimi-K3-DSpark" in cmd[spec_idx + 1]
    assert mgr.get_kimi_k3_plans()["vllm"]["model"] == "kimi-k3"


def test_local_runtimes_kimi_k3_sglang_plan():
    from ai_generation.local_runtimes import LocalRuntimeManager, RuntimeType
    mgr = LocalRuntimeManager()
    plan = mgr.configure_kimi_k3_runtime(
        RuntimeType.SGLANG, url="http://gpu-01:30000", hardware="b200",
    )
    assert plan["launch"]["engine"] == "sglang"
    assert "lmsysorg/sglang:kimi-k3" in plan["launch"]["image"]
    assert "--reasoning-parser" in plan["launch"]["command"]
    assert set(mgr.get_kimi_k3_plans()) == {"sglang"}


def test_local_runtimes_kimi_k3_invalid_runtime():
    from ai_generation.local_runtimes import LocalRuntimeManager, RuntimeType
    mgr = LocalRuntimeManager()
    with pytest.raises(ValueError):
        mgr.configure_kimi_k3_runtime(RuntimeType.OLLAMA, url="http://x:11434")


# ── Supervision + regression detection integration ───────────────

def test_kimi_k3_supervisor_workers_healthy(monkeypatch):
    from ai_generation.kimi_k3 import (
        KimiK3Manager, register_kimi_k3_supervisor_workers,
    )
    from ai_generation.supervisor import SupervisorTree

    async def fake_get(url, api_key="", timeout=15.0):
        return {"data": [{"id": "moonshotai/Kimi-K3"}]}

    monkeypatch.setattr("ai_generation.kimi_k3._get_json", fake_get)
    tree = SupervisorTree(name="kimi_k3_test")
    manager = KimiK3Manager()
    worker_ids = register_kimi_k3_supervisor_workers(tree, manager=manager)
    assert len(worker_ids) == 3
    for wid in worker_ids:
        result = tree.run_worker(wid)
        assert result["healthy"] is True
        state = tree.get_worker_state(wid)
        assert state["status"] in ("idle", "running", "stopped")
        assert state["total_failures"] == 0


def test_kimi_k3_supervisor_workers_unhealthy(monkeypatch):
    from ai_generation.kimi_k3 import (
        KimiK3Manager, register_kimi_k3_supervisor_workers,
    )
    from ai_generation.supervisor import (
        SupervisorConfig, SupervisorTree, WorkerCrashError,
    )

    async def fake_get(url, api_key="", timeout=15.0):
        return {"data": []}

    monkeypatch.setattr("ai_generation.kimi_k3._get_json", fake_get)
    tree = SupervisorTree(
        name="kimi_k3_test",
        config=SupervisorConfig(
            max_restarts=1, restart_interval_secs=1.0,
            initial_backoff_secs=0.01, exponential_backoff_base=1.0,
        ),
    )
    manager = KimiK3Manager()
    worker_ids = register_kimi_k3_supervisor_workers(tree, manager=manager)
    with pytest.raises(WorkerCrashError):
        tree.run_worker(worker_ids[0])
    state = tree.get_worker_state(worker_ids[0])
    assert state["status"] == "stopped"
    assert state["total_failures"] == 2


def test_record_kimi_k3_regression_baseline_and_detect():
    from ai_generation.kimi_k3 import record_kimi_k3_regression
    from ai_generation.regression_detector import RegressionDetector

    detector = RegressionDetector()
    first = {
        "prompt": "test",
        "runs": [
            {"provider": "kimi_k3_vllm", "success": True, "latency_ms": 100.0,
             "quality_score": 90.0},
            {"provider": "kimi_k3_vllm", "success": True, "latency_ms": 120.0,
             "quality_score": 88.0},
        ],
    }
    alerts = record_kimi_k3_regression(detector, first)
    assert alerts == []
    baseline = detector.get_baseline("kimi_k3_vllm")
    assert baseline["latency_p50"] == 120.0
    assert baseline["quality_score"] == 89.0

    bad = {
        "prompt": "test",
        "runs": [
            {"provider": "kimi_k3_vllm", "success": True, "latency_ms": 500.0,
             "quality_score": 40.0},
        ],
    }
    alerts = record_kimi_k3_regression(detector, bad)
    assert len(alerts) >= 2
    assert len(detector.get_provider_history("kimi_k3_vllm")) == 2


# ── Generation Manager / TEXT provider integration ───────────────

def test_kimi_k3_text_provider_registered():
    from ai_generation.providers.base import ProviderType, TextProvider
    from ai_generation.providers.registry import get_registry
    registry = get_registry()
    provider = registry.get("kimi_k3")
    assert provider is not None
    assert isinstance(provider, TextProvider)
    assert provider.provider_type == ProviderType.TEXT
    assert provider.supported_models == ["kimi-k3"]


@pytest.mark.asyncio
async def test_kimi_k3_text_provider_direct(monkeypatch):
    from ai_generation.providers.kimi_k3_provider import KimiK3TextProvider
    monkeypatch.setattr("ai_generation.kimi_k3._post_json", make_post())
    provider = KimiK3TextProvider()
    result = await provider.generate_text("hi", provider="kimi_k3_vllm")
    assert result.status == "success"
    assert result.metadata["text"] == "Hello from Kimi K3"
    assert result.metadata["reasoning"]
    assert provider.success_rate == 100.0


@pytest.mark.asyncio
async def test_kimi_k3_text_provider_error(monkeypatch):
    from ai_generation.kimi_k3 import KimiK3Error
    from ai_generation.providers.kimi_k3_provider import KimiK3TextProvider

    async def fail(url, api_key, payload, timeout=120.0):
        raise KimiK3Error("down")

    monkeypatch.setattr("ai_generation.kimi_k3._post_json", fail)
    provider = KimiK3TextProvider()
    result = await provider.generate_text("boom")
    assert result.status == "error"
    assert provider.success_rate == 0.0


@pytest.mark.asyncio
async def test_generation_manager_generate_text(monkeypatch):
    from ai_generation.generation_manager import GenerationManager
    monkeypatch.setattr("ai_generation.kimi_k3._post_json", make_post())
    monkeypatch.setenv("MOONSHOT_API_KEY", "test-key")
    manager = GenerationManager()
    result = await manager.generate_text("hello kimi")
    assert result.status == "success"
    assert result.metadata["text"] == "Hello from Kimi K3"
    assert result.metadata["reasoning"]
    assert result.latency_ms >= 0


# ── CLI health + benchmark commands ──────────────────────────────

def test_cli_kimi_health(capsys, monkeypatch):
    from ai_generation.cli import cmd_kimi_health

    async def fake_get(url, api_key="", timeout=15.0):
        return {"data": [{"id": "moonshotai/Kimi-K3"}]}

    monkeypatch.setattr("ai_generation.kimi_k3._get_json", fake_get)
    asyncio.run(cmd_kimi_health())
    out = capsys.readouterr().out
    assert "Kimi K3 endpoint health" in out
    assert "kimi_k3_cloud" in out
    assert "OK" in out


def test_cli_kimi_benchmark(capsys, monkeypatch):
    from ai_generation.cli import cmd_kimi_benchmark
    monkeypatch.setattr("ai_generation.kimi_k3._post_json", make_post())
    asyncio.run(cmd_kimi_benchmark("hi", runs=1, provider="kimi_k3_vllm",
                                   reasoning_effort="low"))
    out = capsys.readouterr().out
    assert "run 1: OK" in out
    assert "kimi_k3_vllm" in out


# ── SDK graph wiring (Knowledge + Capability graphs) ─────────────

def test_sdk_knowledge_graph_includes_kimi_k3():
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    kg = ai.knowledge_graph
    assert kg.get_node("provider:kimi_k3") is not None
    assert kg.get_node("model:kimi-k3") is not None
    assert kg.get_node("capability:chat") is not None


def test_sdk_capability_graph_includes_kimi_k3():
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    cg = ai.capability_graph
    for pid in ("kimi_k3_cloud", "kimi_k3_vllm", "kimi_k3_sglang"):
        assert cg.get_node(pid) is not None
    assert cg.get_node("chat") is not None
