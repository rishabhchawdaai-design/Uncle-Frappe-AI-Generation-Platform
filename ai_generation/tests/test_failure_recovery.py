"""
Phase 28 Tests — Failure Recovery System

Tests GPU OOM, Runtime Crash, GPU Crash, and NaN/Inf recovery playbooks.
"""
import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))


# ── FailureType Enum Tests ────────────────────────────────────

def test_failure_type_enum():
    from ai_generation.failure_recovery import FailureType
    assert FailureType.GPU_OOM.value == "gpu_oom"
    assert FailureType.GPU_CRASH.value == "gpu_crash"
    assert FailureType.RUNTIME_CRASH.value == "runtime_crash"
    assert FailureType.NAN_INF.value == "nan_inf"
    assert FailureType.UNKNOWN.value == "unknown"


def test_recovery_step_enum():
    from ai_generation.failure_recovery import RecoveryStep
    assert RecoveryStep.LOG_FAILURE.value == "log_failure"
    assert RecoveryStep.REDUCE_BATCH.value == "reduce_batch"
    assert RecoveryStep.REPORT_FAILURE.value == "report_failure"


# ── RecoveryResult Tests ─────────────────────────────────────

def test_recovery_result_defaults():
    from ai_generation.failure_recovery import RecoveryResult
    r = RecoveryResult()
    assert r.success is False
    assert r.recovered is False
    assert r.fallback_used is False
    assert r.steps_attempted == []
    assert r.error is None


def test_recovery_result_to_dict():
    from ai_generation.failure_recovery import RecoveryResult, FailureType
    r = RecoveryResult(
        success=True,
        failure_type=FailureType.GPU_OOM,
        steps_attempted=["log_failure", "reduce_batch"],
        steps_succeeded=["log_failure"],
        recovered=True,
        final_action="Reduced batch size",
        duration_secs=0.5,
    )
    d = r.to_dict()
    assert d["success"] is True
    assert d["failure_type"] == "gpu_oom"
    assert d["recovered"] is True
    assert len(d["steps_attempted"]) == 2
    assert d["duration_secs"] == 0.5


# ── FailureRecoveryEngine Tests ───────────────────────────────

def test_engine_init():
    from ai_generation.failure_recovery import FailureRecoveryEngine
    engine = FailureRecoveryEngine()
    stats = engine.get_stats()
    assert stats["total_recovery_attempts"] == 0
    assert stats["successful_recoveries"] == 0
    assert stats["failed_recoveries"] == 0
    assert stats["total_events"] == 0


def test_engine_init_with_config():
    from ai_generation.failure_recovery import FailureRecoveryEngine
    engine = FailureRecoveryEngine({"max_retries": 5, "enable_quantization": False})
    assert engine._max_retries == 5
    assert engine._enable_quantization is False


# ── GPU OOM Detection ─────────────────────────────────────────

def test_detect_gpu_oom_cuda():
    from ai_generation.failure_recovery import FailureRecoveryEngine
    engine = FailureRecoveryEngine()
    assert engine.detect_gpu_oom("CUDA out of memory")
    assert engine.detect_gpu_oom("RuntimeError: CUDA out of memory")
    assert engine.detect_gpu_oom("torch.cuda.OutOfMemoryError")
    assert engine.detect_gpu_oom("cudaMalloc failed: out of memory")


def test_detect_gpu_oom_generic():
    from ai_generation.failure_recovery import FailureRecoveryEngine
    engine = FailureRecoveryEngine()
    assert engine.detect_gpu_oom("Out of Memory")
    assert engine.detect_gpu_oom("OOM on GPU 0")


def test_detect_gpu_oom_false_positive():
    from ai_generation.failure_recovery import FailureRecoveryEngine
    engine = FailureRecoveryEngine()
    assert not engine.detect_gpu_oom("Connection timeout")
    assert not engine.detect_gpu_oom("Invalid API key")
    assert not engine.detect_gpu_oom("")


# ── GPU OOM Recovery ──────────────────────────────────────────

def test_recover_gpu_oom_reduces_batch():
    from ai_generation.failure_recovery import FailureRecoveryEngine
    engine = FailureRecoveryEngine()
    context = {
        "model": "flux",
        "batch_size": 4,
        "vram_gb": 8,
        "error": "CUDA out of memory",
        "oom_batch_threshold": 2,
    }
    result = engine.recover_gpu_oom(context)
    assert result.success is True
    assert result.recovered is True
    assert "reduce_batch" in result.steps_attempted
    assert result.diagnostics.get("reduced_batch_size") == 2


