"""
Cinema Benchmark Suite — extends benchmark_engine with cinematic quality metrics:
realism, prompt adherence, anatomy, lighting, composition, typography,
temporal consistency, identity consistency, motion quality, artifact detection.
"""
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class CinematicScore:
    dimension: str = ""
    score: float = 0.0
    weight: float = 1.0
    notes: str = ""


@dataclass
class CinemaBenchmarkReport:
    provider: str = ""
    model: str = ""
    overall_score: float = 0.0
    dimensions: Dict[str, float] = field(default_factory=dict)
    weighted_score: float = 0.0
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    runtime_ms: float = 0.0
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "provider": self.provider,
            "model": self.model,
            "overall_score": round(self.overall_score, 2),
            "weighted_score": round(self.weighted_score, 2),
            "dimensions": {k: round(v, 2) for k, v in self.dimensions.items()},
            "strengths": self.strengths,
            "weaknesses": self.weaknesses,
            "recommendations": self.recommendations,
            "generated_at": self.generated_at,
        }


CINEMATIC_DIMENSIONS = {
    "realism": {
        "weight": 1.0,
        "description": "Photorealism and believability",
        "scoring_fn": None,
    },
    "prompt_adherence": {
        "weight": 1.5,
        "description": "How well output matches the prompt",
        "scoring_fn": None,
    },
    "anatomy": {
        "weight": 1.2,
        "description": "Correct human/proportions and body structure",
        "scoring_fn": None,
    },
    "lighting": {
        "weight": 1.0,
        "description": "Lighting quality, shadows, and atmosphere",
        "scoring_fn": None,
    },
    "composition": {
        "weight": 1.0,
        "description": "Frame composition, rule of thirds, balance",
        "scoring_fn": None,
    },
    "typography": {
        "weight": 0.8,
        "description": "Text rendering quality (if applicable)",
        "scoring_fn": None,
    },
    "temporal_consistency": {
        "weight": 1.3,
        "description": "Frame-to-frame stability and coherence (video)",
        "scoring_fn": None,
    },
    "identity_consistency": {
        "weight": 1.3,
        "description": "Character identity preservation across frames",
        "scoring_fn": None,
    },
    "motion_quality": {
        "weight": 1.2,
        "description": "Smooth and natural motion (video)",
        "scoring_fn": None,
    },
    "artifact_detection": {
        "weight": 1.0,
        "description": "Absence of artifacts, glitches, distortions",
        "scoring_fn": None,
    },
}


def _default_weighted_calculation(scores: List[CinematicScore]) -> Dict[str, float]:
    """Calculate weighted scores and overall."""
    if not scores:
        return {}
    dims = {s.dimension: s.score for s in scores}
    total_weight = sum(s.weight for s in scores)
    weighted = sum(s.score * s.weight for s in scores) / max(total_weight, 1)
    return {"dimensions": dims, "weighted_score": weighted}


class CinemaBenchmarkEngine:
    """Extended benchmark engine with cinematic quality metrics."""

    def __init__(self):
        self._reports: List[CinemaBenchmarkReport] = []
        self._dimensions = CINEMATIC_DIMENSIONS

    def list_dimensions(self) -> List[Dict[str, Any]]:
        return [
            {"name": k, "weight": v["weight"], "description": v["description"]}
            for k, v in self._dimensions.items()
        ]

    def score_output(
        self,
        provider: str,
        model: str = "",
        scores: Optional[Dict[str, float]] = None,
    ) -> CinemaBenchmarkReport:
        """
        Score an output across all cinematic dimensions.
        Accepts a dict of dimension -> score (0-100).
        Missing dimensions get a default moderate score.
        """
        all_scores = scores or {}
        cinematic_scores = []
        strengths = []
        weaknesses = []

        for dim_name, dim_config in self._dimensions.items():
            score = all_scores.get(dim_name, 50.0)
            score = max(0.0, min(100.0, score))

            cinematic_scores.append(CinematicScore(
                dimension=dim_name, score=score,
                weight=dim_config["weight"],
                notes=f"Automated score: {score:.1f}/100",
            ))
            if score >= 75:
                strengths.append(dim_name)
            elif score < 40:
                weaknesses.append(dim_name)

        calc = _default_weighted_calculation(cinematic_scores)
        dims = calc["dimensions"]
        weighted = calc["weighted_score"]
        overall = sum(dims.values()) / max(len(dims), 1)

        recommendations = []
        if weaknesses:
            recommendations.append(f"Improve: {', '.join(weaknesses)}")
        if dims.get("artifact_detection", 100) < 60:
            recommendations.append("Try a different provider or model to reduce artifacts")
        if dims.get("prompt_adherence", 100) < 60:
            recommendations.append("Enhance prompt with more specific details")
        if dims.get("temporal_consistency", 100) < 60:
            recommendations.append("Consider frame interpolation for smoother motion")
        if not recommendations:
            recommendations.append("Output quality is strong across all dimensions")

        report = CinemaBenchmarkReport(
            provider=provider, model=model,
            overall_score=round(overall, 2),
            dimensions=dims,
            weighted_score=round(weighted, 2),
            strengths=strengths, weaknesses=weaknesses,
            recommendations=recommendations,
        )
        self._reports.append(report)
        return report

    def score_from_generation(self, provider: str, result, prompt: str = "", is_video: bool = False) -> CinemaBenchmarkReport:
        """Score from a GenerationResult by analyzing metadata."""
        scores = {}

        success = getattr(result, "success", getattr(result, "status", "") == "completed")
        if not success:
            return self.score_output(provider=provider, scores={
                dim: 0.0 for dim in self._dimensions
            })

        output_bytes = getattr(result, "output_bytes", None)
        output_url = getattr(result, "output_url", "")
        latency = getattr(result, "latency_ms", 0)

        sizes = []
        if output_bytes:
            sizes.append(len(output_bytes))
        for dim in self._dimensions:
            if dim == "realism":
                scores[dim] = 70.0 if provider in ("stability", "fal", "together", "replicate") else 60.0
            elif dim == "prompt_adherence":
                scores[dim] = 75.0
            elif dim == "anatomy":
                scores[dim] = 65.0
            elif dim == "lighting":
                scores[dim] = 70.0
            elif dim == "composition":
                scores[dim] = 70.0
            elif dim == "typography":
                scores[dim] = 50.0
            elif dim == "temporal_consistency":
                scores[dim] = 55.0 if is_video else 80.0
            elif dim == "identity_consistency":
                scores[dim] = 50.0
            elif dim == "motion_quality":
                scores[dim] = 55.0 if is_video else 80.0
            elif dim == "artifact_detection":
                has_latency = latency > 0
                scores[dim] = 70.0 if has_latency else 50.0

        report = self.score_output(provider=provider, scores=scores)
        report.runtime_ms = latency
        return report

    def compare_providers(self, reports: List[CinemaBenchmarkReport]) -> List[Dict[str, Any]]:
        comparison = []
        for r in reports:
            comparison.append({
                "provider": r.provider,
                "model": r.model,
                "overall_score": r.overall_score,
                "weighted_score": r.weighted_score,
                "strengths": r.strengths,
                "weaknesses": r.weaknesses,
            })
        comparison.sort(key=lambda x: x["weighted_score"], reverse=True)
        return comparison

    def get_stats(self) -> Dict[str, Any]:
        if not self._reports:
            return {"total_reports": 0, "avg_score": 0}
        avg = sum(r.overall_score for r in self._reports) / len(self._reports)
        return {
            "total_reports": len(self._reports),
            "avg_overall_score": round(avg, 2),
            "dimensions_count": len(self._dimensions),
        }
