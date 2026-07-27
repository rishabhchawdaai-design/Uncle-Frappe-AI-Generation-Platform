"""
Phase 21 Tests — Observability Layer

Tests metrics, traces, logs, generation tracking, and SDK/MCP exposure.
"""
import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))


# ── ObservabilityManager Tests ───────────────────────────────

def test_observability_manager_import():
    from ai_generation.observability import ObservabilityManager
    obs = ObservabilityManager()
    assert obs is not None


def test_default_metrics():
    from ai_generation.observability import ObservabilityManager
    obs = ObservabilityManager()
    assert obs.get_counter("generation_requests_total") == 0
    assert obs.get_counter("generation_success_total") == 0
    assert obs.get_counter("generation_failure_total") == 0


def test_counter_increment():
    from ai_generation.observability import ObservabilityManager
    obs = ObservabilityManager()
    obs.increment_counter("test_counter")
    assert obs.get_counter("test_counter") == 1.0
    obs.increment_counter("test_counter", 5.0)
    assert obs.get_counter("test_counter") == 6.0


def test_counter_with_labels():
    from ai_generation.observability import ObservabilityManager
    obs = ObservabilityManager()
    obs.increment_counter("requests", labels={"provider": "openai"})
    obs.increment_counter("requests", labels={"provider": "openai"})
    obs.increment_counter("requests", labels={"provider": "anthropic"})
    assert obs.get_counter("requests", labels={"provider": "openai"}) == 2.0
    assert obs.get_counter("requests", labels={"provider": "anthropic"}) == 1.0


def test_gauge_operations():
    from ai_generation.observability import ObservabilityManager
    obs = ObservabilityManager()
    obs.set_gauge("cpu_usage", 75.5)
    assert obs.get_gauge("cpu_usage") == 75.5
    obs.set_gauge("cpu_usage", 80.0)
    assert obs.get_gauge("cpu_usage") == 80.0


def test_histogram_operations():
    from ai_generation.observability import ObservabilityManager
    obs = ObservabilityManager()
    for v in [100, 200, 300, 400, 500]:
        obs.record_histogram("latency", v)
    stats = obs.get_histogram_stats("latency")
    assert stats["count"] == 5
    assert stats["min"] == 100
    assert stats["max"] == 500
    assert stats["avg"] == 300


def test_histogram_empty():
    from ai_generation.observability import ObservabilityManager
    obs = ObservabilityManager()
    stats = obs.get_histogram_stats("nonexistent")
    assert stats["count"] == 0


def test_trace_operations():
    from ai_generation.observability import ObservabilityManager, TraceStatus
    obs = ObservabilityManager()
    trace_id = obs.start_trace("test_generation", {"prompt": "hello"})
    assert trace_id != ""
    obs.end_trace(trace_id, TraceStatus.OK)
    traces = obs.get_trace(trace_id)
    assert len(traces) == 1
    assert traces[0]["status"] == "ok"


def test_span_operations():
    from ai_generation.observability import ObservabilityManager, TraceStatus
    obs = ObservabilityManager()
    trace_id = obs.start_trace("parent_trace")
    span_id = obs.start_span(trace_id, "child_span", {"step": "routing"})
    obs.end_span(span_id, TraceStatus.OK)
    traces = obs.get_trace(trace_id)
    assert len(traces) == 2


def test_log_operations():
    from ai_generation.observability import ObservabilityManager
    obs = ObservabilityManager()
    obs.log_info("Test message", source="test", attributes={"key": "value"})
    logs = obs.get_logs(level="info")
    assert len(logs) >= 1
    assert logs[-1]["message"] == "Test message"
    assert logs[-1]["source"] == "test"


def test_log_error():
    from ai_generation.observability import ObservabilityManager
    obs = ObservabilityManager()
    obs.log_error("Error occurred", source="test")
    logs = obs.get_logs(level="error")
    assert len(logs) >= 1


def test_generation_tracking():
    from ai_generation.observability import ObservabilityManager
    obs = ObservabilityManager()
    trace_id = obs.track_generation_start("req-1", "image_generation", "pollinations")
    assert trace_id != ""
    obs.track_generation_end(trace_id, success=True, latency_ms=5000, provider="pollinations")
    assert obs.get_counter("generation_requests_total", labels={"task_type": "image_generation"}) >= 1
    assert obs.get_counter("generation_success_total") >= 1


