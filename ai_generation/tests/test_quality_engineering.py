"""Tests for Quality Engineering Layer — gates, review, scoring, generation, analysis."""
import pytest


# ── Quality Gate Tests ──

def test_gate_severity_enum():
    from ai_generation.quality_engineering import GateSeverity
    assert GateSeverity.INFO.value == "info"
    assert GateSeverity.CRITICAL.value == "critical"


def test_gate_result_enum():
    from ai_generation.quality_engineering import GateResult
    assert GateResult.PASSED.value == "passed"
    assert GateResult.FAILED.value == "failed"


def test_quality_gate_engine_import():
    from ai_generation.quality_engineering import QualityGateEngine
    e = QualityGateEngine()
    assert e is not None


def test_quality_gate_engine_default_gates():
    from ai_generation.quality_engineering import QualityGateEngine
    e = QualityGateEngine()
    gates = e.list_gates()
    assert len(gates) >= 7
    names = [g["name"] for g in gates]
    assert "secrets_scan" in names
    assert "test_pass" in names
    assert "security_patterns" in names


def test_quality_gate_engine_stats():
    from ai_generation.quality_engineering import QualityGateEngine
    e = QualityGateEngine()
    stats = e.get_stats()
    assert stats["registered_gates"] >= 7
    assert stats["total_checks"] == 0


@pytest.mark.asyncio
async def test_secrets_scan_clean():
    from ai_generation.quality_engineering import QualityGateEngine, GateResult
    e = QualityGateEngine()
    result = await e.run_gate("secrets_scan", code='x = "hello world"')
    assert result.result == GateResult.PASSED


@pytest.mark.asyncio
async def test_secrets_scan_api_key():
    from ai_generation.quality_engineering import QualityGateEngine, GateResult
    e = QualityGateEngine()
    result = await e.run_gate("secrets_scan", code='api_key = "AKIAIOSFODNN7EXAMPLE"')
    assert result.result == GateResult.FAILED


@pytest.mark.asyncio
async def test_no_debug_code_clean():
    from ai_generation.quality_engineering import QualityGateEngine, GateResult
    e = QualityGateEngine()
    result = await e.run_gate("no_debug_code", code='def hello():\n    return "world"')
    assert result.result == GateResult.PASSED


@pytest.mark.asyncio
async def test_no_debug_code_print():
    from ai_generation.quality_engineering import QualityGateEngine, GateResult
    e = QualityGateEngine()
    result = await e.run_gate("no_debug_code", code='print("hello")')
    assert result.result == GateResult.FAILED


@pytest.mark.asyncio
async def test_security_patterns_clean():
    from ai_generation.quality_engineering import QualityGateEngine, GateResult
    e = QualityGateEngine()
    result = await e.run_gate("security_patterns", code='x = 42')
    assert result.result == GateResult.PASSED


@pytest.mark.asyncio
async def test_security_patterns_eval():
    from ai_generation.quality_engineering import QualityGateEngine, GateResult
    e = QualityGateEngine()
    result = await e.run_gate("security_patterns", code='eval(user_input)')
    assert result.result == GateResult.FAILED


@pytest.mark.asyncio
async def test_run_all_gates():
    from ai_generation.quality_engineering import QualityGateEngine
    e = QualityGateEngine()
    results = await e.run_all_gates(code='x = 42')
    assert len(results) >= 7
    assert all(hasattr(r, 'result') for r in results)


# ── Code Review Tests ──

def test_review_severity_enum():
    from ai_generation.quality_engineering import ReviewSeverity
    assert ReviewSeverity.ERROR.value == "error"
    assert ReviewSeverity.CRITICAL.value == "critical"


def test_review_category_enum():
    from ai_generation.quality_engineering import ReviewCategory
    assert ReviewCategory.CORRECTNESS.value == "correctness"
    assert ReviewCategory.SECURITY.value == "security"


def test_code_review_engine_import():
    from ai_generation.quality_engineering import CodeReviewEngine
    e = CodeReviewEngine()
    assert e is not None


def test_code_review_engine_rules():
    from ai_generation.quality_engineering import CodeReviewEngine
    e = CodeReviewEngine()
    assert len(e._rules) >= 6


@pytest.mark.asyncio
async def test_code_review_clean():
    from ai_generation.quality_engineering import CodeReviewEngine
    e = CodeReviewEngine()
    result = await e.review(code='def hello() -> str:\n    """Say hello."""\n    return "world"')
    assert result.score > 80


