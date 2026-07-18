"""
True Video Generation Layer — separate text→video, image→video, video→video.
Provider capability detection. Ken Burns/slideshow as fallback animation, not AI video.
"""
import asyncio
import hashlib
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class VideoGenMode(str, Enum):
    TEXT_TO_VIDEO = "text_to_video"
    IMAGE_TO_VIDEO = "image_to_video"
    VIDEO_TO_VIDEO = "video_to_video"


class VideoProviderStatus(str, Enum):
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    RATE_LIMITED = "rate_limitied"
    LOADING = "loading"


@dataclass
class VideoCapability:
    mode: VideoGenMode
    supported: bool = False
    max_duration_secs: float = 0.0
    max_resolution: str = ""
    models: List[str] = field(default_factory=list)
    requires_image: bool = False
    notes: str = ""


@dataclass
class VideoGenResult:
    provider: str = ""
    mode: VideoGenMode = VideoGenMode.TEXT_TO_VIDEO
    status: str = "pending"
    request_id: str = ""
    prompt: str = ""
    input_path: str = ""
    output_url: str = ""
    output_path: str = ""
    output_format: str = "mp4"
    width: int = 0
    height: int = 0
    duration_secs: float = 0.0
    fps: int = 24
    latency_ms: float = 0.0
    cost_estimate: float = 0.0
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "provider": self.provider, "mode": self.mode.value,
            "status": self.status, "request_id": self.request_id,
            "prompt": self.prompt[:200], "output_url": self.output_url,
            "output_path": self.output_path, "output_format": self.output_format,
            "width": self.width, "height": self.height,
            "duration_secs": self.duration_secs, "fps": self.fps,
            "latency_ms": self.latency_ms, "cost_estimate": self.cost_estimate,
            "error": self.error, "created_at": self.created_at,
        }


# Provider capability definitions — ground truth, not simulated
PROVIDER_VIDEO_CAPABILITIES = {
    "replicate_video": [
        VideoCapability(
            mode=VideoGenMode.TEXT_TO_VIDEO, supported=True,
            max_duration_secs=6.0, max_resolution="1024x576",
            models=["stability-ai/stable-video-diffusion", "lucataco/animate-diff-v2-1"],
            notes="SVD requires image input for best results. AnimateDiff supports text-to-video.",
        ),
        VideoCapability(
            mode=VideoGenMode.IMAGE_TO_VIDEO, supported=True,
            max_duration_secs=6.0, max_resolution="1024x576",
            models=["stability-ai/stable-video-diffusion"],
            requires_image=True,
            notes="SVD excels at image-to-video. Input image strongly recommended.",
        ),
        VideoCapability(
            mode=VideoGenMode.VIDEO_TO_VIDEO, supported=False,
            notes="No true video-to-video model available on Replicate currently.",
        ),
    ],
}


class KenBurnsFallback:
    """
    Ken Burns effect / slideshow animation — NOT AI video generation.
    This is a fallback for when true AI video is unavailable.
    Produces camera-movement-style animation from static images.
    """

    def __init__(self):
        self.name = "ken_burns"

    def describe(self) -> Dict[str, Any]:
        return {
            "name": "Ken Burns Fallback",
            "type": "animation",
            "not_ai_video": True,
            "description": "Camera movement animation from static images. Not true AI video generation.",
            "capabilities": ["zoom_in", "zoom_out", "pan_left", "pan_right", "pan_up", "pan_down"],
        }

    async def generate(
        self,
        image_path: str,
        effect: str = "zoom_in",
        duration_secs: float = 4.0,
        fps: int = 24,
        output_path: str = "",
    ) -> VideoGenResult:
        """Generate Ken Burns animation from a static image."""
        request_id = f"kb-{int(time.time() * 1000)}"
        start = time.time()

        try:
            from PIL import Image
            img = Image.open(image_path)
            width, height = img.size
            total_frames = int(duration_secs * fps)

            output_dir = Path(output_path).parent if output_path else Path("./output/videos")
            output_dir.mkdir(parents=True, exist_ok=True)
            out_path = output_path or str(output_dir / f"{request_id}.gif")

            frames = []
            for i in range(min(total_frames, 60)):
                progress = i / max(total_frames - 1, 1)
                if effect == "zoom_in":
                    scale = 1.0 + progress * 0.3
                    new_w, new_h = int(width / scale), int(height / scale)
                    left = (width - new_w) // 2
                    top = (height - new_h) // 2
                    frame = img.crop((left, top, left + new_w, top + new_h))
                    frame = frame.resize((width, height), Image.LANCZOS)
                elif effect == "zoom_out":
                    scale = 1.3 - progress * 0.3
                    new_w, new_h = int(width * scale), int(height * scale)
                    frame = img.resize((new_w, new_h), Image.LANCZOS)
                    left = (new_w - width) // 2
                    top = (new_h - height) // 2
                    frame = frame.crop((left, top, left + width, top + height))
                elif effect == "pan_right":
                    offset = int(progress * width * 0.2)
                    frame = img.crop((offset, 0, offset + width, height))
                    if frame.size != (width, height):
                        frame = frame.resize((width, height), Image.LANCZOS)
                else:
                    frame = img.copy()
                frames.append(frame)

            frames[0].save(
                out_path, save_all=True, append_images=frames[1:],
                duration=int(1000 / fps), loop=0,
            )
            latency_ms = round((time.time() - start) * 1000, 1)

            return VideoGenResult(
                provider="ken_burns", mode=VideoGenMode.IMAGE_TO_VIDEO,
                status="completed", request_id=request_id,
                input_path=image_path, output_path=out_path,
                output_format="gif", width=width, height=height,
                duration_secs=duration_secs, fps=fps, latency_ms=latency_ms,
                metadata={"not_ai_video": True, "effect": effect, "frame_count": len(frames)},
            )
        except ImportError:
            latency_ms = round((time.time() - start) * 1000, 1)
            return VideoGenResult(
                provider="ken_burns", mode=VideoGenMode.IMAGE_TO_VIDEO,
                status="failed", request_id=request_id, input_path=image_path,
                error="Pillow not installed. pip install Pillow",
                latency_ms=latency_ms,
            )
        except Exception as e:
            latency_ms = round((time.time() - start) * 1000, 1)
            return VideoGenResult(
                provider="ken_burns", mode=VideoGenMode.IMAGE_TO_VIDEO,
                status="failed", request_id=request_id, input_path=image_path,
                error=str(e)[:200], latency_ms=latency_ms,
            )