def test_recover_gpu_oom_int8():
    from ai_generation.failure_recovery import FailureRecoveryEngine
    engine = FailureRecoveryEngine()
    context = {
        "model": "flux",
        "batch_size": 1,
        "vram_gb": 8,
        "error": "CUDA out of memory",
        "supports_int8": True,
        "oom_batch_threshold": 0,
    }
    result = engine.recover_gpu_oom(context)
    assert result.success is True
    assert result.recovered is True
    assert "quantize_int8" in result.steps_succeeded
    assert result.diagnostics.get("quantization") == "int8"


def test_recover_gpu_oom_int4():
    from ai_generation.failure_recovery import FailureRecoveryEngine
    engine = FailureRecoveryEngine()
    context = {
        "model": "flux",
        "batch_size": 1,
        "vram_gb": 8,
        "error": "CUDA out of memory",
        "supports_int4": True,
        "oom_batch_threshold": 0,
    }
    result = engine.recover_gpu_oom(context)
    assert result.success is True
    assert result.recovered is True
    assert "quantize_int4" in result.steps_succeeded
    assert result.diagnostics.get("quantization") == "int4"


def test_recover_gpu_oom_smaller_model():
    from ai_generation.failure_recovery import FailureRecoveryEngine
    engine = FailureRecoveryEngine()
    context = {
        "model": "flux-pro",
        "batch_size": 1,
        "vram_gb": 8,
        "error": "CUDA out of memory",
        "smaller_model": "flux-schnell",
        "oom_batch_threshold": 0,
    }
    result = engine.recover_gpu_oom(context)
    assert result.success is True
    assert result.recovered is True
    assert result.fallback_used is True
    assert result.diagnostics.get("smaller_model") == "flux-schnell"


def test_recover_gpu_oom_cpu_offload():
    from ai_generation.failure_recovery import FailureRecoveryEngine
    engine = FailureRecoveryEngine()
    context = {
        "model": "flux",
        "batch_size": 1,
        "vram_gb": 8,
        "error": "CUDA out of memory",
        "supports_cpu_offload": True,
        "oom_batch_threshold": 0,
    }
    result = engine.recover_gpu_oom(context)
    assert result.success is True
    assert result.recovered is True
    assert result.fallback_used is True
    assert "cpu_offload" in result.steps_succeeded


def test_recover_gpu_oom_alternative_gpu():
    from ai_generation.failure_recovery import FailureRecoveryEngine
    engine = FailureRecoveryEngine()
    context = {
        "model": "flux",
        "batch_size": 1,
        "vram_gb": 8,
        "error": "CUDA out of memory",
        "alternative_gpu": "A100-80GB",
        "oom_batch_threshold": 0,
    }
    result = engine.recover_gpu_oom(context)
    assert result.success is True
    assert result.recovered is True
    assert result.diagnostics.get("alternative_gpu") == "A100-80GB"


def test_recover_gpu_oom_all_steps_exhausted():
    from ai_generation.failure_recovery import FailureRecoveryEngine
    engine = FailureRecoveryEngine()
    context = {
        "model": "huge-model",
        "batch_size": 1,
        "vram_gb": 8,
        "error": "CUDA out of memory",
        "oom_batch_threshold": 0,
    }
    result = engine.recover_gpu_oom(context)
    assert result.success is False
    assert result.recovered is False
    assert result.error is not None
    assert "all steps exhausted" in result.error


# ── GPU Crash Detection ───────────────────────────────────────

def test_detect_gpu_crash():
    from ai_generation.failure_recovery import FailureRecoveryEngine
    engine = FailureRecoveryEngine()
    assert engine.detect_gpu_crash("nvidia-smi timeout")
    assert engine.detect_gpu_crash("CUDA error: unspecified")
    assert engine.detect_gpu_crash("Xid 79: GPU has fallen off the bus")


def test_detect_gpu_crash_false():
    from ai_generation.failure_recovery import FailureRecoveryEngine
    engine = FailureRecoveryEngine()
    assert not engine.detect_gpu_crash("Out of memory")
    assert not engine.detect_gpu_crash("")


# ── GPU Crash Recovery ────────────────────────────────────────

