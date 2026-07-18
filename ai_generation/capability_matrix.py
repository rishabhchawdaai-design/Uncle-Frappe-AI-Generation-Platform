"""
Capability Matrix — automatically generate and maintain provider/model capabilities,
supported resolutions, aspect ratios, editing support, batching, streaming,
authentication requirements, and benchmark scores.
"""
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class ModelCapability:
    model_name: str = ""
    provider: str = ""
    type: str = ""  # image, video
    supported_resolutions: List[str] = field(default_factory=list)
    supported_aspect_ratios: List[str] = field(default_factory=list)
    image_editing: bool = False
    video_editing: bool = False
    inpainting: bool = False
    outpainting: bool = False
    img2img: bool = False
    text_to_video: bool = False
    image_to_video: bool = False
    video_to_video: bool = False
    batching: bool = False
    streaming: bool = False
    api_key_required: bool = False
    free_tier: bool = False
    max_batch_size: int = 1
    benchmark_score: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "model_name": self.model_name,
            "provider": self.provider,
            "type": self.type,
            "resolutions": self.supported_resolutions,
            "aspect_ratios": self.supported_aspect_ratios,
            "editing": {
                "image": self.image_editing,
                "video": self.video_editing,
                "inpainting": self.inpainting,
                "outpainting": self.outpainting,
                "img2img": self.img2img,
            },
            "generation": {
                "text_to_video": self.text_to_video,
                "image_to_video": self.image_to_video,
                "video_to_video": self.video_to_video,
            },
            "batching": self.batching,
            "streaming": self.streaming,
            "api_key_required": self.api_key_required,
            "free_tier": self.free_tier,
            "max_batch_size": self.max_batch_size,
            "benchmark_score": self.benchmark_score,
        }


# Pre-populated capability matrix from actual provider documentation
INITIAL_CAPABILITIES = [
    ModelCapability(
        model_name="Flux.1-schnell", provider="pollinations", type="image",
        supported_resolutions=["512x512", "1024x1024", "1024x576", "576x1024", "2048x2048"],
        supported_aspect_ratios=["1:1", "16:9", "9:16", "4:3", "3:4"],
        api_key_required=False, free_tier=True, batching=True, benchmark_score=70.0,
    ),
    ModelCapability(
        model_name="Flux.1-schnell", provider="siliconflow", type="image",
        supported_resolutions=["512x512", "1024x1024", "1024x576", "576x1024", "2048x2048"],
        supported_aspect_ratios=["1:1", "16:9", "9:16", "4:3", "3:4"],
        api_key_required=True, free_tier=True, batching=True, benchmark_score=80.0,
    ),
    ModelCapability(
        model_name="FLUX.1-dev", provider="siliconflow", type="image",
        supported_resolutions=["512x512", "1024x1024", "1024x576", "576x1024", "2048x2048"],
        supported_aspect_ratios=["1:1", "16:9", "9:16", "4:3", "3:4"],
        api_key_required=True, free_tier=True, batching=True, benchmark_score=85.0,
    ),
    ModelCapability(
        model_name="sd3-medium", provider="stability", type="image",
        supported_resolutions=["1024x1024", "1024x576", "576x1024", "1152x896", "896x1152"],
        supported_aspect_ratios=["1:1", "16:9", "9:16", "4:3", "3:4"],
        image_editing=True, img2img=True, inpainting=True, outpainting=True,
        api_key_required=True, free_tier=False, benchmark_score=85.0,
    ),
    ModelCapability(
        model_name="sd3-large", provider="stability", type="image",
        supported_resolutions=["1024x1024", "1024x576", "576x1024", "1152x896", "896x1152"],
        supported_aspect_ratios=["1:1", "16:9", "9:16", "4:3", "3:4"],
        image_editing=True, img2img=True, inpainting=True, outpainting=True,
        api_key_required=True, free_tier=False, benchmark_score=90.0,
    ),
    ModelCapability(
        model_name="sd3.5-large", provider="stability", type="image",
        supported_resolutions=["1024x1024", "1024x576", "576x1024", "1152x896", "896x1152"],
        supported_aspect_ratios=["1:1", "16:9", "9:16", "4:3", "3:4"],
        image_editing=True, img2img=True, inpainting=True, outpainting=True,
        api_key_required=True, free_tier=False, benchmark_score=92.0,
    ),
    ModelCapability(
        model_name="FLUX.1-schnell", provider="replicate", type="image",
        supported_resolutions=["512x512", "1024x1024", "1024x576", "576x1024", "2048x2048"],
        supported_aspect_ratios=["1:1", "16:9", "9:16", "4:3", "3:4"],
        api_key_required=True, free_tier=True, batching=True, benchmark_score=80.0,
    ),
    ModelCapability(
        model_name="flux-dev", provider="replicate", type="image",
        supported_resolutions=["512x512", "1024x1024", "1024x576", "576x1024", "2048x2048"],
        supported_aspect_ratios=["1:1", "16:9", "9:16", "4:3", "3:4"],
        api_key_required=True, free_tier=False, batching=True, benchmark_score=85.0,
    ),
    ModelCapability(
        model_name="stable-video-diffusion", provider="replicate", type="video",
        supported_resolutions=["1024x576", "576x1024"],
        supported_aspect_ratios=["16:9", "9:16"],
        text_to_video=False, image_to_video=True, video_to_video=False,
        api_key_required=True, free_tier=False, benchmark_score=70.0,
    ),
    ModelCapability(
        model_name="animate-diff", provider="replicate", type="video",
        supported_resolutions=["512x512", "768x512", "512x768"],
        supported_aspect_ratios=["1:1", "3:2", "2:3"],
        text_to_video=True, image_to_video=False, video_to_video=False,
        api_key_required=True, free_tier=False, benchmark_score=65.0,
    ),
    ModelCapability(
        model_name="flux-schnell", provider="fal", type="image",
        supported_resolutions=["512x512", "1024x1024", "1024x576", "576x1024", "2048x2048"],
        supported_aspect_ratios=["1:1", "16:9", "9:16", "4:3", "3:4"],
        image_editing=True, img2img=True,
        api_key_required=True, free_tier=False, benchmark_score=80.0,
    ),
    ModelCapability(
        model_name="flux-dev", provider="fal", type="image",
        supported_resolutions=["512x512", "1024x1024", "1024x576", "576x1024", "2048x2048"],
        supported_aspect_ratios=["1:1", "16:9", "9:16", "4:3", "3:4"],
        image_editing=True, img2img=True, inpainting=True,
        api_key_required=True, free_tier=False, benchmark_score=88.0,
    ),
]


