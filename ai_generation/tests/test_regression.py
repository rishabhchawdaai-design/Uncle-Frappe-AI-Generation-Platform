"""
Phase 25 Tests — Benchmark Regression Detection

Tests latency, quality, and stability regression detection, and SDK/MCP exposure.
"""
import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))


def test_regression_type_enum():
    from ai_generation.regression_detector import RegressionType
    assert RegressionType.LATENCY.value == "latency"
    assert RegressionType.QUALITY.value == "quality"
    assert RegressionType.STABILITY.value == "stability"


def test_regression_severity_enum():
    from ai_generation.regression_detector import RegressionSeverity
    assert RegressionSeverity.INFO.value == "info"
    assert RegressionSeverity.WARNING.value == "warning"
    assert RegressionSeverity.CRITICAL.value == "critical"


def test_detector_import():
    from ai_generation.regression_detector import RegressionDetector
    d = RegressionDetector()
    assert d is not None


def test_set_baseline():
    from ai_generation.regression_detector import RegressionDetector
    d = RegressionDetector()
    d.set_baseline("openai", {"latency_p50": 1000, "quality_score": 0.9})
    assert d.get_baseline("openai") == {"latency_p50": 1000, "quality_score": 0.9}


def test_no_latency_regression():
    from ai_generation.regression_detector import RegressionDetector
    d = RegressionDetector()
    d.set_baseline("test", {"latency_p50": 1000})
    alerts = d.detect_latency_regression("test", current_p50=1050)
    assert len(alerts) == 0  # 5% < 20% warning threshold


def test_latency_warning():
    from ai_generation.regression_detector import RegressionDetector
    d = RegressionDetector()
    d.set_baseline("test", {"latency_p50": 1000})
    alerts = d.detect_latency_regression("test", current_p50=1250)
    assert len(alerts) == 1
    assert alerts[0].severity.value == "warning"
    assert alerts[0].deviation_pct == 25.0


def test_latency_critical():
    from ai_generation.regression_detector import RegressionDetector
    d = RegressionDetector()
    d.set_baseline("test", {"latency_p50": 1000})
    alerts = d.detect_latency_regression("test", current_p50=1600)
    assert len(alerts) == 1
    assert alerts[0].severity.value == "critical"
    assert alerts[0].deviation_pct == 60.0


def test_quality_no_regression():
    from ai_generation.regression_detector import RegressionDetector
    d = RegressionDetector()
    d.set_baseline("test", {"quality_score": 0.9})
    alerts = d.detect_quality_regression("test", current_score=0.85)
    assert len(alerts) == 0  # 5.6% < 10% warning


def test_quality_warning():
    from ai_generation.regression_detector import RegressionDetector
    d = RegressionDetector()
    d.set_baseline("test", {"quality_score": 0.9})
    alerts = d.detect_quality_regression("test", current_score=0.78)
    assert len(alerts) == 1
    assert alerts[0].severity.value == "warning"


def test_quality_critical():
    from ai_generation.regression_detector import RegressionDetector
    d = RegressionDetector()
    d.set_baseline("test", {"quality_score": 0.9})
    alerts = d.detect_quality_regression("test", current_score=0.65)
    assert len(alerts) == 1
    assert alerts[0].severity.value == "critical"


def test_stability_error_rate_warning():
    from ai_generation.regression_detector import RegressionDetector
    d = RegressionDetector()
    alerts = d.detect_stability_regression("test", current_error_rate=0.08)
    assert len(alerts) == 1
    assert alerts[0].severity.value == "warning"


def test_stability_error_rate_critical():
    from ai_generation.regression_detector import RegressionDetector
    d = RegressionDetector()
    alerts = d.detect_stability_regression("test", current_error_rate=0.20)
    assert len(alerts) == 1
    assert alerts[0].severity.value == "critical"


def test_auto_detect():
    from ai_generation.regression_detector import RegressionDetector
    d = RegressionDetector()
    d.set_baseline("test", {"latency_p50": 1000, "quality_score": 0.9})
    alerts = d.auto_detect("test", {"latency_p50": 1300, "quality_score": 0.75, "error_rate": 0.10})
    assert len(alerts) >= 2  # latency warning + quality warning


def test_alert_serialization():
    from ai_generation.regression_detector import RegressionDetector
    d = RegressionDetector()
    d.set_baseline("test", {"latency_p50": 1000})
    alerts = d.detect_latency_regression("test", current_p50=1300)
    assert len(alerts) == 1
    d2 = alerts[0].to_dict()
    assert "regression_type" in d2
    assert "severity" in d2
    assert "deviation_pct" in d2


def test_record_measurement():
    from ai_generation.regression_detector import RegressionDetector
    d = RegressionDetector()
    d.record_measurement("test", {"latency_p50": 1000, "quality_score": 0.9})
    history = d.get_provider_history("test")
    assert len(history) == 1


def test_get_all_alerts():
    from ai_generation.regression_detector import RegressionDetector
    d = RegressionDetector()
    d.set_baseline("test", {"latency_p50": 1000})
    d.detect_latency_regression("test", current_p50=1300)
    d.detect_latency_regression("test", current_p50=1600)
    alerts = d.get_all_alerts()
    assert len(alerts) == 2
    critical = d.get_all_alerts(severity="critical")
    assert len(critical) == 1


def test_detector_stats():
    from ai_generation.regression_detector import RegressionDetector
    d = RegressionDetector()
    d.set_baseline("test", {"latency_p50": 1000})
    d.detect_latency_regression("test", current_p50=1300)
    stats = d.get_stats()
    assert stats["baseline_count"] == 1
    assert stats["total_alerts"] == 1
    assert stats["by_type"]["latency"] == 1


def test_custom_config():
    from ai_generation.regression_detector import RegressionDetector
    d = RegressionDetector({"latency_warning_pct": 5.0})
    d.set_baseline("test", {"latency_p50": 1000})
    alerts = d.detect_latency_regression("test", current_p50=1060)
    assert len(alerts) == 1  # 6% > 5% custom threshold


# ── SDK Integration Tests ─────────────────────────────────────

def test_sdk_regression_import():
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    assert hasattr(ai, 'regression_detector')
    assert hasattr(ai, 'set_benchmark_baseline')
    assert hasattr(ai, 'detect_regression')
    assert hasattr(ai, 'get_regression_alerts')
    assert hasattr(ai, 'get_regression_stats')


def test_sdk_detect_regression():
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    ai.set_benchmark_baseline("test", {"latency_p50": 1000, "quality_score": 0.9})
    alerts = ai.detect_regression("test", {"latency_p50": 1300, "quality_score": 0.75})
    assert len(alerts) >= 2


def test_sdk_regression_stats():
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    stats = ai.get_regression_stats()
    assert "total_alerts" in stats


# ── MCP Tools Tests ──────────────────────────────────────────

def test_mcp_regression_tools_exist():
    from ai_generation.mcp_tools import MCP_GENERATION_TOOLS
    assert "detect_regression" in MCP_GENERATION_TOOLS
    assert "get_regression_alerts" in MCP_GENERATION_TOOLS
    assert "get_regression_stats" in MCP_GENERATION_TOOLS


def test_mcp_regression_handler_import():
    from ai_generation.mcp_tools import MCPGenerationTools
    handler = MCPGenerationTools()
    assert hasattr(handler, '_handle_detect_regression')
    assert hasattr(handler, '_handle_get_regression_alerts')
    assert hasattr(handler, '_handle_get_regression_stats')