class VideoProvider:
    """Wrapper for a video generation provider with capability detection."""

    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        self.name = name
        self.config = config or {}
        self._capabilities = PROVIDER_VIDEO_CAPABILITIES.get(name, [])
        self._success_count = 0
        self._error_count = 0
        self._total_latency_ms = 0.0
        self._status = VideoProviderStatus.AVAILABLE

    def get_capabilities(self, mode: Optional[VideoGenMode] = None) -> List[VideoCapability]:
        if mode:
            return [c for c in self._capabilities if c.mode == mode and c.supported]
        return [c for c in self._capabilities if c.supported]

    def supports_mode(self, mode: VideoGenMode) -> bool:
        return any(c.supported for c in self._capabilities if c.mode == mode)

    def get_max_duration(self, mode: VideoGenMode) -> float:
        caps = self.get_capabilities(mode)
        return max((c.max_duration_secs for c in caps), default=0.0)

    def record_success(self, latency_ms: float):
        self._success_count += 1
        self._total_latency_ms += latency_ms

    def record_error(self):
        self._error_count += 1

    @property
    def is_available(self) -> bool:
        return self._status == VideoProviderStatus.AVAILABLE

    async def generate(self, mode: VideoGenMode, prompt="", image_path="",
                       duration_secs=4.0, width=1280, height=720, fps=24,
                       **kwargs) -> VideoGenResult:
        """Generate video. Override in provider-specific subclasses."""
        return VideoGenResult(
            provider=self.name, mode=mode, status="failed",
            error=f"Provider {self.name} not implemented",
        )


class ReplicateVideoGenProvider(VideoProvider):
    """Replicate video generation — SVD, AnimateDiff."""

    def __init__(self, config=None):
        super().__init__("replicate_video", config)
        import os
        self._api_key = self.config.get("api_key") or os.environ.get("REPLICATE_API_TOKEN", "")

    async def generate(self, mode=VideoGenMode.TEXT_TO_VIDEO, prompt="", image_path="",
                       duration_secs=4.0, width=1280, height=720, fps=24,
                       **kwargs) -> VideoGenResult:
        request_id = f"vid-{int(time.time() * 1000)}-{hashlib.sha256(prompt.encode()).hexdigest()[:6]}"
        start = time.time()

        if not self._api_key:
            return VideoGenResult(
                provider=self.name, mode=mode, status="failed",
                request_id=request_id, prompt=prompt,
                error="No REPLICATE_API_TOKEN set",
            )

        if not self.supports_mode(mode):
            return VideoGenResult(
                provider=self.name, mode=mode, status="failed",
                request_id=request_id, prompt=prompt,
                error=f"Provider does not support {mode.value}",
            )

        caps = self.get_capabilities(mode)
        model = caps[0].models[0] if caps else "stability-ai/stable-video-diffusion"
        input_data = {"prompt": prompt, "num_frames": int(duration_secs * fps)}
        if image_path:
            input_data["image"] = image_path

        try:
            import httpx
            async with httpx.AsyncClient(timeout=300) as client:
                response = await client.post(
                    "https://api.replicate.com/v1/predictions",
                    json={"version": model, "input": input_data},
                    headers={"Authorization": f"Bearer {self._api_key}", "Content-Type": "application/json"},
                )
                latency_ms = round((time.time() - start) * 1000, 1)

                if response.status_code in (200, 201):
                    data = response.json()
                    if data.get("status") == "succeeded":
                        output = data.get("output", [])
                        output_url = output if isinstance(output, str) else (output[0] if output else "")
                        self.record_success(latency_ms)
                        return VideoGenResult(
                            provider=self.name, mode=mode, status="completed",
                            request_id=request_id, prompt=prompt, input_path=image_path,
                            output_url=output_url, output_format="mp4",
                            width=width, height=height, duration_secs=duration_secs,
                            fps=fps, latency_ms=latency_ms,
                            metadata={"model": model},
                        )
                    self.record_error()
                    return VideoGenResult(
                        provider=self.name, mode=mode, status="failed",
                        request_id=request_id, prompt=prompt,
                        error=f"Status: {data.get('status')}",
                        latency_ms=latency_ms,
                    )
                self.record_error()
                return VideoGenResult(
                    provider=self.name, mode=mode, status="failed",
                    request_id=request_id, prompt=prompt,
                    error=f"HTTP {response.status_code}", latency_ms=latency_ms,
                )
        except Exception as e:
            latency_ms = round((time.time() - start) * 1000, 1)
            self.record_error()
            return VideoGenResult(
                provider=self.name, mode=mode, status="failed",
                request_id=request_id, prompt=prompt, error=str(e)[:200],
                latency_ms=latency_ms,
            )


