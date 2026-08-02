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
    # Pollinations — free anonymous text generation (live-verified 2026-08-01)
    ModelEntry(model_id="pollinations-openai-fast", provider="pollinations_text",
               model_name="openai-fast", media_type="text",
               supported_tasks=["chat"], api_key_required=False, free_tier=True,
               known_limits={
                   "tier": "anonymous",
                   "reasoning": True,
                   "tools": True,
                   "output_modalities": ["text"],
               }),
    ModelEntry(model_id="pollinations-openai", provider="pollinations_text",
               model_name="openai", media_type="text",
               supported_tasks=["chat"], api_key_required=False, free_tier=True),
    # Kimi K3 — official execution paths (Moonshot AI)
    ModelEntry(model_id="kimi-k3-cloud", provider="kimi_k3_cloud", model_name="kimi-k3",
               media_type="text", supported_tasks=["chat"],
               api_key_required=True, free_tier=False,
               known_limits={
                   "context_length": 1048576,
                   "reasoning_effort": ["low", "high", "max"],
                   "architecture": "MoE 2.8T total / 104B active",
                   "multimodal": True,
               }),
    ModelEntry(model_id="kimi-k3-vllm", provider="kimi_k3_vllm", model_name="kimi-k3",
               media_type="text", supported_tasks=["chat"],
               api_key_required=False, free_tier=False,
               known_limits={"context_length": 1048576, "engine": "vLLM >= 0.27.0", "min_vram_gb": 1680}),
    ModelEntry(model_id="kimi-k3-sglang", provider="kimi_k3_sglang", model_name="kimi-k3",
               media_type="text", supported_tasks=["chat"],
               api_key_required=False, free_tier=False,
               known_limits={"context_length": 1048576, "engine": "SGLang kimi-k3 image", "min_vram_gb": 1680}),
    # ── Local backends — free, open-weight, self-hostable, CPU (live-verified 2026-08-01) ──
    ModelEntry(model_id="local-minilm-l6-v2", provider="sentence_transformers",
               model_name="all-MiniLM-L6-v2", media_type="text",
               supported_tasks=["text_embedding"],
               api_key_required=False, free_tier=True,
               known_limits={"vector_dim": 384, "runtime": "local-cpu",
                             "verified": "cos_sim 0.858"}),
    ModelEntry(model_id="local-piper-lessac", provider="piper_local",
               model_name="en_US-lessac-medium", media_type="audio",
               supported_tasks=["text_to_speech"],
               api_key_required=False, free_tier=True,
               known_limits={"output_format": "wav", "runtime": "local-cpu",
                             "verified": "2.76s WAV round-trip"}),
    ModelEntry(model_id="local-whisper-tiny", provider="faster_whisper",
               model_name="tiny", media_type="audio",
               supported_tasks=["speech_to_text"],
               api_key_required=False, free_tier=True,
               known_limits={"runtime": "local-cpu", "compute_type": "int8",
                             "verified": "TTS->STT round-trip"}),
    ModelEntry(model_id="local-opus-mt-en-fr", provider="helsinki_opus_mt",
               model_name="opus-mt-en-fr", media_type="text",
               supported_tasks=["translation"],
               api_key_required=False, free_tier=True,
               known_limits={"runtime": "local-cpu", "pairs": ["en-fr", "en-de", "en-es"],
                             "verified": "en->fr live"}),
    ModelEntry(model_id="local-realesrgan-x4v3", provider="realesrgan",
               model_name="realesr-general-x4v3", media_type="image",
               supported_tasks=["upscale"],
               supported_resolutions=["any"],
               api_key_required=False, free_tier=True,
               known_limits={"scale": 4, "runtime": "local-cpu",
                             "verified": "200x60 -> 800x240"}),
    ModelEntry(model_id="local-rembg-u2net", provider="rembg",
               model_name="u2net", media_type="image",
               supported_tasks=["background_removal"],
               api_key_required=False, free_tier=True,
               known_limits={"runtime": "local-cpu", "output": "RGBA PNG",
                             "verified": "88.5% transparent"}),
    ModelEntry(model_id="local-tesseract-5", provider="tesseract_ocr",
               model_name="tesseract-5.3", media_type="image",
               supported_tasks=["text_extraction"],
               api_key_required=False, free_tier=True,
               known_limits={"runtime": "local-cpu", "verified": "exact HELLO WORLD 123"}),
    # ── Storage & Databases (ACOS Storage Architecture) ──
    ModelEntry(model_id="storage-sqlite-local", provider="sqlite_local",
               model_name="sqlite3", media_type="text",
               supported_tasks=["metadata", "ledger", "audit", "cache"],
               api_key_required=False, free_tier=True,
               known_limits={"runtime": "local-stdlib", "engine": "sqlite3"}),
    ModelEntry(model_id="storage-json-local", provider="json_files",
               model_name="json-files", media_type="text",
               supported_tasks=["metadata", "ledger", "graph"],
               api_key_required=False, free_tier=True,
               known_limits={"runtime": "local-stdlib", "engine": "json"}),
    ModelEntry(model_id="storage-postgresql", provider="postgresql",
               model_name="postgresql", media_type="text",
               supported_tasks=["metadata", "ledger", "audit"],
               api_key_required=True, free_tier=False,
               known_limits={"external": True, "status": "not_configured"}),
    ModelEntry(model_id="storage-qdrant", provider="qdrant",
               model_name="qdrant", media_type="text",
               supported_tasks=["embeddings"],
               api_key_required=True, free_tier=False,
               known_limits={"external": True, "status": "not_configured"}),
    ModelEntry(model_id="storage-lancedb", provider="lancedb",
               model_name="lancedb", media_type="text",
               supported_tasks=["embeddings"],
               api_key_required=False, free_tier=True,
               known_limits={"external": True, "status": "not_configured"}),
    ModelEntry(model_id="storage-minio", provider="minio",
               model_name="minio", media_type="text",
               supported_tasks=["artifacts"],
               api_key_required=True, free_tier=False,
               known_limits={"external": True, "status": "not_configured"}),
    ModelEntry(model_id="storage-neo4j", provider="neo4j",
               model_name="neo4j", media_type="text",
               supported_tasks=["graph"],
               api_key_required=True, free_tier=False,
               known_limits={"external": True, "status": "not_configured"}),
    ModelEntry(model_id="storage-prometheus", provider="prometheus",
               model_name="prometheus", media_type="text",
               supported_tasks=["metrics"],
               api_key_required=False, free_tier=True,
               known_limits={"external": True, "status": "not_configured"}),
    ModelEntry(model_id="storage-redis", provider="redis",
               model_name="redis", media_type="text",
               supported_tasks=["cache"],
               api_key_required=True, free_tier=False,
               known_limits={"external": True, "status": "not_configured"}),
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
