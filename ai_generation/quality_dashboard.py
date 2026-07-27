"""
Quality Dashboard — aggregates metrics from all quality engines into a unified report.

Provides: QualityDashboard with comprehensive code health metrics.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


class HealthGrade(str, Enum):
    A_PLUS = "A+"
    A = "A"
    B_PLUS = "B+"
    B = "B"
    C_PLUS = "C+"
    C = "C"
    D = "D"
    F = "F"


@dataclass
class DimensionScore:
    name: str
    score: float
    max_score: float = 100.0
    grade: str = ""
    findings_count: int = 0
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "score": self.score,
            "max_score": self.max_score,
            "grade": self.grade,
            "findings_count": self.findings_count,
            "details": self.details,
        }


@dataclass
class QualityReport:
    timestamp: str
    file_path: str
    overall_score: float
    overall_grade: str
    dimensions: List[Dict[str, Any]]
    summary: str
    recommendations: List[str]
    metrics: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "file_path": self.file_path,
            "overall_score": self.overall_score,
            "overall_grade": self.overall_grade,
            "dimensions": self.dimensions,
            "summary": self.summary,
            "recommendations": self.recommendations,
            "metrics": self.metrics,
        }


class QualityDashboard:
    """Unified quality dashboard aggregating all quality engines."""

    def __init__(self):
        self._history: List[QualityReport] = []

    def analyze(self, code: str, file_path: str = "<input>") -> QualityReport:
        """Run comprehensive quality analysis and produce a unified report."""
        dimensions: List[DimensionScore] = []

        security_score = self._analyze_security(code, file_path)
        dimensions.append(security_score)

        quality_score = self._analyze_code_quality(code, file_path)
        dimensions.append(quality_score)

        complexity_score = self._analyze_complexity(code, file_path)
        dimensions.append(complexity_score)

        documentation_score = self._analyze_documentation(code, file_path)
        dimensions.append(documentation_score)

        debt_score = self._analyze_debt(code, file_path)
        dimensions.append(debt_score)

        refactoring_score = self._analyze_refactoring(code, file_path)
        dimensions.append(refactoring_score)

        total_weight = sum(d.score for d in dimensions)
        max_weight = sum(d.max_score for d in dimensions)
        overall_score = (total_weight / max_weight * 100) if max_weight > 0 else 0
        overall_grade = self._score_to_grade(overall_score)

        recommendations = self._generate_recommendations(dimensions)
        summary = self._generate_summary(dimensions, overall_grade, overall_score)

        metrics = {
            "dimensions_analyzed": len(dimensions),
            "total_findings": sum(d.findings_count for d in dimensions),
            "security_grade": security_score.grade,
            "quality_grade": quality_score.grade,
            "complexity_grade": complexity_score.grade,
            "documentation_grade": documentation_score.grade,
            "debt_grade": debt_score.grade,
            "refactoring_grade": refactoring_score.grade,
        }

        report = QualityReport(
            timestamp=datetime.now(timezone.utc).isoformat(),
            file_path=file_path,
            overall_score=round(overall_score, 1),
            overall_grade=overall_grade,
            dimensions=[d.to_dict() for d in dimensions],
            summary=summary,
            recommendations=recommendations,
            metrics=metrics,
        )

        self._history.append(report)
        return report

    def _analyze_security(self, code: str, file_path: str) -> DimensionScore:
        from .code_analysis import SecretScanner, StaticAnalyzer
        scanner = SecretScanner()
        analyzer = StaticAnalyzer()
        secrets = scanner.scan_text(code, file_path)
        issues = analyzer.analyze_code(code, file_path)
        security_issues = [i for i in issues if i.category == "security"]
        total = len(secrets) + len(security_issues)
        score = max(0, 100 - total * 20)
        return DimensionScore(
            name="security",
            score=score,
            grade=self._score_to_grade(score),
            findings_count=total,
            details={"secrets": len(secrets), "vulnerabilities": len(security_issues)},
        )

    def _analyze_code_quality(self, code: str, file_path: str) -> DimensionScore:
        from .code_analysis import StaticAnalyzer
        analyzer = StaticAnalyzer()
        issues = analyzer.analyze_code(code, file_path)
        quality_issues = [i for i in issues if i.category == "quality"]
        total = len(quality_issues)
        score = max(0, 100 - total * 5)
        return DimensionScore(
            name="code_quality",
            score=score,
            grade=self._score_to_grade(score),
            findings_count=total,
            details={"quality_issues": total},
        )

    def _analyze_complexity(self, code: str, file_path: str) -> DimensionScore:
        from .code_analysis import StructuralAnalyzer
        analyzer = StructuralAnalyzer()
        findings = analyzer.analyze({file_path: code})
        complexity_issues = [f for f in findings if f.category in ("complexity", "long_function")]
        total = len(complexity_issues)
        score = max(0, 100 - total * 15)
        return DimensionScore(
            name="complexity",
            score=score,
            grade=self._score_to_grade(score),
            findings_count=total,
            details={"complexity_issues": total},
        )

    def _analyze_documentation(self, code: str, file_path: str) -> DimensionScore:
        from .code_analysis import StaticAnalyzer
        import ast
        analyzer = StaticAnalyzer()
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return DimensionScore(name="documentation", score=50, grade="C", findings_count=0)

        total_funcs = 0
        documented = 0
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                total_funcs += 1
                if ast.get_docstring(node):
                    documented += 1
        ratio = documented / max(1, total_funcs)
        score = ratio * 100
        return DimensionScore(
            name="documentation",
            score=score,
            grade=self._score_to_grade(score),
            findings_count=total_funcs - documented,
            details={"total_functions": total_funcs, "documented": documented, "ratio": round(ratio, 2)},
        )

    def _analyze_debt(self, code: str, file_path: str) -> DimensionScore:
        from .code_analysis import TechnicalDebtTracker
        tracker = TechnicalDebtTracker()
        items = tracker.scan_codebase({file_path: code})
        total = len(items)
        high_priority = sum(1 for i in items if i.priority in ("high", "critical"))
        score = max(0, 100 - high_priority * 15 - (total - high_priority) * 3)
        return DimensionScore(
            name="technical_debt",
            score=score,
            grade=self._score_to_grade(score),
            findings_count=total,
            details={"total_items": total, "high_priority": high_priority},
        )

    def _analyze_refactoring(self, code: str, file_path: str) -> DimensionScore:
        from .refactoring_engine import RefactoringEngine
        engine = RefactoringEngine()
        suggestions = engine.analyze(code, file_path)
        total = len(suggestions)
        high_effort = sum(1 for s in suggestions if s.effort == "high")
        score = max(0, 100 - high_effort * 20 - (total - high_effort) * 5)
        return DimensionScore(
            name="refactoring",
            score=score,
            grade=self._score_to_grade(score),
            findings_count=total,
            details={"total_suggestions": total, "high_effort": high_effort},
        )

    def _score_to_grade(self, score: float) -> str:
        if score >= 97: return HealthGrade.A_PLUS.value
        if score >= 93: return HealthGrade.A.value
        if score >= 90: return HealthGrade.B_PLUS.value
        if score >= 80: return HealthGrade.B.value
        if score >= 70: return HealthGrade.C_PLUS.value
        if score >= 60: return HealthGrade.C.value
        if score >= 50: return HealthGrade.D.value
        return HealthGrade.F.value

    def _generate_recommendations(self, dimensions: List[DimensionScore]) -> List[str]:
        recs = []
        for d in dimensions:
            if d.score < 80:
                if d.name == "security":
                    recs.append("Fix security vulnerabilities and remove hardcoded secrets")
                elif d.name == "code_quality":
                    recs.append("Address code quality issues (bare excepts, star imports, print statements)")
                elif d.name == "complexity":
                    recs.append("Reduce cyclomatic complexity and break down large functions")
                elif d.name == "documentation":
                    recs.append("Add docstrings to undocumented functions")
                elif d.name == "technical_debt":
                    recs.append("Address high-priority technical debt items (FIXMEs, HACKs)")
                elif d.name == "refactoring":
                    recs.append("Apply suggested refactorings to improve code structure")
        return recs

    def _generate_summary(self, dimensions: List[DimensionScore], grade: str, score: float) -> str:
        total_findings = sum(d.findings_count for d in dimensions)
        if grade in ("A+", "A"):
            return f"Excellent code health ({score:.0f}/100). {total_findings} minor findings."
        elif grade in ("B+", "B"):
            return f"Good code health ({score:.0f}/100). {total_findings} findings to address."
        elif grade in ("C+", "C"):
            return f"Fair code health ({score:.0f}/100). {total_findings} findings need attention."
        else:
            return f"Poor code health ({score:.0f}/100). {total_findings} findings require immediate action."

    def get_history(self) -> List[Dict[str, Any]]:
        return [r.to_dict() for r in self._history]

    def get_stats(self) -> Dict[str, Any]:
        if not self._history:
            return {"total_analyses": 0, "avg_score": 0, "avg_grade": "N/A"}
        scores = [r.overall_score for r in self._history]
        grades = [r.overall_grade for r in self._history]
        grade_counts = {}
        for g in grades:
            grade_counts[g] = grade_counts.get(g, 0) + 1
        return {
            "total_analyses": len(self._history),
            "avg_score": round(sum(scores) / len(scores), 1),
            "avg_grade": max(set(grades), key=grades.count),
            "grade_distribution": grade_counts,
        }