class CapabilityMatrix:
    """
    Automatically generate and maintain provider/model capability matrix.
    """

    def __init__(self):
        self._capabilities: List[ModelCapability] = list(INITIAL_CAPABILITIES)
        self._last_updated = datetime.now().isoformat()

    def register_model(self, capability: ModelCapability):
        for i, existing in enumerate(self._capabilities):
            if existing.model_name == capability.model_name and existing.provider == capability.provider:
                self._capabilities[i] = capability
                self._last_updated = datetime.now().isoformat()
                return
        self._capabilities.append(capability)
        self._last_updated = datetime.now().isoformat()

    def get_capabilities(self, provider: Optional[str] = None, model_type: Optional[str] = None) -> List[Dict[str, Any]]:
        results = self._capabilities
        if provider:
            results = [c for c in results if c.provider == provider]
        if model_type:
            results = [c for c in results if c.type == model_type]
        return [c.to_dict() for c in results]

    def get_provider_summary(self) -> Dict[str, Dict[str, Any]]:
        summary = {}
        for cap in self._capabilities:
            if cap.provider not in summary:
                summary[cap.provider] = {
                    "models": 0, "image_models": 0, "video_models": 0,
                    "editing_support": False, "free_tier": False,
                    "avg_benchmark": 0, "scores": [],
                }
            p = summary[cap.provider]
            p["models"] += 1
            if cap.type == "image":
                p["image_models"] += 1
            elif cap.type == "video":
                p["video_models"] += 1
            if cap.image_editing:
                p["editing_support"] = True
            if cap.free_tier:
                p["free_tier"] = True
            if cap.benchmark_score > 0:
                p["scores"].append(cap.benchmark_score)

        for provider, data in summary.items():
            scores = data.pop("scores", [])
            data["avg_benchmark"] = round(sum(scores) / max(len(scores), 1), 1)
        return summary

    def find_best_model(self, task: str, require_free: bool = False) -> List[Dict[str, Any]]:
        task_map = {
            "text_to_image": lambda c: c.type == "image",
            "text_to_video": lambda c: c.text_to_video,
            "image_to_video": lambda c: c.image_to_video,
            "inpainting": lambda c: c.inpainting,
            "outpainting": lambda c: c.outpainting,
            "img2img": lambda c: c.img2img,
            "upscale": lambda c: False,  # no built-in upscale models in matrix
        }
        filter_fn = task_map.get(task, lambda c: True)
        candidates = [c for c in self._capabilities if filter_fn(c)]
        if require_free:
            candidates = [c for c in candidates if c.free_tier]
        candidates.sort(key=lambda c: c.benchmark_score, reverse=True)
        return [c.to_dict() for c in candidates[:5]]

    def get_all_aspect_ratios(self) -> List[str]:
        ratios = set()
        for cap in self._capabilities:
            ratios.update(cap.supported_aspect_ratios)
        return sorted(ratios)

    def get_all_resolutions(self) -> List[str]:
        res = set()
        for cap in self._capabilities:
            res.update(cap.supported_resolutions)
        return sorted(res)

    def get_stats(self) -> Dict[str, Any]:
        providers = set(c.provider for c in self._capabilities)
        return {
            "total_models": len(self._capabilities),
            "providers": len(providers),
            "provider_names": sorted(providers),
            "image_models": sum(1 for c in self._capabilities if c.type == "image"),
            "video_models": sum(1 for c in self._capabilities if c.type == "video"),
            "editing_capable": sum(1 for c in self._capabilities if c.image_editing),
            "free_tier_models": sum(1 for c in self._capabilities if c.free_tier),
            "last_updated": self._last_updated,
        }
