"""
Together AI — Flux & other models, has free tier credits.
https://together.ai
"""
import asyncio
from typing import Optional
import logging
from typing import Optional
import time
from typing import Optional

import httpx
from typing import Optional

from .base import ImageProvider, GenerationResult, ProviderTier, ProviderCapability

logger = logging.getLogger(__name__)


class TogetherProvider(ImageProvider):
    """Together AI image generation with Flux and other models."""

    name = "together"
    tier = ProviderTier.FREE
    requires_api_key = True
    cloud_first = True
    base_url = "https://api.together.xyz/v1/images/generations"
    supported_models = [
        "black-forest-labs/FLUX.1-schnell-Free",
        "black-forest-labs/FLUX.1-dev",
        "stabilityai/stable-diffusion-xl-base-1.0",
        "stabilityai/stable-diffusion-3-medium",
        "Prompthero/stable-diffusion-v1-4",
    ]
    default_model = "black-forest-labs/FLUX.1-schnell-Free"

    capabilities = [
        ProviderCapability(
            name="text_to_image",
            description="Generate images via Together AI",
            input_types=["text"],
            output_types=["image/png", "image/webp"],
            max_resolution="2048x2048",
            supports_negative_prompt=False,
            supports_seed=True,
        ),
    ]

    async def generate_image(
        self, prompt, width=1024, height=1024, negative_prompt="",
        seed=None, model="", style="", **kwargs
    ) -> GenerationResult:
        request_id = self._make_request_id()
        start = time.time()
        api_key = self.api_key

        if not api_key:
            return GenerationResult(
                provider=self.name, provider_type="image", status="error",
                request_id=request_id, error="No TOGETHER_API_KEY set",
                latency_ms=0, prompt=prompt,
            )

        if not model:
            model = self.default_model

        payload = {
            "model": model,
            "prompt": prompt,
            "width": min(width, 1024),
            "height": min(height, 1024),
            "steps": kwargs.get("steps", 4),
            "n": 1,
            "response_format": "b64_json",
        }
        if seed is not None:
            payload["seed"] = seed

        try:
            async with httpx.AsyncClient(timeout=120) as client:
                response = await client.post(
                    self.base_url, json=payload,
                    headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                )
                latency_ms = round((time.time() - start) * 1000, 1)

                if response.status_code == 200:
                    data = response.json()
                    b64 = data["data"][0].get("b64_json", "")
                    import base64
                    output_bytes = base64.b64decode(b64) if b64 else b""
                    self.record_success(latency_ms)
                    return GenerationResult(
                        provider=self.name, provider_type="image",
                        status="success", request_id=request_id,
                        output_bytes=output_bytes, output_format="png",
                        width=width, height=height, latency_ms=latency_ms,
                        prompt=prompt, seed=seed, metadata={"model": model},
                    )
                else:
                    error = f"HTTP {response.status_code}: {response.text[:200]}"
                    is_rl = response.status_code == 429
                    self.record_error(error, is_rate_limit=is_rl)
                    return GenerationResult(
                        provider=self.name, provider_type="image",
                        status="rate_limited" if is_rl else "error",
                        request_id=request_id, error=error,
                        latency_ms=latency_ms, prompt=prompt,
                    )
        except Exception as e:
            latency_ms = round((time.time() - start) * 1000, 1)
            self.record_error(str(e))
            return GenerationResult(
                provider=self.name, provider_type="image", status="error",
                request_id=request_id, error=str(e)[:200],
                latency_ms=latency_ms, prompt=prompt,
            )


