"""
Auto Router — classifies tasks, discovers compatible providers, verifies availability,
ranks providers, executes remotely, retries if needed, falls back automatically.
"""
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


TASK_KEYWORDS = {
    "background_removal": {"keywords": ["remove background", "remove the background", "remove bg", "transparent background", "cutout", "strip background", "no background"], "weight": 5},
    "background_replacement": {"keywords": ["replace background", "new background", "change background"], "weight": 5},
    "inpainting": {"keywords": ["inpaint", "fill in", "complete the", "restore missing"], "weight": 5},
    "outpainting": {"keywords": ["outpaint", "extend the image", "expand the", "wider view"], "weight": 5},
    "upscale": {"keywords": ["upscale", "higher resolution", "4k", "8k", "enlarge", "sharpen"], "weight": 5},
    "style_transfer": {"keywords": ["in the style of", "make it look like", "style transfer"], "weight": 4},
    "object_removal": {"keywords": ["remove the object", "erase the", "delete the object"], "weight": 5},
    "object_insertion": {"keywords": ["insert a", "place a"], "weight": 5},
    "text_to_video": {"keywords": ["video", "animation", "animate", "motion", "cinematic clip", "footage", "timelapse"], "weight": 3},
    "text_to_audio": {"keywords": ["music", "sound", "audio", "soundtrack"], "weight": 3},
    "text_to_speech": {"keywords": ["speak", "narrate", "tts"], "weight": 3},
    "image_to_image": {"keywords": ["transform", "modify", "restyle"], "weight": 2},
    "text_to_image": {"keywords": ["image", "picture", "photo", "illustration", "render", "drawing", "painting", "generate", "create", "draw", "make", "design"], "weight": 2},
    "chat": {"keywords": ["answer", "explain", "summarize", "summarise", "write", "chat", "tell me", "what is", "how to", "why", "define", "poem", "essay", "translate", "reason about"], "weight": 1},
    "generate_fallback": {"keywords": ["generate", "create", "draw", "make"], "weight": 1},
}


@dataclass
class RouteDecision:
    task_type: str = ""
    confidence: float = 0.0
    recommended_providers: List[Dict[str, Any]] = field(default_factory=list)
    estimated_cost: float = 0.0
    estimated_latency_ms: float = 0.0
    reasoning: str = ""
    alternatives: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_type": self.task_type,
            "confidence": round(self.confidence, 2),
            "recommended_providers": self.recommended_providers[:3],
            "estimated_cost": self.estimated_cost,
            "estimated_latency_ms": self.estimated_latency_ms,
            "reasoning": self.reasoning,
            "alternatives": self.alternatives,
        }


class AutoRouter:
    """Automatically classify, route, and execute media generation tasks."""

    def __init__(self, capability_registry=None, provider_discovery=None,
                 execution_engine=None, provider_verifier=None):
        self._cr = capability_registry
        self._pd = provider_discovery
        self._ee = execution_engine
        self._pv = provider_verifier
        self._route_history: List[RouteDecision] = []

    def classify_task(self, request: str) -> RouteDecision:
        """Classify a natural language request into a task type."""
        request_lower = request.lower()
        scores = {}
        alternatives = []

        for task_type, config in TASK_KEYWORDS.items():
            keywords = config["keywords"]
            weight = config["weight"]
            score = sum(weight for kw in keywords if kw in request_lower)
            if score > 0:
                scores[task_type] = score
                alternatives.append(task_type)

        if not scores:
            return RouteDecision(
                task_type="text_to_image", confidence=0.3,
                reasoning="No strong keyword match; defaulting to text_to_image",
            )

        best_task = max(scores, key=scores.get)
        total = sum(scores.values())
        confidence = min(scores[best_task] / max(total, 1) * 1.2, 1.0)

        recommended = []
        if self._cr:
            models = self._cr.find_models(task=best_task, free_only=False)
            for m in models[:5]:
                recommended.append({
                    "model_id": m["model_id"],
                    "provider": m["provider"],
                    "free_tier": m["free_tier"],
                    "tasks": m["tasks"],
                })

        decision = RouteDecision(
            task_type=best_task, confidence=round(confidence, 2),
            recommended_providers=recommended,
            reasoning=f"Matched {scores[best_task]} keywords for {best_task}",
            alternatives=alternatives[:3],
        )
        self._route_history.append(decision)
        return decision

    async def plan_and_execute(self, request: str, **kwargs) -> Dict[str, Any]:
        """Full pipeline: classify → plan → execute → return result."""
        decision = self.classify_task(request)
        self._route_history.append(decision)

        if not self._ee:
            return {
                "route": decision.to_dict(),
                "execution": {"status": "no_engine", "note": "Execution engine not configured"},
            }

        from .execution_engine import ExecutionTask, TaskType
        task_type_map = {t.value: t for t in TaskType}
        task_type = task_type_map.get(decision.task_type, TaskType.TEXT_TO_IMAGE)

        task = ExecutionTask(
            task_type=task_type,
            prompt=request,
            params=kwargs,
            require_free=kwargs.get("require_free", False),
            timeout_secs=kwargs.get("timeout_secs", 120.0),
        )

        result = await self._ee.execute(task)
        return {
            "route": decision.to_dict(),
            "execution": result.to_dict(),
        }

    def get_route_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        return [r.to_dict() for r in self._route_history[-limit:]]

    def get_stats(self) -> Dict[str, Any]:
        types = {}
        for r in self._route_history:
            types[r.task_type] = types.get(r.task_type, 0) + 1
        return {"total_routes": len(self._route_history), "by_task_type": types}
