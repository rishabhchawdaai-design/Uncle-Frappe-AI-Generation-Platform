"""
Capability Registry — live registry of provider capabilities, models, supported tasks,
media types, resolutions, auth, latency, limits, and benchmark history.
"""
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class ModelEntry:
    model_id: str = ""
    provider: str = ""
    model_name: str = ""
    media_type: str = ""  # image, video, audio
    supported_tasks: List[str] = field(default_factory=list)
    supported_resolutions: List[str] = field(default_factory=list)
    supported_aspect_ratios: List[str] = field(default_factory=list)
    max_batch_size: int = 1
    api_key_required: bool = False
    free_tier: bool = False
    observed_latency_ms: float = 0
    benchmark_history: List[Dict[str, Any]] = field(default_factory=list)
    known_limits: Dict[str, Any] = field(default_factory=dict)
    last_updated: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "model_id": self.model_id,
            "provider": self.provider,
            "model_name": self.model_name,
            "media_type": self.media_type,
            "tasks": self.supported_tasks,
            "resolutions": self.supported_resolutions,
            "aspect_ratios": self.supported_aspect_ratios,
            "max_batch_size": self.max_batch_size,
            "api_key_required": self.api_key_required,
            "free_tier": self.free_tier,
            "observed_latency_ms": self.observed_latency_ms,
            "benchmarks_count": len(self.benchmark_history),
            "known_limits": self.known_limits,
        }


INITIAL_REGISTRY = [
    ModelEntry(model_id="pollinations-flux", provider="pollinations", model_name="flux",
               media_type="image", supported_tasks=["text_to_image"],
               supported_resolutions=["512x512", "1024x1024", "2048x2048"],
               supported_aspect_ratios=["1:1", "16:9", "9:16"],
               free_tier=True, known_limits={"no_api_key": True, "max_resolution": "2048"}),
    ModelEntry(model_id="siliconflow-flux-schnell", provider="siliconflow", model_name="FLUX.1-schnell",
               media_type="image", supported_tasks=["text_to_image"],
               supported_resolutions=["512x512", "1024x1024", "2048x2048"],
               free_tier=True, api_key_required=True),
    ModelEntry(model_id="siliconflow-flux-dev", provider="siliconflow", model_name="FLUX.1-dev",
               media_type="image", supported_tasks=["text_to_image"],
               supported_resolutions=["512x512", "1024x1024", "2048x2048"],
               free_tier=True, api_key_required=True),
    ModelEntry(model_id="together-flux-schnell-free", provider="together", model_name="FLUX.1-schnell-Free",
               media_type="image", supported_tasks=["text_to_image"],
               supported_resolutions=["512x512", "1024x1024", "2048x2048"],
               free_tier=True, api_key_required=True),
    ModelEntry(model_id="stability-sd3-medium", provider="stability", model_name="sd3-medium",
               media_type="image", supported_tasks=["text_to_image", "img2img", "inpainting", "outpainting", "upscale", "style_transfer", "object_removal", "background_replacement"],
               supported_resolutions=["1024x1024", "1024x576", "576x1024"],
               free_tier=False, api_key_required=True),
    ModelEntry(model_id="stability-sd3-large", provider="stability", model_name="sd3-large",
               media_type="image", supported_tasks=["text_to_image", "img2img", "inpainting", "outpainting", "upscale"],
               supported_resolutions=["1024x1024", "1024x576", "576x1024"],
               free_tier=False, api_key_required=True),
    ModelEntry(model_id="stability-sd35-large", provider="stability", model_name="sd3.5-large",
               media_type="image", supported_tasks=["text_to_image", "img2img", "inpainting", "outpainting", "upscale"],
               supported_resolutions=["1024x1024", "1024x576", "576x1024"],
               free_tier=False, api_key_required=True),
    ModelEntry(model_id="replicate-flux-schnell", provider="replicate", model_name="flux-schnell",
               media_type="image", supported_tasks=["text_to_image"],
               supported_resolutions=["512x512", "1024x1024", "2048x2048"],
               free_tier=True, api_key_required=True),
    ModelEntry(model_id="replicate-flux-dev", provider="replicate", model_name="flux-dev",
               media_type="image", supported_tasks=["text_to_image"],
               supported_resolutions=["512x512", "1024x1024", "2048x2048"],
               free_tier=False, api_key_required=True),
    ModelEntry(model_id="replicate-sdxl", provider="replicate", model_name="sdxl",
               media_type="image", supported_tasks=["text_to_image", "img2img"],
               supported_resolutions=["1024x1024"],
               free_tier=False, api_key_required=True),
    ModelEntry(model_id="replicate-svd", provider="replicate", model_name="stable-video-diffusion",
               media_type="video", supported_tasks=["image_to_video"],
               supported_resolutions=["1024x576", "576x1024"],
               free_tier=False, api_key_required=True,
               known_limits={"max_duration_secs": 6, "requires_image_input": True}),
    ModelEntry(model_id="replicate-animatediff", provider="replicate", model_name="animate-diff",
               media_type="video", supported_tasks=["text_to_video"],
               supported_resolutions=["512x512", "768x512"],
               free_tier=False, api_key_required=True),
    ModelEntry(model_id="fal-flux-schnell", provider="fal", model_name="flux-schnell",
               media_type="image", supported_tasks=["text_to_image"],
               supported_resolutions=["512x512", "1024x1024", "2048x2048"],
               free_tier=False, api_key_required=True),
    ModelEntry(model_id="fal-flux-dev", provider="fal", model_name="flux-dev",
               media_type="image", supported_tasks=["text_to_image", "img2img", "inpainting"],
               supported_resolutions=["512x512", "1024x1024", "2048x2048"],
               free_tier=False, api_key_required=True),
    ModelEntry(model_id="craiyon-v3", provider="craiyon", model_name="craiyon-v3",
               media_type="image", supported_tasks=["text_to_image"],
               supported_resolutions=["512x512"],
               free_tier=True, known_limits={"max_resolution": "512x512"}),
    ModelEntry(model_id="hf-sdxl", provider="huggingface_inference", model_name="stabilityai/stable-diffusion-xl-base-1.0",
               media_type="image", supported_tasks=["text_to_image"],
               supported_resolutions=["1024x1024"],
               free_tier=True, api_key_required=True),
]