from pathlib import Path


class VideoGenerationLayer:
    """
    True AI video generation with provider capability detection.
    Ken Burns fallback clearly marked as non-AI animation.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._providers: Dict[str, VideoProvider] = {}
        self._fallback = KenBurnsFallback()
        self._history: List[VideoGenResult] = []
        self._init_providers()

    def _init_providers(self):
        self._providers["replicate_video"] = ReplicateVideoGenProvider(self.config.get("replicate", {}))

    def get_providers_for_mode(self, mode: VideoGenMode) -> List[str]:
        return [name for name, p in self._providers.items()
                if p.supports_mode(mode) and p.is_available]

    def get_capabilities_report(self) -> List[Dict[str, Any]]:
        report = []
        for name, provider in self._providers.items():
            for mode in VideoGenMode:
                caps = provider.get_capabilities(mode)
                if caps:
                    for cap in caps:
                        report.append({
                            "provider": name,
                            "mode": mode.value,
                            "supported": cap.supported,
                            "max_duration_secs": cap.max_duration_secs,
                            "max_resolution": cap.max_resolution,
                            "models": cap.models,
                            "notes": cap.notes,
                        })
        report.append({
            "provider": "ken_burns",
            "mode": "image_to_video",
            "supported": True,
            "max_duration_secs": 30.0,
            "max_resolution": "any",
            "models": [],
            "notes": "NOT AI video. Camera animation from static images. Fallback only.",
            "not_ai_video": True,
        })
        return report

    async def generate(
        self,
        mode: VideoGenMode,
        prompt: str = "",
        image_path: str = "",
        duration_secs: float = 4.0,
        width: int = 1280,
        height: int = 720,
        fps: int = 24,
        preferred_provider: Optional[str] = None,
        fallback_to_ken_burns: bool = False,
        **kwargs,
    ) -> VideoGenResult:
        """Generate video with provider failover and optional Ken Burns fallback."""
        providers_to_try = []
        if preferred_provider and preferred_provider in self._providers:
            if self._providers[preferred_provider].supports_mode(mode):
                providers_to_try.append(preferred_provider)
        for name in self.get_providers_for_mode(mode):
            if name not in providers_to_try:
                providers_to_try.append(name)

        for provider_name in providers_to_try:
            provider = self._providers[provider_name]
            result = await provider.generate(
                mode=mode, prompt=prompt, image_path=image_path,
                duration_secs=duration_secs, width=width, height=height, fps=fps, **kwargs,
            )
            if result.status == "completed":
                self._history.append(result)
                return result
            logger.warning(f"Video provider {provider_name} failed: {result.error}")

        if fallback_to_ken_burns and image_path:
            logger.info("Falling back to Ken Burns animation (NOT AI video)")
            result = await self._fallback.generate(
                image_path=image_path, duration_secs=duration_secs, fps=fps,
            )
            self._history.append(result)
            return result

        result = VideoGenResult(
            provider="none", mode=mode, status="failed", prompt=prompt,
            error="No video provider available and fallback disabled",
        )
        self._history.append(result)
        return result

    async def text_to_video(self, prompt, **kwargs):
        return await self.generate(VideoGenMode.TEXT_TO_VIDEO, prompt=prompt, **kwargs)

    async def image_to_video(self, image_path, prompt="", **kwargs):
        return await self.generate(VideoGenMode.IMAGE_TO_VIDEO, prompt=prompt, image_path=image_path, **kwargs)

    async def video_to_video(self, video_path, prompt="", **kwargs):
        return await self.generate(VideoGenMode.VIDEO_TO_VIDEO, prompt=prompt, **kwargs)

    def get_fallback_info(self) -> Dict[str, Any]:
        return self._fallback.describe()

    def get_stats(self) -> Dict[str, Any]:
        modes = {}
        for r in self._history:
            modes[r.mode.value] = modes.get(r.mode.value, 0) + 1
        return {
            "total_generations": len(self._history),
            "by_mode": modes,
            "providers": list(self._providers.keys()),
            "has_fallback": True,
            "fallback_is_ai_video": False,
        }
