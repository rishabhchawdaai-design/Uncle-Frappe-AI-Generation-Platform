"""
Generation Manager — Intelligent provider routing, cloud-first execution,
automatic failover, and request orchestration.
"""
import asyncio
import logging
import time
import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .providers.base import (
    Provider, ImageProvider, VideoProvider, EditProvider,
    ProviderType, ProviderTier, ProviderStatus, GenerationResult,
)
from .providers.registry import get_registry

logger = logging.getLogger(__name__)


@dataclass
class GenerationRequest:
    """A request to generate media."""
    prompt: str
    provider_type: ProviderType = ProviderType.IMAGE
    preferred_provider: Optional[str] = None
    width: int = 1024
    height: int = 1024
    duration_secs: float = 4.0
    negative_prompt: str = ""
    seed: Optional[int] = None
    model: str = ""
    style: str = ""
    max_retries: int = 3
    prefer_free: bool = True
    prefer_cloud: bool = True
    timeout_secs: float = 180.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def request_id(self) -> str:
        h = hashlib.sha256(f"{self.prompt}:{self.provider_type.value}:{time.time()}".encode()).hexdigest()[:12]
        return f"req-{h}"


@dataclass
class GenerationPlan:
    """Execution plan for a generation request."""
    request: GenerationRequest
    provider_order: List[str] = field(default_factory=list)
    current_index: int = 0
    attempts: List[Dict[str, Any]] = field(default_factory=list)
    started_at: str = field(default_factory=lambda: datetime.now().isoformat())

    @property
    def current_provider(self) -> Optional[str]:
        if self.current_index < len(self.provider_order):
            return self.provider_order[self.current_index]
        return None

    def advance(self):
        self.current_index += 1

    def record_attempt(self, provider: str, result: GenerationResult):
        self.attempts.append({
            "provider": provider,
            "status": result.status,
            "latency_ms": result.latency_ms,
            "error": result.error,
            "attempt": len(self.attempts) + 1,
        })