def test_recover_gpu_crash_reset():
    from ai_generation.failure_recovery import FailureRecoveryEngine
    engine = FailureRecoveryEngine()
    context = {
        "gpu_id": "GPU-0",
        "error": "nvidia-smi timeout",
        "active_tasks": ["task-1", "task-2"],
        "gpu_reset_supported": True,
    }
    result = engine.recover_gpu_crash(context)
    assert result.success is True
    assert result.recovered is True
    assert "reset_device" in result.steps_succeeded
    assert result.diagnostics.get("reset_attempted") is True


def test_recover_gpu_crash_reassign():
    from ai_generation.failure_recovery import FailureRecoveryEngine
    engine = FailureRecoveryEngine()
    context = {
        "gpu_id": "GPU-0",
        "error": "nvidia-smi timeout",
        "active_tasks": ["task-1"],
        "gpu_reset_supported": False,
        "healthy_gpus": ["GPU-1", "GPU-2"],
    }
    result = engine.recover_gpu_crash(context)
    assert result.success is True
    assert result.recovered is True
    assert "reassign_tasks" in result.steps_succeeded
    assert "GPU-1" in result.diagnostics.get("reassigned_to", [])


def test_recover_gpu_crash_queue():
    from ai_generation.failure_recovery import FailureRecoveryEngine
    engine = FailureRecoveryEngine()
    context = {
        "gpu_id": "GPU-0",
        "error": "nvidia-smi timeout",
        "active_tasks": ["task-1"],
        "gpu_reset_supported": False,
        "healthy_gpus": [],
        "backoff_secs": 30,
    }
    result = engine.recover_gpu_crash(context)
    assert result.success is True
    assert result.recovered is False
    assert "queue_backoff" in result.steps_succeeded
    assert result.diagnostics.get("queued") is True


# ── Runtime Crash Detection ───────────────────────────────────

def test_detect_runtime_crash():
    from ai_generation.failure_recovery import FailureRecoveryEngine
    engine = FailureRecoveryEngine()
    assert engine.detect_runtime_crash("process exited unexpectedly")
    assert engine.detect_runtime_crash("connection refused")
    assert engine.detect_runtime_crash("SIGSEGV")
    assert engine.detect_runtime_crash("heartbeat timeout")


def test_detect_runtime_crash_false():
    from ai_generation.failure_recovery import FailureRecoveryEngine
    engine = FailureRecoveryEngine()
    assert not engine.detect_runtime_crash("CUDA out of memory")
    assert not engine.detect_runtime_crash("")


# ── Runtime Crash Recovery ────────────────────────────────────

def test_recover_runtime_crash_restart():
    from ai_generation.failure_recovery import FailureRecoveryEngine
    engine = FailureRecoveryEngine()
    context = {
        "runtime_id": "vllm-0",
        "model": "llama-3-70b",
        "error": "process exited with SIGSEGV",
        "can_restart": True,
        "active_tasks": 3,
    }
    result = engine.recover_runtime_crash(context)
    assert result.success is True
    assert result.recovered is True
    assert "restart_runtime" in result.steps_succeeded
    assert "reload_model" in result.steps_succeeded
    assert "reassign_tasks" in result.steps_succeeded
    assert result.diagnostics.get("model_reloaded") == "llama-3-70b"


def test_recover_runtime_crash_fallback():
    from ai_generation.failure_recovery import FailureRecoveryEngine
    engine = FailureRecoveryEngine()
    context = {
        "runtime_id": "vllm-0",
        "model": "llama-3-70b",
        "error": "process exited",
        "can_restart": False,
        "fallback_runtime": "llama.cpp-0",
        "active_tasks": 2,
    }
    result = engine.recover_runtime_crash(context)
    assert result.success is True
    assert result.recovered is True
    assert result.fallback_used is True
    assert result.diagnostics.get("fallback_runtime") == "llama.cpp-0"


def test_recover_runtime_crash_failure():
    from ai_generation.failure_recovery import FailureRecoveryEngine
    engine = FailureRecoveryEngine()
    context = {
        "runtime_id": "vllm-0",
        "model": "llama-3-70b",
        "error": "process exited",
        "can_restart": False,
        "active_tasks": 2,
    }
    result = engine.recover_runtime_crash(context)
    assert result.success is False
    assert result.recovered is False
    assert result.error is not None


# ── NaN/Inf Detection ─────────────────────────────────────────

