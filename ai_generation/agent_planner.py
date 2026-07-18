"""
Agent Planning Layer — receives a natural language request like
"Create a luxury cafe advertisement" and automatically plans:
prompts, storyboard, required assets, workflow, provider selection,
benchmark strategy, quality evaluation, export pipeline.
"""
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class PlanStep:
    step_id: str = ""
    name: str = ""
    description: str = ""
    action: str = ""
    params: Dict[str, Any] = field(default_factory=dict)
    depends_on: List[str] = field(default_factory=list)
    provider: str = ""
    priority: int = 5
    estimated_cost: float = 0.0
    estimated_latency_ms: float = 0.0
    status: str = "planned"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_id": self.step_id,
            "name": self.name,
            "description": self.description,
            "action": self.action,
            "params": self.params,
            "depends_on": self.depends_on,
            "provider": self.provider,
            "priority": self.priority,
            "estimated_cost": self.estimated_cost,
            "estimated_latency_ms": self.estimated_latency_ms,
            "status": self.status,
        }


@dataclass
class GenerationPlan:
    request: str = ""
    plan_id: str = ""
    category: str = ""
    steps: List[PlanStep] = field(default_factory=list)
    recommended_providers: List[str] = field(default_factory=list)
    prompts: List[Dict[str, Any]] = field(default_factory=list)
    assets_required: List[str] = field(default_factory=list)
    workflow_template: str = ""
    total_estimated_cost: float = 0.0
    total_estimated_latency_ms: float = 0.0
    quality_checkpoints: List[str] = field(default_factory=list)
    export_formats: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "request": self.request[:200],
            "plan_id": self.plan_id,
            "category": self.category,
            "steps_count": len(self.steps),
            "steps": [s.to_dict() for s in self.steps],
            "recommended_providers": self.recommended_providers,
            "prompts": self.prompts,
            "assets_required": self.assets_required,
            "workflow_template": self.workflow_template,
            "total_estimated_cost": self.total_estimated_cost,
            "total_estimated_latency_ms": self.total_estimated_latency_ms,
            "quality_checkpoints": self.quality_checkpoints,
            "export_formats": self.export_formats,
            "created_at": self.created_at,
        }


CATEGORY_PATTERNS = {
    "advertisement": ["ad", "advertisement", "commercial", "promo", "marketing", "banner", "poster", "flyer"],
    "cinematic": ["cinematic", "movie", "film", "scene", "shot", "sequence", "storyboard"],
    "character": ["character", "portrait", "person", "figure", "avatar", "persona"],
    "landscape": ["landscape", "scenery", "nature", "cityscape", "panorama", "environment"],
    "product": ["product", "showcase", "display", "catalog", "e-commerce"],
    "food": ["food", "dish", "menu", "restaurant", "cafe", "cuisine"],
    "brand": ["brand", "logo", "identity", "style guide", "branding"],
    "social_media": ["social", "instagram", "tiktok", "reel", "story", "post"],
    "animation": ["animation", "animated", "cartoon", "anime", "motion"],
}


