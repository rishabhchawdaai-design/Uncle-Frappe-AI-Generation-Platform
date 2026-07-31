"""
Execution Engine — 4-layer priority-based remote execution.

Layer 1: Public APIs (official documented endpoints)
Layer 2: Hosted Open-Source (HF Spaces, community inference)
Layer 3: User-Configured Remote (ComfyUI, Forge, custom APIs)
Layer 4: Browser Execution (WebGPU, ONNX, Transformers.js)

Given a task, finds the best available execution path and returns the result.
"""
import asyncio
import hashlib
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Awaitable

logger = logging.getLogger(__name__)


class ExecutionLayer(int, Enum):
    PUBLIC_API = 1
    HOSTED_OPENSOURCE = 2
    USER_CONFIGURED = 3
    BROWSER = 4


class TaskType(str, Enum):
    TEXT_TO_IMAGE = "text_to_image"
    IMAGE_TO_IMAGE = "image_to_image"
    INPAINTING = "inpainting"
    OUTPAINTING = "outpainting"
    UPSCALE = "upscale"
    BACKGROUND_REMOVAL = "background_removal"
    BACKGROUND_REPLACEMENT = "background_replacement"
    STYLE_TRANSFER = "style_transfer"
    OBJECT_REMOVAL = "object_removal"
    OBJECT_INSERTION = "object_insertion"
    RELIGHTING = "relighting"
    TEXT_TO_VIDEO = "text_to_video"
    IMAGE_TO_VIDEO = "image_to_video"
    VIDEO_TO_VIDEO = "video_to_video"
    TEXT_TO_AUDIO = "text_to_audio"
    AUDIO_TO_AUDIO = "audio_to_audio"
    TEXT_TO_SPEECH = "text_to_speech"
    CHAT = "chat"


class ExecutionStatus(str, Enum):
    PENDING = "pending"
    ROUTING = "routing"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    RATE_LIMITED = "rate_limited"
    NO_PROVIDER = "no_provider"


@dataclass
class ExecutionTask:
    task_id: str = ""
    task_type: TaskType = TaskType.TEXT_TO_IMAGE
    prompt: str = ""
    input_data: Optional[Dict[str, Any]] = None
    params: Dict[str, Any] = field(default_factory=dict)
    preferred_layer: Optional[ExecutionLayer] = None
    preferred_provider: Optional[str] = None
    max_retries: int = 2
    timeout_secs: float = 120.0
    require_free: bool = False
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def __post_init__(self):
        if not self.task_id:
            h = hashlib.sha256(f"{self.task_type.value}:{self.prompt}:{time.time()}".encode()).hexdigest()[:10]
            self.task_id = f"task-{h}"


@dataclass
class ExecutionResult:
    task_id: str = ""
    status: ExecutionStatus = ExecutionStatus.PENDING
    layer: Optional[ExecutionLayer] = None
    provider: str = ""
    model: str = ""
    output_url: str = ""
    output_path: str = ""
    output_bytes: Optional[bytes] = None
    output_format: str = ""
    width: int = 0
    height: int = 0
    duration_secs: float = 0.0
    latency_ms: float = 0.0
    cost_estimate: float = 0.0
    attempts: List[Dict[str, Any]] = field(default_factory=list)
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    completed_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "status": self.status.value,
            "layer": self.layer.value if self.layer else None,
            "provider": self.provider,
            "model": self.model,
            "output_url": self.output_url,
            "output_path": self.output_path,
            "output_format": self.output_format,
            "width": self.width,
            "height": self.height,
            "duration_secs": self.duration_secs,
            "latency_ms": self.latency_ms,
            "cost_estimate": self.cost_estimate,
            "attempts_count": len(self.attempts),
            "error": self.error,
            "completed_at": self.completed_at,
        }


