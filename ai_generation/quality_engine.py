"""
Quality Engine — evaluate generated content quality with
heuristic scoring, A/B comparison, and consistency checking.
"""
import hashlib
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class QualityReport:
    asset_id: str = ""
    overall_score: float = 0.0
    dimensions: Dict[str, float] = field(default_factory=dict)
    issues: List[Dict[str, str]] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    evaluated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self):
        return {
            "asset_id": self.asset_id,
            "overall_score": round(self.overall_score, 2),
            "dimensions": {k: round(v, 2) for k, v in self.dimensions.items()},
            "issues": self.issues,
            "suggestions": self.suggestions,
            "evaluated_at": self.evaluated_at,
        }


class QualityEngine:
    """Evaluate and score generated content quality."""

    def __init__(self):
        self._history: List[QualityReport] = []

    def evaluate_generation(self, result, prompt="", style="") -> QualityReport:
        report = QualityReport(asset_id=result.request_id if hasattr(result, 'request_id') else "")

        prompt_relevance = self._score_prompt_relevance(prompt, getattr(result, 'metadata', {}))
        technical_quality = self._score_technical(result)
        style_consistency = self._score_style_consistency(style, getattr(result, 'metadata', {}))
        output_completeness = self._score_completeness(result)

        report.dimensions = {
            "prompt_relevance": prompt_relevance,
            "technical_quality": technical_quality,
            "style_consistency": style_consistency,
            "output_completeness": output_completeness,
        }
        report.overall_score = sum(report.dimensions.values()) / max(len(report.dimensions), 1)

        if report.overall_score < 50:
            report.suggestions.append("Consider re-generating with a different provider")
        if technical_quality < 60:
            report.suggestions.append("Output may have quality issues")
        if prompt_relevance < 50:
            report.suggestions.append("Prompt may need more specificity")

        self._history.append(report)
        return report

    def evaluate_prompt(self, prompt, enhanced="", negative="") -> QualityReport:
        report = QualityReport(asset_id="prompt-" + hashlib.sha256(prompt.encode()).hexdigest()[:8])

        word_count = len(prompt.split())
        has_quality = any(w in prompt.lower() for w in ["masterpiece", "detailed", "sharp", "high quality", "8k"])
        has_subject = len(prompt) > 20
        has_style = any(s in prompt.lower() for s in ["photo", "art", "painting", "render", "digital"])

        dims = {
            "specificity": min(word_count / 15.0, 1.0) * 100,
            "quality_hints": 100.0 if has_quality else 30.0,
            "subject_clarity": 100.0 if has_subject else 40.0,
            "style_defined": 100.0 if has_style else 50.0,
        }
        if enhanced:
            dims["enhancement_quality"] = min(len(enhanced) / max(len(prompt), 1), 2.0) * 50
        if negative:
            dims["negative_coverage"] = min(len(negative.split(",")) / 5.0, 1.0) * 100

        report.dimensions = dims
        report.overall_score = sum(dims.values()) / max(len(dims), 1)

        if word_count < 5:
            report.issues.append({"severity": "medium", "message": "Prompt is too short"})
        if not has_quality:
            report.suggestions.append("Add quality modifiers for better results")
        if not has_style:
            report.suggestions.append("Consider adding style direction")

        self._history.append(report)
        return report

    def compare_results(self, results) -> List[Dict[str, Any]]:
        scored = []
        for r in results:
            report = self.evaluate_generation(r)
            scored.append({
                "provider": getattr(r, 'provider', 'unknown'),
                "score": report.overall_score,
                "dimensions": report.dimensions,
                "status": getattr(r, 'status', 'unknown'),
                "latency_ms": getattr(r, 'latency_ms', 0),
            })
        scored.sort(key=lambda x: x['score'], reverse=True)
        return scored

    def _score_prompt_relevance(self, prompt, metadata):
        if not prompt:
            return 50.0
        score = 50.0
        if len(prompt.split()) > 5:
            score += 20
        if any(w in prompt.lower() for w in ["photo", "art", "scene", "portrait"]):
            score += 15
        if metadata.get("model"):
            score += 10
        return min(score, 100.0)

    def _score_technical(self, result):
        score = 50.0
        if hasattr(result, 'output_bytes') and result.output_bytes:
            size = len(result.output_bytes)
            if size > 50000:
                score += 25
            elif size > 10000:
                score += 15
        if hasattr(result, 'width') and result.width >= 1024:
            score += 15
        if hasattr(result, 'latency_ms') and result.latency_ms < 30000:
            score += 10
        return min(score, 100.0)

    def _score_style_consistency(self, style, metadata):
        if not style:
            return 70.0
        return 80.0

    def _score_completeness(self, result):
        score = 30.0
        if hasattr(result, 'output_bytes') and result.output_bytes:
            score += 30
        if hasattr(result, 'output_url') and result.output_url:
            score += 30
        if hasattr(result, 'status') and result.status == 'success':
            score += 10
        return min(score, 100.0)

    def get_stats(self):
        return {
            "total_evaluations": len(self._history),
            "avg_score": round(
                sum(r.overall_score for r in self._history) / max(len(self._history), 1), 2
            ),
        }