class AgentPlanner:
    """
    Plans complete media production from a natural language request.
    """

    def __init__(self, media_intelligence=None, capability_matrix=None,
                 prompt_engine=None, project_manager=None):
        self._mi = media_intelligence
        self._cm = capability_matrix
        self._pe = prompt_engine
        self._pm = project_manager
        self._history: List[GenerationPlan] = []

    def _classify_request(self, request: str) -> str:
        request_lower = request.lower()
        for category, keywords in CATEGORY_PATTERNS.items():
            if any(kw in request_lower for kw in keywords):
                return category
        return "general"

    def _estimate_complexity(self, request: str) -> str:
        word_count = len(request.split())
        if word_count > 50:
            return "production"
        if word_count > 20:
            return "complex"
        if word_count > 8:
            return "moderate"
        return "simple"

    def plan(self, request: str, project_id: Optional[str] = None) -> GenerationPlan:
        import uuid
        plan = GenerationPlan(
            request=request,
            plan_id="plan-" + uuid.uuid4().hex[:8],
        )

        category = self._classify_request(request)
        plan.category = category
        complexity = self._estimate_complexity(request)

        steps = []
        prompts = []
        providers = []
        quality_checks = []
        export_formats = ["png"]

        steps.append(PlanStep(
            step_id="analyze",
            name="Analyze Request",
            description=f"Classify and analyze the request (category={category}, complexity={complexity})",
            action="analyze_request", priority=1,
        ))

        if self._pe:
            enhancement = self._pe.enhance(request, style="photorealistic", quality="high")
            prompts.append({
                "prompt": enhancement.enhanced,
                "negative_prompt": enhancement.negative_prompt,
                "style": "photorealistic",
                "techniques": enhancement.techniques_applied,
            })
            steps.append(PlanStep(
                step_id="enhance_prompt",
                name="Enhance Prompt",
                description="Enhance the prompt with quality modifiers and style",
                action="enhance_prompt", depends_on=["analyze"],
                params={"original": request, "enhanced": enhancement.enhanced},
                priority=2,
            ))

        if category == "advertisement":
            providers = ["pollinations", "siliconflow", "stability"]
            export_formats.extend(["jpg", "webp", "svg"])
            steps.append(PlanStep(
                step_id="generate_hero",
                name="Generate Hero Image",
                description="Generate the main advertisement image",
                action="generate_image",
                depends_on=["enhance_prompt"] if len(steps) > 1 else ["analyze"],
                provider=providers[0], priority=3,
                estimated_cost=0.0,
            ))
            steps.append(PlanStep(
                step_id="generate_variants",
                name="Generate Variants",
                description="Generate 2-3 alternative compositions",
                action="batch_generate",
                depends_on=["generate_hero"],
                provider=providers[1] if len(providers) > 1 else providers[0],
                priority=4,
            ))
            quality_checks.extend(["realism", "prompt_adherence", "lighting", "composition"])
        elif category == "cinematic":
            providers = ["replicate", "stability", "pollinations"]
            export_formats.extend(["mp4", "webm"])
            plan.workflow_template = "full_cinematic"
            steps.extend([
                PlanStep(step_id="storyboard", name="Create Storyboard",
                        action="create_storyboard", depends_on=["enhance_prompt"], priority=3),
                PlanStep(step_id="character_design", name="Design Characters",
                        action="character_design", depends_on=["storyboard"], priority=4),
                PlanStep(step_id="master_frames", name="Generate Master Frames",
                        action="batch_generate", depends_on=["character_design"],
                        provider=providers[0], priority=5),
                PlanStep(step_id="video_gen", name="Generate Video",
                        action="generate_video", depends_on=["master_frames"],
                        provider="replicate_video", priority=6),
                PlanStep(step_id="upscale", name="Upscale", action="upscale",
                        depends_on=["video_gen"], priority=7),
                PlanStep(step_id="color_grade", name="Color Grade",
                        action="color_grade", depends_on=["upscale"], priority=8),
            ])
            quality_checks.extend(["realism", "temporal_consistency", "identity_consistency", "motion_quality"])
        elif category == "food":
            providers = ["pollinations", "siliconflow", "stability"]
            export_formats.extend(["jpg", "webp"])
            steps.append(PlanStep(
                step_id="generate_food",
                name="Generate Food Image",
                description="Generate appetizing food photography",
                action="generate_image",
                depends_on=["enhance_prompt"] if prompts else ["analyze"],
                provider=providers[0], priority=3,
            ))
            steps.append(PlanStep(
                step_id="enhance_food",
                name="Enhance Food Image",
                description="Apply food-specific style and quality",
                action="generate_image",
                depends_on=["generate_food"],
                provider=providers[0], priority=4,
                params={"style": "food_photo"},
            ))
            quality_checks.extend(["realism", "prompt_adherence", "lighting"])
        elif category == "character":
            providers = ["stability", "replicate", "siliconflow"]
            steps.extend([
                PlanStep(step_id="character_sheet", name="Character Sheet",
                        action="character_design", depends_on=["enhance_prompt"], priority=3),
                PlanStep(step_id="generate_character", name="Generate Character",
                        action="generate_image",
                        depends_on=["character_sheet"],
                        provider=providers[0], priority=4),
                PlanStep(step_id="generate_variants", name="Generate Variants",
                        action="batch_generate", depends_on=["generate_character"],
                        provider=providers[1] if len(providers) > 1 else providers[0],
                        priority=5),
            ])
            quality_checks.extend(["anatomy", "prompt_adherence", "composition"])
        else:
            providers = ["pollinations", "siliconflow", "together"]
            steps.append(PlanStep(
                step_id="generate",
                name="Generate Image",
                action="generate_image",
                depends_on=["enhance_prompt"] if prompts else ["analyze"],
                provider=providers[0], priority=3,
            ))
            quality_checks.extend(["realism", "prompt_adherence"])

        steps.append(PlanStep(
            step_id="quality_check",
            name="Quality Evaluation",
            description="Evaluate generated output quality",
            action="quality_eval",
            depends_on=[s.step_id for s in steps if s.action in ("generate_image", "generate_video", "batch_generate")][-1:] or ["analyze"],
            priority=9,
        ))
        steps.append(PlanStep(
            step_id="export",
            name="Export",
            description=f"Export in formats: {', '.join(export_formats)}",
            action="export",
            depends_on=["quality_check"],
            priority=10,
        ))

        plan.steps = steps
        plan.recommended_providers = providers
        plan.prompts = prompts
        plan.workflow_template = plan.workflow_template or "simple_generation_pipeline"
        plan.quality_checkpoints = quality_checks
        plan.export_formats = export_formats

        plan.total_estimated_cost = sum(s.estimated_cost for s in steps)
        plan.total_estimated_latency_ms = sum(s.estimated_latency_ms for s in steps)

        self._history.append(plan)
        return plan

    def get_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        return [p.to_dict() for p in self._history[-limit:]]

    def get_stats(self) -> Dict[str, Any]:
        categories = {}
        for p in self._history:
            categories[p.category] = categories.get(p.category, 0) + 1
        return {
            "total_plans": len(self._history),
            "by_category": categories,
        }