def test_detect_nan_inf():
    from ai_generation.failure_recovery import FailureRecoveryEngine
    engine = FailureRecoveryEngine()
    assert engine.detect_nan_inf({"has_nan": True, "has_inf": False})
    assert engine.detect_nan_inf({"has_nan": False, "has_inf": True})
    assert engine.detect_nan_inf({"has_nan": True, "has_inf": True})
    assert not engine.detect_nan_inf({"has_nan": False, "has_inf": False})


# ── NaN/Inf Recovery ──────────────────────────────────────────

def test_recover_nan_inf_recompute():
    from ai_generation.failure_recovery import FailureRecoveryEngine
    engine = FailureRecoveryEngine()
    context = {
        "has_nan": True,
        "has_inf": False,
        "layer": "attention",
        "step": 10,
        "can_recompute": True,
    }
    result = engine.recover_nan_inf(context)
    assert result.success is True
    assert result.recovered is True
    assert "recompute" in result.steps_succeeded


def test_recover_nan_inf_truncate():
    from ai_generation.failure_recovery import FailureRecoveryEngine
    engine = FailureRecoveryEngine()
    context = {
        "has_nan": True,
        "has_inf": False,
        "layer": "attention",
        "step": 10,
        "can_recompute": False,
        "can_truncate": True,
    }
    result = engine.recover_nan_inf(context)
    assert result.success is True
    assert result.recovered is True
    assert "truncate_sequence" in result.steps_succeeded


def test_recover_nan_inf_clip():
    from ai_generation.failure_recovery import FailureRecoveryEngine
    engine = FailureRecoveryEngine()
    context = {
        "has_nan": True,
        "has_inf": False,
        "layer": "attention",
        "step": 10,
        "can_clip": True,
    }
    result = engine.recover_nan_inf(context)
    assert result.success is True
    assert result.recovered is True
    assert "clip_gradients" in result.steps_succeeded


def test_recover_nan_inf_regularize():
    from ai_generation.failure_recovery import FailureRecoveryEngine
    engine = FailureRecoveryEngine()
    context = {
        "has_nan": True,
        "has_inf": False,
        "layer": "attention",
        "step": 10,
        "can_regularize": True,
    }
    result = engine.recover_nan_inf(context)
    assert result.success is True
    assert result.recovered is True
    assert "regularize" in result.steps_succeeded


def test_recover_nan_inf_failure():
    from ai_generation.failure_recovery import FailureRecoveryEngine
    engine = FailureRecoveryEngine()
    context = {
        "has_nan": True,
        "has_inf": False,
        "layer": "attention",
        "step": 10,
    }
    result = engine.recover_nan_inf(context)
    assert result.success is False
    assert result.recovered is False
    assert result.error is not None


# ── Attempt Recovery (Auto-Detect) ────────────────────────────

def test_attempt_recovery_gpu_oom():
    from ai_generation.failure_recovery import FailureRecoveryEngine
    engine = FailureRecoveryEngine()
    context = {"model": "flux", "batch_size": 4, "vram_gb": 8, "oom_batch_threshold": 2}
    result = engine.attempt_recovery("CUDA out of memory", context)
    assert result.success is True
    assert result.failure_type.value == "gpu_oom"


def test_attempt_recovery_runtime_crash():
    from ai_generation.failure_recovery import FailureRecoveryEngine
    engine = FailureRecoveryEngine()
    context = {"runtime_id": "vllm-0", "can_restart": True, "model": "test", "active_tasks": 0}
    result = engine.attempt_recovery("process exited with SIGSEGV", context)
    assert result.success is True
    assert result.failure_type.value == "runtime_crash"


def test_attempt_recovery_unknown():
    from ai_generation.failure_recovery import FailureRecoveryEngine
    engine = FailureRecoveryEngine()
    context = {}
    result = engine.attempt_recovery("some random error", context)
    assert result.success is False
    assert result.failure_type.value == "unknown"


# ── Stats & Events ────────────────────────────────────────────

def test_stats_after_recovery():
    from ai_generation.failure_recovery import FailureRecoveryEngine
    engine = FailureRecoveryEngine()
    context = {"model": "flux", "batch_size": 4, "vram_gb": 8, "oom_batch_threshold": 2}
    engine.attempt_recovery("CUDA out of memory", context)
    stats = engine.get_stats()
    assert stats["total_recovery_attempts"] == 1
    assert stats["successful_recoveries"] == 1
    assert stats["recovery_rate"] == 100.0