@pytest.mark.asyncio
async def test_code_review_bare_except():
    from ai_generation.quality_engineering import CodeReviewEngine
    e = CodeReviewEngine()
    result = await e.review(code='try:\n    x = 1\nexcept:\n    pass')
    assert result.score < 100
    assert any(f.rule_id == "no_bare_except" for f in result.findings)


@pytest.mark.asyncio
async def test_code_review_mutable_default():
    from ai_generation.quality_engineering import CodeReviewEngine
    e = CodeReviewEngine()
    result = await e.review(code='def append(item, lst=[]):\n    lst.append(item)\n    return lst')
    assert any(f.rule_id == "no_mutable_default" for f in result.findings)


@pytest.mark.asyncio
async def test_code_review_star_import():
    from ai_generation.quality_engineering import CodeReviewEngine
    e = CodeReviewEngine()
    result = await e.review(code='from os import *')
    assert any(f.rule_id == "no_star_imports" for f in result.findings)


def test_code_review_engine_stats():
    from ai_generation.quality_engineering import CodeReviewEngine
    e = CodeReviewEngine()
    stats = e.get_stats()
    assert stats["registered_rules"] >= 6
    assert stats["total_reviews"] == 0


# ── Quality Scoring Tests ──

def test_quality_dimension_enum():
    from ai_generation.quality_engineering import QualityDimension
    assert QualityDimension.CORRECTNESS.value == "correctness"
    assert QualityDimension.SECURITY.value == "security"
    assert QualityDimension.DOCUMENTATION.value == "documentation"


def test_quality_scoring_engine_import():
    from ai_generation.quality_engineering import QualityScoringEngine
    e = QualityScoringEngine()
    assert e is not None


@pytest.mark.asyncio
async def test_score_clean_code():
    from ai_generation.quality_engineering import QualityScoringEngine
    e = QualityScoringEngine()
    result = await e.score_file(code='def hello() -> str:\n    """Say hello."""\n    return "world"')
    assert result["overall_score"] > 70


@pytest.mark.asyncio
async def test_score_unsafe_code():
    from ai_generation.quality_engineering import QualityScoringEngine
    e = QualityScoringEngine()
    result = await e.score_file(code='eval(user_input)\nos.system("rm -rf /")')
    assert result["overall_score"] < 80


def test_quality_scoring_stats():
    from ai_generation.quality_engineering import QualityScoringEngine
    e = QualityScoringEngine()
    stats = e.get_stats()
    assert stats["total_scored"] == 0


# ── Test Generation Tests ──

def test_test_generation_engine_import():
    from ai_generation.quality_engineering import TestGenerationEngine
    e = TestGenerationEngine()
    assert e is not None


def test_test_generation_templates():
    from ai_generation.quality_engineering import TestGenerationEngine
    e = TestGenerationEngine()
    templates = e.get_templates()
    assert len(templates) >= 4
    names = [t["name"] for t in templates]
    assert "unit_test_pytest" in names


@pytest.mark.asyncio
async def test_generate_tests_for_functions():
    from ai_generation.quality_engineering import TestGenerationEngine
    e = TestGenerationEngine()
    result = await e.generate_tests(code='def add(a, b):\n    return a + b\ndef subtract(a, b):\n    return a - b')
    assert result["functions_found"] == 2
    assert len(result["test_cases"]) == 2


def test_test_generation_stats():
    from ai_generation.quality_engineering import TestGenerationEngine
    e = TestGenerationEngine()
    stats = e.get_stats()
    assert stats["total_generations"] == 0


# ── Coverage Gap Tests ──

def test_coverage_gap_engine_import():
    from ai_generation.quality_engineering import CoverageGapEngine
    e = CoverageGapEngine()
    assert e is not None


@pytest.mark.asyncio
async def test_analyze_coverage_gaps():
    from ai_generation.quality_engineering import CoverageGapEngine
    e = CoverageGapEngine()
    result = await e.analyze_gaps(
        code='def add(a, b): return a + b\ndef auth(user): return user.is_valid',
        test_code='def test_add(): assert add(1, 2) == 3',
    )
    assert result["total_functions"] == 2
    assert result["tested_functions"] == 1
    assert len(result["gaps"]) == 1
    assert result["gaps"][0]["function"] == "auth"


def test_coverage_gap_stats():
    from ai_generation.quality_engineering import CoverageGapEngine
    e = CoverageGapEngine()
    stats = e.get_stats()
    assert stats["total_analyses"] == 0


# ── Flaky Detection Tests ──

def test_flaky_detection_engine_import():
    from ai_generation.quality_engineering import FlakyDetectionEngine
    e = FlakyDetectionEngine()
    assert e is not None