class CapabilityRegistry:
    """Live registry of provider and model capabilities."""

    def __init__(self):
        self._models: Dict[str, ModelEntry] = {}
        for m in INITIAL_REGISTRY:
            self._models[m.model_id] = m

    def register_model(self, model: ModelEntry):
        self._models[model.model_id] = model

    def find_models(self, task: Optional[str] = None, provider: Optional[str] = None,
                    media_type: Optional[str] = None, free_only: bool = False) -> List[Dict[str, Any]]:
        results = list(self._models.values())
        if task:
            results = [m for m in results if task in m.supported_tasks]
        if provider:
            results = [m for m in results if m.provider == provider]
        if media_type:
            results = [m for m in results if m.media_type == media_type]
        if free_only:
            results = [m for m in results if m.free_tier]
        return [m.to_dict() for m in results]

    def get_model(self, model_id: str) -> Optional[Dict[str, Any]]:
        model = self._models.get(model_id)
        return model.to_dict() if model else None

    def get_providers(self) -> List[str]:
        return sorted(set(m.provider for m in self._models.values()))

    def get_tasks(self) -> List[str]:
        tasks = set()
        for m in self._models.values():
            tasks.update(m.supported_tasks)
        return sorted(tasks)

    def get_summary(self) -> Dict[str, Any]:
        providers = {}
        for m in self._models.values():
            if m.provider not in providers:
                providers[m.provider] = {"models": 0, "tasks": set(), "free_tier": False}
            providers[m.provider]["models"] += 1
            providers[m.provider]["tasks"].update(m.supported_tasks)
            if m.free_tier:
                providers[m.provider]["free_tier"] = True
        for v in providers.values():
            v["tasks"] = list(v["tasks"])
        return {
            "total_models": len(self._models),
            "providers": len(providers),
            "provider_details": providers,
            "total_tasks": len(self.get_tasks()),
            "tasks": self.get_tasks(),
        }

    def get_stats(self) -> Dict[str, Any]:
        return {
            "total_models": len(self._models),
            "providers": len(self.get_providers()),
            "tasks": len(self.get_tasks()),
            "free_models": sum(1 for m in self._models.values() if m.free_tier),
        }
