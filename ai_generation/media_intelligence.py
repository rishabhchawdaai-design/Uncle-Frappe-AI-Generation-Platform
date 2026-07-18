"""
Media Intelligence Engine — understands media requests, classifies them,
determines generation strategy, selects workflows, estimates cost/latency,
and recommends providers/models while preserving project context.
"""
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class MediaType(str, Enum):
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    MIXED = "mixed"


class RequestType(str, Enum):
    TEXT_TO_IMAGE = "text_to_image"
    TEXT_TO_VIDEO = "text_to_video"
    IMAGE_TO_IMAGE = "image_to_image"
    IMAGE_TO_VIDEO = "image_to_video"
    VIDEO_TO_VIDEO = "video_to_video"
    INPAINTING = "inpainting"
    OUTPAINTING = "outpainting"
    UPSCALE = "upscale"
    STYLE_TRANSFER = "style_transfer"
    BACKGROUND_REMOVAL = "background_removal"
    BACKGROUND_REPLACEMENT = "background_replacement"
    OBJECT_REMOVAL = "object_removal"
    OBJECT_INSERTION = "object_insertion"
    RELIGHTING = "relighting"
    STORYBOARD = "storyboard"
    CINEMATIC_PRODUCTION = "cinematic_production"
    BATCH_GENERATION = "batch_generation"


class ComplexityLevel(str, Enum):
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    PRODUCTION = "production"


class BudgetTier(str, Enum):
    FREE = "free"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    UNLIMITED = "unlimited"


BUDGET_RANGES = {
    BudgetTier.FREE: (0.0, 0.0),
    BudgetTier.LOW: (0.0, 1.0),
    BudgetTier.MEDIUM: (1.0, 10.0),
    BudgetTier.HIGH: (10.0, 100.0),
    BudgetTier.UNLIMITED: (100.0, float("inf")),
}

ESTIMATED_COST_PER_GENERATION = {
    "pollinations": 0.0,
    "craiyon": 0.0,
    "siliconflow": 0.0,
    "together": 0.0,
    "huggingface": 0.0,
    "replicate": 0.003,
    "replicate_video": 0.05,
    "stability": 0.01,
    "fal": 0.005,
}

ESTIMATED_LATENCY_MS = {
    "pollinations": 8000,
    "craiyon": 15000,
    "siliconflow": 4000,
    "together": 4000,
    "huggingface": 6000,
    "replicate": 10000,
    "replicate_video": 60000,
    "stability": 5000,
    "fal": 3000,
}


class PromptAnalyzer:
    """Analyze a prompt to determine media type and strategy."""

    VIDEO_KEYWORDS = [
        "video", "animation", "timelapse", "timelapse", "motion",
        "cinematic clip", "footage", "scene moving", "walking",
        "running", "flying", "waves crashing", "flowing",
    ]
    IMAGE_KEYWORDS = [
        "photo", "portrait", "landscape", "illustration", "painting",
        "logo", "icon", "poster", "banner", "design", "render",
        "concept art", "digital art", "sketch", "drawing",
    ]
    EDIT_KEYWORDS = [
        "edit", "remove", "replace", "change", "transform",
        "upscale", "enhance", "restore", "inpaint", "outpaint",
        "relight", "transfer style",
    ]

    def analyze(self, prompt: str) -> Dict[str, Any]:
        prompt_lower = prompt.lower()
        video_score = sum(1 for kw in self.VIDEO_KEYWORDS if kw in prompt_lower)
        image_score = sum(1 for kw in self.IMAGE_KEYWORDS if kw in prompt_lower)
        edit_score = sum(1 for kw in self.EDIT_KEYWORDS if kw in prompt_lower)

        if edit_score > 0 and (image_score > 0 or video_score > 0):
            request_type = RequestType.IMAGE_TO_IMAGE if image_score > video_score else RequestType.VIDEO_TO_VIDEO
        elif video_score > image_score:
            request_type = RequestType.TEXT_TO_VIDEO
        else:
            request_type = RequestType.TEXT_TO_IMAGE

        has_style = any(s in prompt_lower for s in [
            "photorealistic", "cinematic", "anime", "oil painting",
            "watercolor", "3d render", "digital art",
        ])
        has_quality = any(q in prompt_lower for q in [
            "masterpiece", "high quality", "detailed", "8k", "4k",
        ])
        word_count = len(prompt.split())

        if word_count > 30 or (has_style and has_quality):
            complexity = ComplexityLevel.COMPLEX
        elif word_count > 15 or has_style or has_quality:
            complexity = ComplexityLevel.MODERATE
        else:
            complexity = ComplexityLevel.SIMPLE

        return {
            "request_type": request_type,
            "media_type": MediaType.VIDEO if video_score > image_score else MediaType.IMAGE,
            "complexity": complexity,
            "has_style": has_style,
            "has_quality_hints": has_quality,
            "word_count": word_count,
            "video_score": video_score,
            "image_score": image_score,
            "edit_score": edit_score,
        }


