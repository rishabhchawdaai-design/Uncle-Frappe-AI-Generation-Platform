"""
Provider base classes for the AI Generation Platform.
All providers inherit from these abstractions.
"""
import asyncio
import time
import hashlib
import logging
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


class ProviderType(str, Enum):
    IMAGE = "image"
    VIDEO = "video"
    IMAGE_EDIT = "image_edit"
    VIDEO_EDIT = "video_edit"
    TEXT = "text"
    AUDIO = "audio"


class ProviderTier(str, Enum):
    FREE = "free"
    COMMUNITY = "community"
    PAID = "paid"
    ENTERPRISE = "enterprise"


class ProviderStatus(str, Enum):
    AVAILABLE = "available"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"
    RATE_LIMITED = "rate_limited"
    MAINTENANCE = "maintenance"


@dataclass
class ProviderCapability:
    name: str
    description: str = ""
    input_types: List[str] = field(default_factory=list)
    output_types: List[str] = field(default_factory=list)
    max_resolution: Optional[str] = None
    max_duration_secs: Optional[float] = None
    supports_negative_prompt: bool = False
    supports_seed: bool = False
    supports_style: bool = False


@dataclass
class GenerationResult:
    """Unified result from any provider generation."""
    provider: str = ""
    provider_type: str = ""
    status: str = "pending"  # pending, success, error, timeout, rate_limited
    request_id: str = ""
    output_url: Optional[str] = None
    output_path: Optional[str] = None
    output_bytes: Optional[bytes] = None
    output_format: str = "png"
    width: int = 0
    height: int = 0
    duration_secs: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    cost_estimate: float = 0.0
    latency_ms: float = 0.0
    error: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    prompt: str = ""
    seed: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "provider": self.provider,
            "provider_type": self.provider_type,
            "status": self.status,
            "request_id": self.request_id,
            "output_url": self.output_url,
            "output_path": self.output_path,
            "output_format": self.output_format,
            "width": self.width,
            "height": self.height,
            "duration_secs": self.duration_secs,
            "metadata": self.metadata,
            "cost_estimate": self.cost_estimate,
            "latency_ms": self.latency_ms,
            "error": self.error,
            "created_at": self.created_at,
            "prompt": self.prompt[:200],
            "seed": self.seed,
        }

    @property
    def success(self) -> bool:
        return self.status == "success"

    @property
    def content_hash(self) -> str:
        if self.output_bytes:
            return hashlib.sha256(self.output_bytes).hexdigest()[:16]
        return ""


class Provider(ABC):
    """Abstract base class for all AI generation providers."""

    name: str = "base"
    provider_type: ProviderType = ProviderType.IMAGE
    tier: ProviderTier = ProviderTier.FREE
    requires_api_key: bool = False
    requires_docker: bool = False
    cloud_first: bool = True
    capabilities: List[ProviderCapability] = field(default_factory=list)
    supported_models: List[str] = field(default_factory=list)
    default_model: str = ""
    base_url: str = ""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._status = ProviderStatus.AVAILABLE
        self._error_count = 0
        self._success_count = 0
        self._total_latency_ms = 0.0
        self._last_error: Optional[str] = None
        self._last_used: Optional[str] = None
        self._rate_limit_reset: Optional[float] = None

    @property
    def api_key(self) -> str:
        env_var = f"{self.name.upper().replace('-', '_')}_API_KEY"
        return self.config.get("api_key") or os.environ.get(env_var, "")

    @property
    def avg_latency_ms(self) -> float:
        total = self._success_count + self._error_count
        return self._total_latency_ms / max(total, 1)

    @property
    def success_rate(self) -> float:
        total = self._success_count + self._error_count
        return self._success_count / max(total, 1) * 100

    @property
    def is_available(self) -> bool:
        if self._status in (ProviderStatus.UNAVAILABLE, ProviderStatus.MAINTENANCE):
            return False
        if self._rate_limit_reset and time.time() < self._rate_limit_reset:
            return False
        if self._error_count > 5 and self.success_rate < 20:
            return False
        return True

    def record_success(self, latency_ms: float):
        self._success_count += 1
        self._total_latency_ms += latency_ms
        self._status = ProviderStatus.AVAILABLE
        self._error_count = max(0, self._error_count - 1)

    def record_error(self, error: str, is_rate_limit: bool = False):
        self._error_count += 1
        self._last_error = error
        if is_rate_limit:
            self._status = ProviderStatus.RATE_LIMITED
            self._rate_limit_reset = time.time() + 60
        elif self._error_count > 10:
            self._status = ProviderStatus.UNAVAILABLE

    def get_stats(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "type": self.provider_type.value,
            "tier": self.tier.value,
            "status": self._status.value,
            "success_count": self._success_count,
            "error_count": self._error_count,
            "success_rate": round(self.success_rate, 1),
            "avg_latency_ms": round(self.avg_latency_ms, 1),
            "cloud_first": self.cloud_first,
            "requires_api_key": self.requires_api_key,
            "has_api_key": bool(self.api_key),
            "models": self.supported_models,
            "capabilities": [c.name for c in self.capabilities],
        }

    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> GenerationResult:
        """Generate media from a prompt."""
        raise NotImplementedError

    async def health_check(self) -> Dict[str, Any]:
        return {
            "provider": self.name,
            "status": self._status.value,
            "available": self.is_available,
            "success_rate": round(self.success_rate, 1),
        }

    def _make_request_id(self) -> str:
        ts = int(time.time() * 1000)
        h = hashlib.sha256(f"{self.name}:{ts}:{id(self)}".encode()).hexdigest()[:8]
        return f"{self.name}-{ts}-{h}"


class ImageProvider(Provider):
    """Base class for image generation providers."""
    provider_type: ProviderType = ProviderType.IMAGE

    @abstractmethod
    async def generate_image(
        self,
        prompt: str,
        width: int = 1024,
        height: int = 1024,
        negative_prompt: str = "",
        seed: Optional[int] = None,
        model: str = "",
        style: str = "",
        **kwargs,
    ) -> GenerationResult:
        raise NotImplementedError

    async def generate(self, prompt: str, **kwargs) -> GenerationResult:
        return await self.generate_image(prompt, **kwargs)


class VideoProvider(Provider):
    """Base class for video generation providers."""
    provider_type: ProviderType = ProviderType.VIDEO

    @abstractmethod
    async def generate_video(
        self,
        prompt: str,
        duration_secs: float = 4.0,
        width: int = 1280,
        height: int = 720,
        fps: int = 24,
        negative_prompt: str = "",
        seed: Optional[int] = None,
        model: str = "",
        **kwargs,
    ) -> GenerationResult:
        raise NotImplementedError

    async def generate(self, prompt: str, **kwargs) -> GenerationResult:
        return await self.generate_video(prompt, **kwargs)


class EditProvider(Provider):
    """Base class for image/video editing providers."""
    provider_type: ProviderType = ProviderType.IMAGE_EDIT

    @abstractmethod
    async def edit(
        self,
        input_path: str,
        prompt: str,
        **kwargs,
    ) -> GenerationResult:
        raise NotImplementedError

    async def generate(self, prompt: str, **kwargs) -> GenerationResult:
        return await self.edit(
            kwargs.get("input_path", ""),
            prompt,
            **{k: v for k, v in kwargs.items() if k != "input_path"},
        )