def test_flaky_detection_record():
    from ai_generation.quality_engineering import FlakyDetectionEngine
    e = FlakyDetectionEngine()
    for _ in range(5):
        e.record_result("test_flaky", "passed")
    e.record_result("test_flaky", "failed")
    e.record_result("test_flaky", "failed")
    assert len(e._test_history["test_flaky"]) == 7


@pytest.mark.asyncio
async def test_detect_flaky_tests():
    from ai_generation.quality_engineering import FlakyDetectionEngine
    e = FlakyDetectionEngine()
    for _ in range(5):
        e.record_result("test_flaky", "passed")
    for _ in range(5):
        e.record_result("test_flaky", "failed")
    flaky = await e.detect_flaky(min_runs=3)
    assert len(flaky) == 1
    assert flaky[0]["test_name"] == "test_flaky"


def test_flaky_detection_stats():
    from ai_generation.quality_engineering import FlakyDetectionEngine
    e = FlakyDetectionEngine()
    stats = e.get_stats()
    assert stats["total_tests_tracked"] == 0


# ── Pattern Learning Tests ──

def test_pattern_learning_engine_import():
    from ai_generation.quality_engineering import PatternLearningEngine
    e = PatternLearningEngine()
    assert e is not None


def test_learn_pattern():
    from ai_generation.quality_engineering import PatternLearningEngine
    e = PatternLearningEngine()
    e.learn_pattern("lazy_property", "design_pattern", "Lazy-loaded property", "@property\ndef x(self): ...")
    pattern = e.get_pattern("lazy_property")
    assert pattern is not None
    assert pattern["type"] == "design_pattern"


def test_find_patterns():
    from ai_generation.quality_engineering import PatternLearningEngine
    e = PatternLearningEngine()
    e.learn_pattern("p1", "design_pattern", "Test pattern 1", "code1")
    e.learn_pattern("p2", "error_handling", "Test pattern 2", "code2")
    results = e.find_patterns(pattern_type="design_pattern")
    assert len(results) == 1


def test_pattern_learning_stats():
    from ai_generation.quality_engineering import PatternLearningEngine
    e = PatternLearningEngine()
    stats = e.get_stats()
    assert stats["total_patterns"] == 0


# ── SDK Integration ──

def test_sdk_quality_engineering_import():
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    assert ai.quality_gates is not None
    assert ai.code_review is not None
    assert ai.test_generation is not None
    assert ai.coverage_gap is not None
    assert ai.flaky_detection is not None
    assert ai.pattern_learning is not None
    assert ai.quality_scoring is not None


def test_sdk_quality_engineering_in_stats():
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    stats = ai.get_stats()
    assert "quality_gates" in stats
    assert "code_review" in stats
    assert "test_generation" in stats
    assert "quality_scoring" in stats


# ── MCP Tools ──

def test_mcp_qe_tools_exist():
    from ai_generation.mcp_tools import MCP_GENERATION_TOOLS
    assert "run_quality_gates" in MCP_GENERATION_TOOLS
    assert "run_single_gate" in MCP_GENERATION_TOOLS
    assert "list_quality_gates" in MCP_GENERATION_TOOLS
    assert "review_code" in MCP_GENERATION_TOOLS
    assert "score_quality" in MCP_GENERATION_TOOLS
    assert "generate_tests" in MCP_GENERATION_TOOLS
    assert "analyze_coverage_gaps" in MCP_GENERATION_TOOLS
    assert "detect_flaky_tests" in MCP_GENERATION_TOOLS
    assert "learn_pattern" in MCP_GENERATION_TOOLS
    assert "find_patterns" in MCP_GENERATION_TOOLS


@pytest.mark.asyncio
async def test_mcp_run_quality_gates():
    from ai_generation.mcp_tools import MCPGenerationTools
    mcp = MCPGenerationTools()
    result = await mcp.handle("run_quality_gates", {"code": "x = 42"})
    assert "results" in result
    assert len(result["results"]) >= 7


@pytest.mark.asyncio
async def test_mcp_review_code():
    from ai_generation.mcp_tools import MCPGenerationTools
    mcp = MCPGenerationTools()
    result = await mcp.handle("review_code", {"code": "def hello():\n    return 'world'"})
    assert "score" in result
    assert "findings" in result


@pytest.mark.asyncio
async def test_mcp_score_quality():
    from ai_generation.mcp_tools import MCPGenerationTools
    mcp = MCPGenerationTools()
    result = await mcp.handle("score_quality", {"code": "x = 42"})
    assert "overall_score" in result
    assert "dimensions" in result
