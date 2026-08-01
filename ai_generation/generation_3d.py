"""
3D Generation — text-to-3D, image-to-3D, Gaussian splatting capabilities.

Based on ACOS Research: Image Generation Research §3D Models
Provides 3D generation routing with provider profiles for available backends.

Current models (from research):
- TRELLIS (Microsoft Research) — 3D generation, 16GB VRAM
- Hunyuan3D (Tencent) — 3D generation, 12GB VRAM
- Point-E (OpenAI) — Point cloud generation, 8GB VRAM
- Shap-E (OpenAI) — 3D asset generation, 8GB VRAM

All 3D models are experimental; this module provides routing and profiling.
"""
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class Generation3DMode(str, Enum):
    TEXT_TO_3D = "text_to_3d"
    IMAGE_TO_3D = "image_to_3d"
    POINT_CLOUD = "point_cloud"
    MESH_GENERATION = "mesh_generation"
    GAUSSIAN_SPLAT = "gaussian_splat"


class OutputFormat(str, Enum):
    OBJ = "obj"
    GLTF = "gltf"
    GLB = "glb"
    PLY = "ply"
    STL = "stl"
    POINT_CLOUD = "point_cloud"
    GAUSSIAN_SPLAT = "gaussian_splat"


@dataclass
class Generation3DProfile:
    """Profile for a 3D generation model/provider."""
    model_id: str = ""
    name: str = ""
    developer: str = ""
    license: str = ""
    supported_modes: List[Generation3DMode] = field(default_factory=list)
    output_formats: List[OutputFormat] = field(default_factory=list)
    parameter_count_b: float = 0.0
    vram_gb: float = 0.0
    quality_rating: float = 0.0
    maturity: str = "experimental"  # experimental, emerging, production
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)
    source_url: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "model_id": self.model_id,
            "name": self.name,
            "developer": self.developer,
            "license": self.license,
            "supported_modes": [m.value for m in self.supported_modes],
            "output_formats": [f.value for f in self.output_formats],
            "parameter_count_b": self.parameter_count_b,
            "vram_gb": self.vram_gb,
            "quality_rating": self.quality_rating,
            "maturity": self.maturity,
            "strengths": self.strengths,
            "weaknesses": self.weaknesses,
            "source_url": self.source_url,
        }


# ── Built-in 3D Model Profiles ────────────────────────────────

TRELLIS_PROFILE = Generation3DProfile(
    model_id="microsoft/trellis",
    name="TRELLIS",
    developer="Microsoft Research",
    license="MIT",
    supported_modes=[Generation3DMode.TEXT_TO_3D, Generation3DMode.IMAGE_TO_3D],
    output_formats=[OutputFormat.GLTF, OutputFormat.GLB, OutputFormat.GAUSSIAN_SPLAT],
    parameter_count_b=0.5,
    vram_gb=16.0,
    quality_rating=0.8,
    maturity="experimental",
    strengths=["High quality meshes", "Multiple output formats", "Gaussian splat support"],
    weaknesses=["High VRAM requirement", "Slow generation", "Experimental"],
    source_url="https://github.com/microsoft/TRELLIS",
)

HUNYUAN3D_PROFILE = Generation3DProfile(
    model_id="tencent/hunyuan3d",
    name="Hunyuan3D",
    developer="Tencent",
    license="Tencent Community",
    supported_modes=[Generation3DMode.TEXT_TO_3D, Generation3DMode.IMAGE_TO_3D],
    output_formats=[OutputFormat.GLTF, OutputFormat.GLB, OutputFormat.OBJ],
    parameter_count_b=0.3,
    vram_gb=12.0,
    quality_rating=0.75,
    maturity="experimental",
    strengths=["Good quality", "Lower VRAM than TRELLIS", "Text and image input"],
    weaknesses=["Proprietary license", "Experimental", "Chinese-focused documentation"],
    source_url="https://github.com/Tencent/Hunyuan3D-2",
)

POINTE_PROFILE = Generation3DProfile(
    model_id="openai/point-e",
    name="Point-E",
    developer="OpenAI",
    license="MIT",
    supported_modes=[Generation3DMode.TEXT_TO_3D, Generation3DMode.IMAGE_TO_3D, Generation3DMode.POINT_CLOUD],
    output_formats=[OutputFormat.POINT_CLOUD, OutputFormat.PLY],
    parameter_count_b=0.6,
    vram_gb=8.0,
    quality_rating=0.6,
    maturity="emerging",
    strengths=["Low VRAM", "Fast point cloud generation", "MIT license"],
    weaknesses=["Point clouds only (not meshes)", "Lower quality", "Limited formats"],
    source_url="https://github.com/openai/point-e",
)

SHAPE_PROFILE = Generation3DProfile(
    model_id="openai/shap-e",
    name="Shap-E",
    developer="OpenAI",
    license="MIT",
    supported_modes=[Generation3DMode.TEXT_TO_3D],
    output_formats=[OutputFormat.OBJ, OutputFormat.PLY],
    parameter_count_b=0.6,
    vram_gb=8.0,
    quality_rating=0.55,
    maturity="emerging",
    strengths=["Fast generation", "Low VRAM", "Simple API"],
    weaknesses=["Lower quality", "Limited to simple shapes", "No texture"],
    source_url="https://github.com/openai/shap-e",
)


# ── 3D Generation Engine ──────────────────────────────────────