class CostEstimator:
    """Estimate cost and latency for a generation request."""

    def estimate(
        self,
        provider: str,
        request_type: RequestType,
        width: int = 1024,
        height: int = 1024,
        duration_secs: float = 4.0,
        batch_size: int = 1,
    ) -> Dict[str, Any]:
        base_cost = ESTIMATED_COST_PER_GENERATION.get(provider, 0.01)
        base_latency = ESTIMATED_LATENCY_MS.get(provider, 8000)

        pixel_factor = (width * height) / (1024 * 1024)
        if request_type in (RequestType.TEXT_TO_VIDEO, RequestType.IMAGE_TO_VIDEO, RequestType.VIDEO_TO_VIDEO):
            pixel_factor *= duration_secs / 4.0
            base_cost *= duration_secs
            base_latency *= duration_secs / 4.0

        cost = round(base_cost * pixel_factor * batch_size, 6)
        latency = round(base_latency * pixel_factor, 0)

        return {
            "provider": provider,
            "estimated_cost_usd": cost,
            "estimated_latency_ms": latency,
            "pixel_factor": round(pixel_factor, 3),
            "batch_size": batch_size,
        }


class ProviderRecommender:
    """Recommend providers based on request characteristics."""

    PROVIDER_STRENGTHS = {
        "pollinations": {"free": True, "image_quality": 8, "speed": 6, "video": False},
        "craiyon": {"free": True, "image_quality": 5, "speed": 4, "video": False},
        "siliconflow": {"free": True, "image_quality": 8, "speed": 8, "video": False},
        "together": {"free": True, "image_quality": 8, "speed": 8, "video": False},
        "huggingface": {"free": True, "image_quality": 7, "speed": 6, "video": False},
        "replicate": {"free": False, "image_quality": 9, "speed": 7, "video": True},
        "replicate_video": {"free": False, "image_quality": 0, "speed": 3, "video": True},
        "stability": {"free": False, "image_quality": 9, "speed": 7, "video": False},
        "fal": {"free": False, "image_quality": 9, "speed": 9, "video": False},
    }

    def recommend(
        self,
        request_type: RequestType,
        budget: BudgetTier = BudgetTier.FREE,
        prioritize_speed: bool = False,
        require_video: bool = False,
        top_n: int = 3,
    ) -> List[Dict[str, Any]]:
        candidates = []
        for name, strengths in self.PROVIDER_STRENGTHS.items():
            if require_video and not strengths["video"]:
                continue
            if request_type in (RequestType.TEXT_TO_IMAGE, RequestType.IMAGE_TO_IMAGE,
                                RequestType.INPAINTING, RequestType.OUTPAINTING,
                                RequestType.UPSCALE, RequestType.STYLE_TRANSFER):
                if not strengths.get("image_quality", 0):
                    continue
            if budget == BudgetTier.FREE and not strengths.get("free", False):
                continue

            score = strengths["image_quality"] * 0.5 + strengths["speed"] * 0.3
            if prioritize_speed:
                score = strengths["speed"] * 0.6 + strengths["image_quality"] * 0.2
            if strengths.get("free"):
                score += 5

            candidates.append({
                "provider": name,
                "score": round(score, 2),
                "image_quality": strengths["image_quality"],
                "speed": strengths["speed"],
                "free": strengths["free"],
                "video_support": strengths["video"],
            })

        candidates.sort(key=lambda x: x["score"], reverse=True)
        return candidates[:top_n]


