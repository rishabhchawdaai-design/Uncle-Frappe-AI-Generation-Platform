"""
Kimi K3 Text Provider — Kimi K3 as a text/chat generation provider.

Exposes Moonshot AI's Kimi K3 through the unified provider registry and
Generation Manager. Execution always delegates to the canonical
``ai_generation.kimi_k3.KimiK3Manager`` so every request flows through the
same runtime selection, negotiation, observability, and fallback paths used
by the rest of the platform.
"""
import logging
import os
from typing import Any, Dict, Optional

from .base import GenerationResult, ProviderTier, TextProvider

logger = logging.getLogger(__name__)


class KimiK3TextProvider(TextProvider):
    """Text/chat generation via Moonshot AI Kimi K3 (cloud + self-hosted)."""

    name = "kimi_k3"
    provider_type = TextProvider.provider_type
    tier = ProviderTier.COMMUNITY
    requires_api_key = True
    cloud_first = True
    supported_models = ["kimi-k3"]
    default_model = "kimi-k3"
    base_url = "https://api.moonshot.ai/v1"

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self._manager = None

    @property
    def api_key(self) -> str:
        """Official Moonshot AI cloud API key."""
        return (self.config.get("api_key")
                or os.environ.get("MOONSHOT_API_KEY", "")
                or os.environ.get("KIMI_K3_API_KEY", ""))

    @property
    def manager(self):
        """Lazy Kimi K3 manager (cloud API + self-hosted vLLM/SGLang)."""
        if self._manager is None:
            from ..kimi_k3 import KimiK3Manager
            self._manager = KimiK3Manager(self.config)
        return self._manager

    async def generate_text(
        self,
        prompt: str,
        system_prompt: str = "",
        model: str = "",
        **kwargs,
    ) -> GenerationResult:
        provider = kwargs.pop("provider", "auto")
        reasoning_effort = kwargs.pop("reasoning_effort", "max")
        request_id = self._make_request_id()
        try:
            result = await self.manager.chat(
                prompt,
                provider=provider,
                system_prompt=system_prompt,
                reasoning_effort=reasoning_effort,
                images=kwargs.pop("images", None),
                history=kwargs.pop("history", None),
                max_tokens=kwargs.pop("max_tokens", None),
                temperature=kwargs.pop("temperature", None),
                top_p=kwargs.pop("top_p", None),
                timeout_secs=kwargs.pop("timeout_secs", 120.0),
            )
        except Exception as e:  # defensive: manager raises only KimiK3Error
            self.record_error(str(e)[:300])
            return GenerationResult(
                provider=self.name,
                provider_type=self.provider_type.value,
                status="error",
                error=str(e)[:300],
                prompt=prompt,
                request_id=request_id,
            )
        if result.error is not None:
            self.record_error(result.error)
            return GenerationResult(
                provider=result.provider,
                provider_type=self.provider_type.value,
                status="error",
                error=result.error,
                prompt=prompt,
                request_id=request_id,
            )
        self.record_success(result.latency_ms)
        return GenerationResult(
            provider=result.provider,
            provider_type=self.provider_type.value,
            status="success",
            request_id=request_id,
            output_format="text",
            latency_ms=result.latency_ms,
            prompt=prompt,
            metadata={
                "text": result.text,
                "reasoning": result.reasoning or "",
                "model": result.model or "kimi-k3",
                "usage": result.usage or {},
                "quality_score": result.quality_score,
                "fallbacks": result.fallbacks or [],
            },
        )

    async def health_check(self) -> Dict[str, Any]:
        try:
            health = await self.manager.health()
        except Exception as e:
            return {"provider": self.name, "available": False, "error": str(e)[:200]}
        cloud = health.get("kimi_k3_cloud", {})
        return {
            "provider": self.name,
            "status": "available" if cloud.get("healthy") else self._status.value,
            "available": bool(cloud.get("healthy")),
            "endpoints": {name: h.get("healthy") for name, h in health.items()},
        }
