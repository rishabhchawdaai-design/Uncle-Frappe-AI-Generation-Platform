"""Tests for quality_dashboard.py — QualityDashboard, QualityReport."""

import pytest
from ai_generation.quality_dashboard import (
    HealthGrade, DimensionScore, QualityReport, QualityDashboard,
)


class TestDimensionScore:
    def test_create(self):
        d = DimensionScore(name="security", score=95, grade="A")
        assert d.name == "security"
        assert d.score == 95

    def test_to_dict(self):
        d = DimensionScore(name="quality", score=80, grade="B", findings_count=3)
        dd = d.to_dict()
        assert dd["name"] == "quality"
        assert dd["findings_count"] == 3


class TestQualityDashboard:
    def test_analyze_clean_code(self):
        dashboard = QualityDashboard()
        code = 'import logging\nlogger = logging.getLogger(__name__)\ndef main() -> None:\n    """Main entry point."""\n    pass'
        report = dashboard.analyze(code, "clean.py")
        assert report.overall_score >= 70
        assert report.overall_grade in ("A+", "A", "B+", "B")
        assert len(report.dimensions) == 6

    def test_analyze_insecure_code(self):
        dashboard = QualityDashboard()
        code = "API_KEY = 'sk-1234567890abcdefghijklmnopqrst'\nresult = eval(input())"
        report = dashboard.analyze(code, "bad.py")
        assert report.overall_score < 80  # security issues lower the score
        assert report.metrics["security_grade"] in ("D", "F", "C", "C+")

    def test_analyze_complex_code(self):
        dashboard = QualityDashboard()
        lines = ["def complex_func(x):"]
        for i in range(60):
            lines.append(f"    x_{i} = {i}")
        code = "\n".join(lines)
        report = dashboard.analyze(code, "complex.py")
        assert report.metrics["total_findings"] > 0

    def test_report_to_dict(self):
        dashboard = QualityDashboard()
        code = "x = 1"
        report = dashboard.analyze(code, "test.py")
        d = report.to_dict()
        assert "timestamp" in d
        assert "overall_score" in d
        assert "dimensions" in d
        assert "recommendations" in d

    def test_history(self):
        dashboard = QualityDashboard()
        dashboard.analyze("x = 1", "a.py")
        dashboard.analyze("y = 2", "b.py")
        assert len(dashboard.get_history()) == 2

    def test_stats(self):
        dashboard = QualityDashboard()
        dashboard.analyze("x = 1", "a.py")
        stats = dashboard.get_stats()
        assert stats["total_analyses"] == 1
        assert "avg_score" in stats

    def test_empty_stats(self):
        dashboard = QualityDashboard()
        stats = dashboard.get_stats()
        assert stats["total_analyses"] == 0

    def test_recommendations_generated(self):
        dashboard = QualityDashboard()
        code = "API_KEY = 'sk-1234567890abcdefghijklmnopqrst'\nresult = eval(input())"
        report = dashboard.analyze(code, "bad.py")
        assert len(report.recommendations) > 0

    def test_all_grades_possible(self):
        for grade in HealthGrade:
            assert grade.value in ("A+", "A", "B+", "B", "C+", "C", "D", "F")

    def test_documentation_analysis(self):
        dashboard = QualityDashboard()
        code = 'def documented():\n    """Has docstring."""\n    pass\ndef undocumented():\n    pass'
        report = dashboard.analyze(code, "test.py")
        doc_dim = next(d for d in report.dimensions if d["name"] == "documentation")
        assert doc_dim["findings_count"] == 1

    def test_syntax_error_handling(self):
        dashboard = QualityDashboard()
        report = dashboard.analyze("def func(:\n  pass", "bad.py")
        assert report.overall_score >= 0
        assert len(report.dimensions) == 6
