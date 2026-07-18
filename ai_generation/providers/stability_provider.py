"""
Stability AI — Official API for SDXL, SD3, Stable Video Diffusion.
https://platform.stability.ai
"""
import asyncio
from typing import Optional
import base64
from typing import Optional
import logging
from typing import Optional
import time
from typing import Optional

import httpx
from typing import Optional

from .base import ImageProvider, VideoProvider, GenerationResult, ProviderTier, ProviderCapability

logger = logging.getLogger(__name__)


class StabilityImageProvider(ImageProvider):
    """Stability AI image generation API."""

    name = "stability"
    tier = ProviderTier.PAID
    requires_api_key = True
    cloud_first = True
    base_url = "https://api.stability.ai/v2beta"
    supported_models = [
        "stable-diffusion-xl-1024-v1-0",
        "sd3-medium",
        "sd3-large",
        "sd3.5-large",
    ]
    default_model = "sd3-medium"

    capabilities = [
        ProviderCapability(
            name="text_to_image",
            description="Generate images via Stability AI",
            input_types=["text"],
            output_types=["image/png", "image/webp"],
            max_resolution="2048x2048",
            supports_negative_prompt=True,
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
                request_id=request_id, error="No STABILITY_API_KEY set",
                latency_ms=0, prompt=prompt,
            )

        if not model:
            model = self.default_model

        url = f"{self.base_url}/stable-image/generate/sd3"
        data = {
            "prompt": prompt,
            "model": model,
            "output_format": "png",
            "aspect_ratio": f"{width}:{height}",
        }
        if negative_prompt:
            data["negative_prompt"] = negative_prompt
        if seed is not None:
            data["seed"] = seed

        try:
            async with httpx.AsyncClient(timeout=120) as client:
                response = await client.post(
                    url,
                    data=data,
                    headers={"Authorization": f"Bearer {api_key}", "Accept": "image/*"},
                )
                latency_ms = round((time.time() - start) * 1000, 1)

                if response.status_code == 200:
                    self.record_success(latency_ms)
                    return GenerationResult(
                        provider=self.name, provider_type="image",
                        status="success", request_id=request_id,
                        output_bytes=response.content, output_format="png",
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