def test_get_events():
    from ai_generation.failure_recovery import FailureRecoveryEngine
    engine = FailureRecoveryEngine()
    context = {"model": "flux", "batch_size": 4, "vram_gb": 8, "oom_batch_threshold": 2}
    engine.attempt_recovery("CUDA out of memory", context)
    events = engine.get_events()
    assert len(events) == 1
    assert events[0]["failure_type"] == "gpu_oom"


def test_get_events_filtered():
    from ai_generation.failure_recovery import FailureRecoveryEngine
    engine = FailureRecoveryEngine()
    engine.attempt_recovery("CUDA out of memory", {"batch_size": 4, "oom_batch_threshold": 2})
    engine.attempt_recovery("process exited", {"can_restart": True})
    events = engine.get_events(failure_type="runtime_crash")
    assert len(events) == 1
    assert events[0]["failure_type"] == "runtime_crash"


def test_get_event_summary():
    from ai_generation.failure_recovery import FailureRecoveryEngine
    engine = FailureRecoveryEngine()
    engine.attempt_recovery("CUDA out of memory", {"batch_size": 4, "oom_batch_threshold": 2})
    summary = engine.get_event_summary()
    assert summary["total_events"] == 1
    assert summary["recent_count"] >= 1


def test_reset_stats():
    from ai_generation.failure_recovery import FailureRecoveryEngine
    engine = FailureRecoveryEngine()
    engine.attempt_recovery("CUDA out of memory", {"batch_size": 4, "oom_batch_threshold": 2})
    engine.reset_stats()
    stats = engine.get_stats()
    assert stats["total_recovery_attempts"] == 0
    assert stats["total_events"] == 0


def test_event_type_counts():
    from ai_generation.failure_recovery import FailureRecoveryEngine
    engine = FailureRecoveryEngine()
    engine.attempt_recovery("CUDA out of memory", {"batch_size": 4, "oom_batch_threshold": 2})
    engine.attempt_recovery("process exited", {"can_restart": True})
    counts = engine._get_event_type_counts()
    assert counts.get("gpu_oom") == 1
    assert counts.get("runtime_crash") == 1


# ── SDK Integration Tests ─────────────────────────────────────

def test_sdk_failure_recovery_import():
    from ai_generation.sdk import UncleFrappeAI
    sdk = UncleFrappeAI({"test_mode": True})
    assert sdk.failure_recovery is not None
    stats = sdk.get_failure_recovery_stats()
    assert stats["total_recovery_attempts"] == 0


def test_sdk_attempt_recovery():
    from ai_generation.sdk import UncleFrappeAI
    sdk = UncleFrappeAI({"test_mode": True})
    result = sdk.attempt_recovery(
        "CUDA out of memory",
        {"model": "flux", "batch_size": 4, "vram_gb": 8, "oom_batch_threshold": 2},
    )
    assert result["success"] is True
    assert result["failure_type"] == "gpu_oom"


def test_sdk_detect_failure_type():
    from ai_generation.sdk import UncleFrappeAI
    sdk = UncleFrappeAI({"test_mode": True})
    assert sdk.detect_failure_type("CUDA out of memory") == "gpu_oom"
    assert sdk.detect_failure_type("SIGSEGV") == "runtime_crash"
    assert sdk.detect_failure_type("nvidia-smi timeout") == "gpu_crash"
    assert sdk.detect_failure_type("unknown error") == "unknown"


def test_sdk_recover_gpu_oom():
    from ai_generation.sdk import UncleFrappeAI
    sdk = UncleFrappeAI({"test_mode": True})
    result = sdk.recover_gpu_oom(
        {"model": "flux", "batch_size": 4, "vram_gb": 8, "oom_batch_threshold": 2}
    )
    assert result["success"] is True
    assert "reduce_batch" in result["steps_attempted"]


def test_sdk_recover_runtime_crash():
    from ai_generation.sdk import UncleFrappeAI
    sdk = UncleFrappeAI({"test_mode": True})
    result = sdk.recover_runtime_crash(
        {"runtime_id": "test", "can_restart": True, "model": "test", "active_tasks": 0}
    )
    assert result["success"] is True


def test_sdk_recover_gpu_crash():
    from ai_generation.sdk import UncleFrappeAI
    sdk = UncleFrappeAI({"test_mode": True})
    result = sdk.recover_gpu_crash(
        {"gpu_id": "GPU-0", "gpu_reset_supported": True, "active_tasks": []}
    )
    assert result["success"] is True