def test_generation_tracking_failure():
    from ai_generation.observability import ObservabilityManager
    obs = ObservabilityManager()
    trace_id = obs.track_generation_start("req-2", "image_generation")
    obs.track_generation_end(trace_id, success=False)
    assert obs.get_counter("generation_failure_total") >= 1


def test_provider_selection_tracking():
    from ai_generation.observability import ObservabilityManager
    obs = ObservabilityManager()
    obs.track_provider_selection("openai", "text_generation", confidence=0.9)
    assert obs.get_counter("negotiation_decisions_total") >= 1


def test_fallback_tracking():
    from ai_generation.observability import ObservabilityManager
    obs = ObservabilityManager()
    obs.track_fallback("openai", "anthropic", "rate_limited")
    assert obs.get_counter("fallback_activations_total", labels={"from": "openai", "to": "anthropic"}) >= 1


def test_recent_traces():
    from ai_generation.observability import ObservabilityManager
    obs = ObservabilityManager()
    for i in range(5):
        tid = obs.start_trace(f"trace_{i}")
        obs.end_trace(tid)
    traces = obs.get_recent_traces(3)
    assert len(traces) == 3


def test_export_metrics():
    from ai_generation.observability import ObservabilityManager
    obs = ObservabilityManager()
    obs.increment_counter("test_metric")
    metrics = obs.export_metrics()
    assert "test_metric" in metrics
    assert metrics["test_metric"]["value"] == 1.0


def test_export_all():
    from ai_generation.observability import ObservabilityManager
    obs = ObservabilityManager()
    data = obs.export_all()
    assert "metrics" in data
    assert "traces" in data
    assert "logs" in data
    assert "stats" in data


def test_observability_stats():
    from ai_generation.observability import ObservabilityManager
    obs = ObservabilityManager()
    stats = obs.get_stats()
    assert "service_name" in stats
    assert "total_metrics" in stats
    assert stats["total_metrics"] > 0


def test_histogram_latency_tracking():
    from ai_generation.observability import ObservabilityManager
    obs = ObservabilityManager()
    trace_id = obs.track_generation_start("req-latency", "image_generation", "pollinations")
    obs.track_generation_end(trace_id, success=True, latency_ms=3500, provider="pollinations")
    stats = obs.get_histogram_stats("generation_latency_ms", labels={"provider": "pollinations"})
    assert stats["count"] >= 1


# ── SDK Integration Tests ─────────────────────────────────────

def test_sdk_observability_import():
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    assert hasattr(ai, 'observability')
    assert hasattr(ai, 'observe_generation')
    assert hasattr(ai, 'observe_generation_end')
    assert hasattr(ai, 'get_observability_metrics')
    assert hasattr(ai, 'get_observability_traces')
    assert hasattr(ai, 'get_observability_logs')
    assert hasattr(ai, 'get_observability_stats')


def test_sdk_observability_metrics():
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    metrics = ai.get_observability_metrics()
    assert isinstance(metrics, dict)
    assert "generation_requests_total" in metrics


def test_sdk_observability_stats():
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    stats = ai.get_observability_stats()
    assert "service_name" in stats
    assert stats["service_name"] == "uncle-frappe-ai"


# ── MCP Tools Tests ──────────────────────────────────────────

def test_mcp_observability_tools_exist():
    from ai_generation.mcp_tools import MCP_GENERATION_TOOLS
    assert "get_observability_metrics" in MCP_GENERATION_TOOLS
    assert "get_observability_traces" in MCP_GENERATION_TOOLS
    assert "get_observability_logs" in MCP_GENERATION_TOOLS
    assert "get_observability_stats" in MCP_GENERATION_TOOLS


def test_mcp_observability_handler_import():
    from ai_generation.mcp_tools import MCPGenerationTools
    handler = MCPGenerationTools()
    assert hasattr(handler, '_handle_get_observability_metrics')
    assert hasattr(handler, '_handle_get_observability_traces')
    assert hasattr(handler, '_handle_get_observability_logs')
    assert hasattr(handler, '_handle_get_observability_stats')