@dataclass
class ProviderEndpoint:
    name: str = ""
    layer: ExecutionLayer = ExecutionLayer.PUBLIC_API
    url: str = ""
    auth_type: str = ""  # api_key, bearer, none
    auth_env_var: str = ""
    supported_tasks: List[TaskType] = field(default_factory=list)
    models: List[str] = field(default_factory=list)
    requires_docker: bool = False
    health_url: str = ""
    documentation_url: str = ""
    license_info: str = ""
    max_resolution: str = ""
    free_tier: bool = False
    rate_limit_rpm: int = 0
    estimated_latency_ms: float = 5000
    verified: bool = False
    last_verified: str = ""
    last_health_check: str = ""
    healthy: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


class ExecutionRouter:
    """Routes tasks to the best available endpoint across all layers."""

    def __init__(self):
        self._endpoints: Dict[str, ProviderEndpoint] = {}
        self._handlers: Dict[str, Callable] = {}
        self._history: List[ExecutionResult] = []
        self._layer_priority: List[ExecutionLayer] = [
            ExecutionLayer.PUBLIC_API,
            ExecutionLayer.HOSTED_OPENSOURCE,
            ExecutionLayer.USER_CONFIGURED,
            ExecutionLayer.BROWSER,
        ]

    def register_endpoint(self, endpoint: ProviderEndpoint):
        self._endpoints[endpoint.name] = endpoint

    def register_handler(self, provider_name: str, handler: Callable):
        self._handlers[provider_name] = handler

    def get_endpoints_for_task(
        self,
        task_type: TaskType,
        require_free: bool = False,
        layer: Optional[ExecutionLayer] = None,
    ) -> List[ProviderEndpoint]:
        candidates = []
        for ep in self._endpoints.values():
            if not ep.healthy:
                continue
            if require_free and not ep.free_tier:
                continue
            if layer and ep.layer != layer:
                continue
            if task_type in ep.supported_tasks:
                candidates.append(ep)

        def sort_key(ep):
            layer_score = self._layer_priority.index(ep.layer) if ep.layer in self._layer_priority else 99
            verified_bonus = -10 if ep.verified else 0
            free_bonus = -5 if ep.free_tier else 0
            latency_penalty = ep.estimated_latency_ms / 10000
            return (layer_score + verified_bonus + free_bonus + latency_penalty)

        candidates.sort(key=sort_key)
        return candidates

    async def execute(
        self,
        task: ExecutionTask,
        context: Optional[Dict[str, Any]] = None,
    ) -> ExecutionResult:
        """Execute a task with automatic routing, retry, and failover."""
        endpoints = self.get_endpoints_for_task(
            task.task_type,
            require_free=task.require_free,
            layer=task.preferred_layer,
        )

        if task.preferred_provider and task.preferred_provider in self._endpoints:
            ep = self._endpoints[task.preferred_provider]
            if ep.healthy and task.task_type in ep.supported_tasks:
                endpoints.insert(0, ep)

        if not endpoints:
            result = ExecutionResult(
                task_id=task.task_id,
                status=ExecutionStatus.NO_PROVIDER,
                error=f"No provider available for {task.task_type.value}",
            )
            self._history.append(result)
            return result

        last_error = None
        for ep in endpoints:
            handler = self._handlers.get(ep.name)
            if not handler:
                continue

            for attempt in range(task.max_retries + 1):
                start = time.time()
                try:
                    if asyncio.iscoroutinefunction(handler):
                        result = await asyncio.wait_for(
                            handler(task, ep, context or {}),
                            timeout=task.timeout_secs,
                        )
                    else:
                        result = handler(task, ep, context or {})

                    latency_ms = round((time.time() - start) * 1000, 1)

                    if isinstance(result, ExecutionResult):
                        result.task_id = task.task_id
                        result.layer = ep.layer
                        result.latency_ms = latency_ms
                    elif isinstance(result, dict):
                        result = ExecutionResult(
                            task_id=task.task_id, status=ExecutionStatus.COMPLETED,
                            layer=ep.layer, provider=ep.name,
                            output_url=result.get("output_url", ""),
                            output_path=result.get("output_path", ""),
                            output_format=result.get("format", "png"),
                            latency_ms=latency_ms,
                            metadata=result,
                        )
                    else:
                        result = ExecutionResult(
                            task_id=task.task_id, status=ExecutionStatus.COMPLETED,
                            layer=ep.layer, provider=ep.name,
                            latency_ms=latency_ms,
                        )

                    if hasattr(result, 'status') and result.status != ExecutionStatus.FAILED:
                        result.attempts.append({"provider": ep.name, "attempt": attempt + 1, "status": "success"})
                        self._history.append(result)
                        return result

                    last_error = getattr(result, 'error', 'unknown error')
                    result.attempts.append({"provider": ep.name, "attempt": attempt + 1, "status": "failed", "error": last_error})

                except asyncio.TimeoutError:
                    latency_ms = round((time.time() - start) * 1000, 1)
                    last_error = f"Timeout after {task.timeout_secs}s"
                    ep.healthy = False

                except Exception as e:
                    latency_ms = round((time.time() - start) * 1000, 1)
                    last_error = str(e)[:200]

                logger.warning(f"Provider {ep.name} attempt {attempt + 1} failed: {last_error}")

        result = ExecutionResult(
            task_id=task.task_id, status=ExecutionStatus.FAILED,
            error=f"All providers failed. Last error: {last_error}",
        )
        self._history.append(result)
        return result

    def get_stats(self) -> Dict[str, Any]:
        by_layer = {}
        by_status = {}
        for r in self._history:
            layer = r.layer.value if r.layer else "unknown"
            by_layer[layer] = by_layer.get(layer, 0) + 1
            by_status[r.status.value] = by_status.get(r.status.value, 0) + 1
        return {
            "total_endpoints": len(self._endpoints),
            "total_executions": len(self._history),
            "by_layer": by_layer,
            "by_status": by_status,
        }

    def list_endpoints(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": ep.name,
                "layer": ep.layer.value,
                "url": ep.url,
                "healthy": ep.healthy,
                "verified": ep.verified,
                "free_tier": ep.free_tier,
                "supported_tasks": [t.value for t in ep.supported_tasks],
                "models": ep.models,
            }
            for ep in self._endpoints.values()
        ]