def test_sdk_recover_nan_inf():
    from ai_generation.sdk import UncleFrappeAI
    sdk = UncleFrappeAI({"test_mode": True})
    result = sdk.recover_nan_inf(
        {"has_nan": True, "has_inf": False, "layer": "test", "step": 1, "can_recompute": True}
    )
    assert result["success"] is True


def test_sdk_get_failure_events():
    from ai_generation.sdk import UncleFrappeAI
    sdk = UncleFrappeAI({"test_mode": True})
    events = sdk.get_failure_events()
    assert isinstance(events, list)


def test_sdk_get_failure_summary():
    from ai_generation.sdk import UncleFrappeAI
    sdk = UncleFrappeAI({"test_mode": True})
    summary = sdk.get_failure_summary()
    assert summary["total_events"] >= 0


# ── MCP Tool Tests ────────────────────────────────────────────

def test_mcp_failure_tools_exist():
    from ai_generation.mcp_tools import MCP_GENERATION_TOOLS
    assert "attempt_recovery" in MCP_GENERATION_TOOLS
    assert "recover_gpu_oom" in MCP_GENERATION_TOOLS
    assert "recover_runtime_crash" in MCP_GENERATION_TOOLS
    assert "recover_gpu_crash" in MCP_GENERATION_TOOLS
    assert "recover_nan_inf" in MCP_GENERATION_TOOLS
    assert "get_failure_events" in MCP_GENERATION_TOOLS
    assert "get_failure_recovery_stats" in MCP_GENERATION_TOOLS


def test_mcp_failure_handler_import():
    from ai_generation.mcp_tools import MCPGenerationTools
    tools = MCPGenerationTools()
    assert hasattr(tools, "_handle_attempt_recovery")
    assert hasattr(tools, "_handle_recover_gpu_oom")
    assert hasattr(tools, "_handle_recover_runtime_crash")
    assert hasattr(tools, "_handle_recover_gpu_crash")
    assert hasattr(tools, "_handle_recover_nan_inf")
    assert hasattr(tools, "_handle_get_failure_events")
    assert hasattr(tools, "_handle_get_failure_recovery_stats")


# ── Edge Cases ────────────────────────────────────────────────

def test_empty_error_detection():
    from ai_generation.failure_recovery import FailureRecoveryEngine
    engine = FailureRecoveryEngine()
    assert not engine.detect_gpu_oom("")
    assert not engine.detect_gpu_crash("")
    assert not engine.detect_runtime_crash("")


def test_max_events_limit():
    from ai_generation.failure_recovery import FailureRecoveryEngine
    engine = FailureRecoveryEngine({"max_events": 2})
    for i in range(5):
        engine.attempt_recovery("CUDA out of memory", {"batch_size": 4, "oom_batch_threshold": 2})
    assert len(engine._events) == 2


def test_quantization_disabled():
    from ai_generation.failure_recovery import FailureRecoveryEngine
    engine = FailureRecoveryEngine({"enable_quantization": False})
    context = {
        "model": "flux",
        "batch_size": 1,
        "vram_gb": 8,
        "error": "CUDA out of memory",
        "supports_int8": True,
        "oom_batch_threshold": 0,
    }
    result = engine.recover_gpu_oom(context)
    # Should skip quantization steps entirely
    assert "quantize_int8" not in result.steps_attempted
    assert "quantize_int4" not in result.steps_attempted


def test_cpu_offload_disabled():
    from ai_generation.failure_recovery import FailureRecoveryEngine
    engine = FailureRecoveryEngine({"enable_cpu_offload": False})
    context = {
        "model": "flux",
        "batch_size": 1,
        "vram_gb": 8,
        "error": "CUDA out of memory",
        "supports_cpu_offload": True,
        "oom_batch_threshold": 0,
    }
    result = engine.recover_gpu_oom(context)
    assert "cpu_offload" not in result.steps_attempted


def test_multiple_recovery_types():
    from ai_generation.failure_recovery import FailureRecoveryEngine
    engine = FailureRecoveryEngine()
    engine.attempt_recovery("CUDA out of memory", {"batch_size": 4, "oom_batch_threshold": 2})
    engine.attempt_recovery("SIGSEGV", {"can_restart": True})
    engine.attempt_recovery("nvidia-smi timeout", {"gpu_reset_supported": True})
    stats = engine.get_stats()
    assert stats["total_recovery_attempts"] == 3
    assert stats["successful_recoveries"] == 3

    types = set(e["failure_type"] for e in engine.get_events())
    assert "gpu_oom" in types
    assert "runtime_crash" in types
    assert "gpu_crash" in types