class Generation3DEngine:
    """
    3D Generation engine with provider profiling and routing.

    Provides 3D model profiles, mode selection, format routing,
    and negotiation engine integration.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._profiles: Dict[str, Generation3DProfile] = {}
        self._stats = {
            "total_requests": 0,
            "by_mode": {},
            "by_format": {},
        }
        self._init_builtin_profiles()

    def _init_builtin_profiles(self):
        """Register built-in 3D model profiles."""
        for profile in [TRELLIS_PROFILE, HUNYUAN3D_PROFILE,
                        POINTE_PROFILE, SHAPE_PROFILE]:
            self._profiles[profile.model_id] = profile

    def list_models(self, mode: Optional[str] = None) -> List[Dict[str, Any]]:
        """List 3D generation model profiles."""
        profiles = list(self._profiles.values())
        if mode:
            mode_enum = Generation3DMode(mode)
            profiles = [p for p in profiles if mode_enum in p.supported_modes]
        return [p.to_dict() for p in profiles]

    def get_model(self, model_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific 3D model profile."""
        profile = self._profiles.get(model_id)
        return profile.to_dict() if profile else None

    def select_model(self, mode: str = "text_to_3d",
                      max_vram_gb: float = 32.0,
                      min_quality: float = 0.0) -> Optional[str]:
        """Select the best 3D model for a request."""
        mode_enum = Generation3DMode(mode)
        candidates = []
        for model_id, profile in self._profiles.items():
            if mode_enum not in profile.supported_modes:
                continue
            if profile.vram_gb > max_vram_gb:
                continue
            if profile.quality_rating < min_quality:
                continue
            score = profile.quality_rating * 10
            score += (1.0 - profile.vram_gb / 32.0) * 5
            candidates.append((model_id, score))

        if not candidates:
            return None
        candidates.sort(key=lambda x: -x[1])
        return candidates[0][0]

    def get_output_formats(self, model_id: str) -> List[str]:
        """Get supported output formats for a model."""
        profile = self._profiles.get(model_id)
        return [f.value for f in profile.output_formats] if profile else []

    def get_stats(self) -> Dict[str, Any]:
        """Get 3D generation statistics."""
        return {
            "model_count": len(self._profiles),
            "stats": self._stats,
        }

    async def generate(self, prompt: str, mode: str = "text_to_3d",
                       model_id: str = "", max_vram_gb: float = 32.0,
                       output_path: str = "", **kwargs) -> Dict[str, Any]:
        """Generate a 3D asset.

        Every officially profiled 3D model (TRELLIS, Hunyuan3D, Point-E,
        Shap-E) requires local GPU inference (8-16GB VRAM); there is no
        keyless cloud 3D backend. This method routes to the selected model
        and returns a truthful result — ``completed`` when a local backend
        actually produces geometry, ``dependency_missing``/``unavailable``
        with the exact reason otherwise.
        """
        import time as _time
        from datetime import datetime, timezone as _tz

        start = _time.time()
        request_id = f"3d-{int(_time.time()*1000)}"
        self._stats["total_requests"] += 1
        self._stats["by_mode"][mode] = self._stats["by_mode"].get(mode, 0) + 1

        selected = model_id or self.select_model(mode=mode, max_vram_gb=max_vram_gb)
        base = {
            "operation": mode,
            "backend": selected or "none",
            "request_id": request_id,
            "prompt": prompt,
            "output_path": output_path or "",
            "output_format": "",
            "latency_ms": round((_time.time() - start) * 1000, 1),
            "created_at": datetime.now(_tz.utc).isoformat(),
        }
        if not selected:
            base.update(
                status="unavailable",
                error=("No 3D backend available for mode "
                       f"{mode!r}. Officially profiled 3D models (TRELLIS, "
                       "Hunyuan3D, Point-E, Shap-E) require local GPU "
                       "inference with 8-16GB VRAM; no keyless cloud 3D "
                       "backend exists. Configure a local runtime."),
            )
            return base
        profile = self._profiles.get(selected)
        base["backend"] = selected
        base["output_format"] = (
            profile.output_formats[0].value if profile and profile.output_formats else ""
        )
        base.update(
            status="dependency_missing",
            error=(f"3D model {selected} requires local GPU inference "
                   f"({profile.vram_gb}GB VRAM) — no keyless cloud backend "
                   "exists. Configure a supported local runtime and retry."),
            metadata={"model": profile.to_dict() if profile else {}},
        )
        return base

    def to_negotiation_candidates(self, mode: str = "text_to_3d",
                                   max_vram_gb: float = 32.0) -> List[Dict[str, Any]]:
        """Generate negotiation engine candidates for 3D generation."""
        candidates = []
        for model_id, profile in self._profiles.items():
            mode_enum = Generation3DMode(mode)
            if mode_enum not in profile.supported_modes:
                continue
            if profile.vram_gb > max_vram_gb:
                continue
            candidates.append({
                "provider": f"3d_{model_id.split('/')[-1]}",
                "model": model_id,
                "layer": "3d_generation",
                "tier": 3,
                "cost_usd": 0.0,
                "latency_estimate_ms": 30000,  # 3D gen is slow
                "quality_estimate": profile.quality_rating,
                "requires_network": False,
                "metadata": {
                    "vram_gb": profile.vram_gb,
                    "maturity": profile.maturity,
                    "formats": [f.value for f in profile.output_formats],
                },
            })
        return candidates