class ExecutionEngine:
    """
    4-layer execution engine with priority-based routing.
    Top-level orchestrator that combines routing, verification, and health.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.router = ExecutionRouter()
        self._initialized = False

    def initialize(self):
        """Register all known endpoints and handlers."""
        if self._initialized:
            return
        self._register_public_api_endpoints()
        self._register_hosted_opensource_endpoints()
        self._register_kimi_k3()
        self._initialized = True

    def _register_kimi_k3(self):
        """Register Kimi K3 official execution paths (cloud API + self-hosted)."""
        from .kimi_k3 import register_kimi_k3
        register_kimi_k3(self)

    def _register_public_api_endpoints(self):
        """Layer 1: Public APIs with documented endpoints."""
        import os
        endpoints = [
            ProviderEndpoint(
                name="pollinations", layer=ExecutionLayer.PUBLIC_API,
                url="https://image.pollinations.ai/prompt",
                auth_type="none",
                supported_tasks=[TaskType.TEXT_TO_IMAGE],
                models=["flux", "flux-realism", "flux-anime", "flux-3d", "turbo"],
                free_tier=True, health_url="https://image.pollinations.ai/health",
                documentation_url="https://pollinations.ai",
                license_info="Free, no API key required",
                max_resolution="2048x2048", verified=True,
            ),
            ProviderEndpoint(
                name="huggingface_inference", layer=ExecutionLayer.PUBLIC_API,
                url="https://api-inference.huggingface.co/models",
                auth_type="api_key", auth_env_var="HUGGINGFACE_API_TOKEN",
                supported_tasks=[TaskType.TEXT_TO_IMAGE, TaskType.IMAGE_TO_IMAGE],
                models=["stabilityai/stable-diffusion-xl-base-1.0", "runwayml/stable-diffusion-v1-5"],
                free_tier=True, health_url="https://huggingface.co/api/models",
                documentation_url="https://huggingface.co/docs/api-inference",
                license_info="Free tier available, rate limited",
                max_resolution="1024x1024", verified=True,
            ),
            ProviderEndpoint(
                name="siliconflow", layer=ExecutionLayer.PUBLIC_API,
                url="https://api.siliconflow.cn/v1/images/generations",
                auth_type="api_key", auth_env_var="SILICONFLOW_API_KEY",
                supported_tasks=[TaskType.TEXT_TO_IMAGE],
                models=["black-forest-labs/FLUX.1-schnell", "black-forest-labs/FLUX.1-dev"],
                free_tier=True, health_url="https://api.siliconflow.cn",
                documentation_url="https://docs.siliconflow.cn",
                license_info="Free tier available",
                max_resolution="2048x2048", verified=True,
            ),
            ProviderEndpoint(
                name="together", layer=ExecutionLayer.PUBLIC_API,
                url="https://api.together.xyz/v1/images/generations",
                auth_type="api_key", auth_env_var="TOGETHER_API_KEY",
                supported_tasks=[TaskType.TEXT_TO_IMAGE],
                models=["black-forest-labs/FLUX.1-schnell-Free", "black-forest-labs/FLUX.1-dev"],
                free_tier=True, health_url="https://api.together.xyz",
                documentation_url="https://docs.together.ai",
                license_info="Free credits for new accounts",
                max_resolution="2048x2048", verified=True,
            ),
            ProviderEndpoint(
                name="stability", layer=ExecutionLayer.PUBLIC_API,
                url="https://api.stability.ai/v2beta",
                auth_type="api_key", auth_env_var="STABILITY_API_KEY",
                supported_tasks=[
                    TaskType.TEXT_TO_IMAGE, TaskType.IMAGE_TO_IMAGE,
                    TaskType.INPAINTING, TaskType.OUTPAINTING,
                    TaskType.STYLE_TRANSFER, TaskType.UPSCALE,
                    TaskType.OBJECT_REMOVAL, TaskType.OBJECT_INSERTION,
                    TaskType.BACKGROUND_REPLACEMENT,
                ],
                models=["sd3-medium", "sd3-large", "sd3.5-large"],
                free_tier=False, health_url="https://api.stability.ai",
                documentation_url="https://platform.stability.ai/docs",
                license_info="Commercial, pay per use",
                max_resolution="2048x2048", verified=True,
            ),
            ProviderEndpoint(
                name="replicate", layer=ExecutionLayer.PUBLIC_API,
                url="https://api.replicate.com/v1/predictions",
                auth_type="api_key", auth_env_var="REPLICATE_API_TOKEN",
                supported_tasks=[
                    TaskType.TEXT_TO_IMAGE, TaskType.IMAGE_TO_IMAGE,
                    TaskType.UPSCALE, TaskType.BACKGROUND_REMOVAL,
                    TaskType.STYLE_TRANSFER,
                    TaskType.TEXT_TO_VIDEO, TaskType.IMAGE_TO_VIDEO,
                ],
                models=["flux-schnell", "flux-dev", "sdxl", "stable-video-diffusion", "animate-diff"],
                free_tier=True, health_url="https://api.replicate.com",
                documentation_url="https://replicate.com/docs",
                license_info="Free tier for Flux-Schnell, pay per use for others",
                max_resolution="2048x2048", verified=True,
            ),
            ProviderEndpoint(
                name="fal", layer=ExecutionLayer.PUBLIC_API,
                url="https://fal.run",
                auth_type="api_key", auth_env_var="FAL_KEY",
                supported_tasks=[TaskType.TEXT_TO_IMAGE, TaskType.IMAGE_TO_IMAGE, TaskType.INPAINTING],
                models=["fal-ai/flux/schnell", "fal-ai/flux/dev", "fal-ai/flux/pro"],
                free_tier=False, health_url="https://fal.ai",
                documentation_url="https://fal.ai/docs",
                license_info="Commercial, pay per use",
                max_resolution="2048x2048", verified=True,
            ),
            ProviderEndpoint(
                name="craiyon", layer=ExecutionLayer.PUBLIC_API,
                url="https://api.craiyon.com/v3",
                auth_type="none",
                supported_tasks=[TaskType.TEXT_TO_IMAGE],
                models=["craiyon-v3"],
                free_tier=True, health_url="https://api.craiyon.com",
                documentation_url="https://www.craiyon.com",
                license_info="Free, no API key",
                max_resolution="512x512", verified=True,
            ),
        ]
        for ep in endpoints:
            self.router.register_endpoint(ep)

    def _register_hosted_opensource_endpoints(self):
        """Layer 2: Hosted open-source services."""
        endpoints = [
            ProviderEndpoint(
                name="hf_spaces_flux", layer=ExecutionLayer.HOSTED_OPENSOURCE,
                url="https://black-forest-labs-flux-1-schnell.hf.space",
                auth_type="none",
                supported_tasks=[TaskType.TEXT_TO_IMAGE],
                models=["flux-schnell"],
                free_tier=True, health_url="https://black-forest-labs-flux-1-schnell.hf.space",
                documentation_url="https://huggingface.co/spaces/black-forest-labs/FLUX.1-schnell",
                license_info="Apache 2.0, hosted on HF Spaces",
                max_resolution="1024x1024", verified=True,
            ),
        ]
        for ep in endpoints:
            self.router.register_endpoint(ep)

    def register_user_endpoint(self, name: str, url: str, auth_type: str = "api_key",
                               auth_env_var: str = "", tasks: Optional[List[TaskType]] = None,
                               models: Optional[List[str]] = None, endpoint_type: str = ""):
        """Layer 3: Register a user-configured remote endpoint."""
        ep = ProviderEndpoint(
            name=name, layer=ExecutionLayer.USER_CONFIGURED,
            url=url, auth_type=auth_type, auth_env_var=auth_env_var,
            supported_tasks=tasks or [TaskType.TEXT_TO_IMAGE],
            models=models or [], free_tier=False,
            verified=False, documentation_url="",
            license_info="User-configured",
        )
        self.router.register_endpoint(ep)
        return ep

    def get_all_endpoints(self) -> List[Dict[str, Any]]:
        return self.router.list_endpoints()

    def get_layer_endpoints(self, layer: ExecutionLayer) -> List[Dict[str, Any]]:
        return [ep for ep in self.router.list_endpoints() if ep["layer"] == layer.value]

    async def execute(self, task: ExecutionTask, **kwargs) -> ExecutionResult:
        self.initialize()
        return await self.router.execute(task, **kwargs)

    async def health_check_all(self) -> Dict[str, Any]:
        results = {}
        for name, ep in self.router._endpoints.items():
            if ep.health_url:
                try:
                    import httpx
                    async with httpx.AsyncClient(timeout=10) as client:
                        r = await client.get(ep.health_url)
                        ep.healthy = r.status_code < 500
                        ep.last_health_check = datetime.now().isoformat()
                        results[name] = {"healthy": ep.healthy, "status_code": r.status_code}
                except Exception as e:
                    ep.healthy = False
                    results[name] = {"healthy": False, "error": str(e)[:100]}
            else:
                results[name] = {"healthy": ep.healthy, "note": "no health URL"}
        return results

    def get_stats(self) -> Dict[str, Any]:
        return self.router.get_stats()