class GenerationManager:
    """
    Master orchestrator for AI media generation.
    Intelligent routing, cloud-first execution, automatic failover.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._registry = get_registry()
        self._history: List[Dict[str, Any]] = []
        self._output_dir = Path(self.config.get("output_dir", "./output/generations"))
        self._output_dir.mkdir(parents=True, exist_ok=True)

    def plan_generation(self, request: GenerationRequest) -> GenerationPlan:
        """Create an execution plan with ordered provider list."""
        providers = []

        if request.preferred_provider:
            p = self._registry.get(request.preferred_provider)
            if p and p.is_available:
                providers.append(request.preferred_provider)

        available = self._registry.get_available(request.provider_type)
        for p in available:
            if p.name not in providers:
                providers.append(p.name)

        if not providers:
            all_p = self._registry.get_by_type(request.provider_type)
            providers = [p.name for p in all_p]

        return GenerationPlan(request=request, provider_order=providers)

    async def generate(self, request: GenerationRequest) -> GenerationResult:
        """Generate media with intelligent routing and automatic failover."""
        plan = self.plan_generation(request)
        logger.info(
            f"Generation plan: {len(plan.provider_order)} providers, "
            f"type={request.provider_type.value}, prompt={request.prompt[:50]}"
        )

        last_result = None
        for provider_name in plan.provider_order:
            provider = self._registry.get(provider_name)
            if not provider or not provider.is_available:
                continue

            if not self._has_required_keys(provider, request):
                logger.debug(f"Skipping {provider_name}: missing API key")
                continue

            result = await self._execute_generation(provider, request)
            plan.record_attempt(provider_name, result)

            if result.success:
                await self._save_result(result, request)
                self._record_history(request, plan, result)
                return result

            last_result = result
            logger.warning(f"Provider {provider_name} failed: {result.error}")

        error_result = last_result or GenerationResult(
            provider="none", provider_type=request.provider_type.value,
            status="error", error="No providers available",
            prompt=request.prompt,
        )
        self._record_history(request, plan, error_result)
        return error_result

    async def generate_image(self, prompt: str, **kwargs) -> GenerationResult:
        """Convenience method for image generation."""
        request = GenerationRequest(
            prompt=prompt,
            provider_type=ProviderType.IMAGE,
            **kwargs,
        )
        return await self.generate(request)

    async def generate_video(self, prompt: str, **kwargs) -> GenerationResult:
        """Convenience method for video generation."""
        request = GenerationRequest(
            prompt=prompt,
            provider_type=ProviderType.VIDEO,
            **kwargs,
        )
        return await self.generate(request)

    async def batch_generate(
        self, prompts: List[str], provider_type: ProviderType = ProviderType.IMAGE,
        concurrency: int = 3, **kwargs,
    ) -> List[GenerationResult]:
        """Generate multiple items with controlled concurrency."""
        sem = asyncio.Semaphore(concurrency)

        async def _limited(prompt):
            async with sem:
                request = GenerationRequest(
                    prompt=prompt, provider_type=provider_type, **kwargs,
                )
                return await self.generate(request)

        return await asyncio.gather(*[_limited(p) for p in prompts])

    def _has_required_keys(self, provider: Provider, request: GenerationRequest) -> bool:
        if provider.requires_api_key and not provider.api_key:
            return False
        return True

    async def _execute_generation(
        self, provider: Provider, request: GenerationRequest,
    ) -> GenerationResult:
        """Execute generation on a single provider with timeout."""
        try:
            if isinstance(provider, ImageProvider):
                return await asyncio.wait_for(
                    provider.generate_image(
                        prompt=request.prompt,
                        width=request.width,
                        height=request.height,
                        negative_prompt=request.negative_prompt,
                        seed=request.seed,
                        model=request.model,
                        style=request.style,
                    ),
                    timeout=request.timeout_secs,
                )
            elif isinstance(provider, VideoProvider):
                return await asyncio.wait_for(
                    provider.generate_video(
                        prompt=request.prompt,
                        duration_secs=request.duration_secs,
                        width=request.width,
                        height=request.height,
                        negative_prompt=request.negative_prompt,
                        seed=request.seed,
                        model=request.model,
                    ),
                    timeout=request.timeout_secs,
                )
            else:
                return await asyncio.wait_for(
                    provider.generate(request.prompt),
                    timeout=request.timeout_secs,
                )
        except asyncio.TimeoutError:
            provider.record_error("timeout")
            return GenerationResult(
                provider=provider.name,
                provider_type=provider.provider_type.value,
                status="timeout",
                error=f"Timeout after {request.timeout_secs}s",
                prompt=request.prompt,
            )

    async def _save_result(self, result: GenerationResult, request: GenerationRequest):
        """Save generation result to disk."""
        if result.output_bytes:
            ext = result.output_format or "png"
            filename = f"{result.request_id}.{ext}"
            filepath = self._output_dir / filename
            filepath.write_bytes(result.output_bytes)
            result.output_path = str(filepath)
            logger.info(f"Saved generation: {filepath}")

    def _record_history(self, request: GenerationRequest, plan: GenerationPlan, result: GenerationResult):
        """Record generation in history for benchmarking."""
        entry = {
            "request_id": result.request_id,
            "prompt": request.prompt[:200],
            "provider_type": request.provider_type.value,
            "final_provider": result.provider,
            "status": result.status,
            "latency_ms": result.latency_ms,
            "cost_estimate": result.cost_estimate,
            "attempts": plan.attempts,
            "created_at": result.created_at,
        }
        self._history.append(entry)
        if len(self._history) > 1000:
            self._history = self._history[-500:]

    def get_stats(self) -> Dict[str, Any]:
        """Get generation statistics."""
        total = len(self._history)
        success = sum(1 for h in self._history if h["status"] == "success")
        by_provider = {}
        for h in self._history:
            p = h["final_provider"]
            if p not in by_provider:
                by_provider[p] = {"success": 0, "total": 0, "avg_latency": 0, "total_latency": 0}
            by_provider[p]["total"] += 1
            by_provider[p]["total_latency"] += h["latency_ms"]
            if h["status"] == "success":
                by_provider[p]["success"] += 1

        for p in by_provider.values():
            p["avg_latency"] = round(p["total_latency"] / max(p["total"], 1), 1)
            p["success_rate"] = round(p["success"] / max(p["total"], 1) * 100, 1)
            del p["total_latency"]

        return {
            "total_generations": total,
            "success_rate": round(success / max(total, 1) * 100, 1),
            "by_provider": by_provider,
            "provider_summary": self._registry.summary(),
        }

    def get_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        return self._history[-limit:]

    def list_providers(self) -> List[Dict[str, Any]]:
        return self._registry.list_providers()