@dataclass
class MediaAnalysis:
    """Complete analysis of a media generation request."""
    original_prompt: str = ""
    request_type: RequestType = RequestType.TEXT_TO_IMAGE
    media_type: MediaType = MediaType.IMAGE
    complexity: ComplexityLevel = ComplexityLevel.SIMPLE
    recommended_providers: List[Dict[str, Any]] = field(default_factory=list)
    cost_estimates: List[Dict[str, Any]] = field(default_factory=list)
    estimated_total_cost: float = 0.0
    estimated_total_latency_ms: float = 0.0
    suggested_workflow: str = ""
    project_context: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    analyzed_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "original_prompt": self.original_prompt[:200],
            "request_type": self.request_type.value,
            "media_type": self.media_type.value,
            "complexity": self.complexity.value,
            "recommended_providers": self.recommended_providers,
            "cost_estimates": self.cost_estimates[:3],
            "estimated_total_cost": self.estimated_total_cost,
            "estimated_total_latency_ms": self.estimated_total_latency_ms,
            "suggested_workflow": self.suggested_workflow,
            "analyzed_at": self.analyzed_at,
        }


class MediaIntelligenceEngine:
    """
    Understands media requests, classifies them, determines generation strategy,
    selects workflows, estimates cost/latency, and recommends providers.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._analyzer = PromptAnalyzer()
        self._cost_estimator = CostEstimator()
        self._recommender = ProviderRecommender()
        self._history: List[MediaAnalysis] = []

    def analyze_request(
        self,
        prompt: str,
        budget: BudgetTier = BudgetTier.FREE,
        prioritize_speed: bool = False,
        width: int = 1024,
        height: int = 1024,
        duration_secs: float = 4.0,
        project_context: Optional[str] = None,
    ) -> MediaAnalysis:
        """Full analysis of a media generation request."""
        analysis_data = self._analyzer.analyze(prompt)

        require_video = analysis_data["request_type"] in (
            RequestType.TEXT_TO_VIDEO, RequestType.IMAGE_TO_VIDEO, RequestType.VIDEO_TO_VIDEO,
        )

        recommended = self._recommender.recommend(
            request_type=analysis_data["request_type"],
            budget=budget,
            prioritize_speed=prioritize_speed,
            require_video=require_video,
        )

        cost_estimates = []
        for rec in recommended:
            est = self._cost_estimator.estimate(
                provider=rec["provider"],
                request_type=analysis_data["request_type"],
                width=width,
                height=height,
                duration_secs=duration_secs,
            )
            cost_estimates.append(est)

        total_cost = sum(e["estimated_cost_usd"] for e in cost_estimates[:1])
        total_latency = max((e["estimated_latency_ms"] for e in cost_estimates[:1]), default=0)

        workflow = self._suggest_workflow(analysis_data["complexity"], analysis_data["request_type"])

        analysis = MediaAnalysis(
            original_prompt=prompt,
            request_type=analysis_data["request_type"],
            media_type=analysis_data["media_type"],
            complexity=analysis_data["complexity"],
            recommended_providers=recommended,
            cost_estimates=cost_estimates,
            estimated_total_cost=total_cost,
            estimated_total_latency_ms=total_latency,
            suggested_workflow=workflow,
            project_context=project_context,
            metadata=analysis_data,
        )
        self._history.append(analysis)
        return analysis

    def _suggest_workflow(self, complexity: ComplexityLevel, request_type: RequestType) -> str:
        if request_type == RequestType.CINEMATIC_PRODUCTION:
            return "cinematic_full_pipeline"
        if request_type in (RequestType.TEXT_TO_VIDEO, RequestType.IMAGE_TO_VIDEO):
            return "video_generation_pipeline"
        if request_type in (RequestType.INPAINTING, RequestType.OUTPAINTING, RequestType.OBJECT_REMOVAL):
            return "image_editing_pipeline"
        if complexity == ComplexityLevel.PRODUCTION:
            return "production_image_pipeline"
        if complexity == ComplexityLevel.COMPLEX:
            return "enhanced_generation_pipeline"
        return "simple_generation_pipeline"

    def get_stats(self) -> Dict[str, Any]:
        types = {}
        for a in self._history:
            t = a.request_type.value
            types[t] = types.get(t, 0) + 1
        return {
            "total_analyses": len(self._history),
            "by_request_type": types,
            "avg_cost": round(
                sum(a.estimated_total_cost for a in self._history) / max(len(self._history), 1), 6
            ),
        }
