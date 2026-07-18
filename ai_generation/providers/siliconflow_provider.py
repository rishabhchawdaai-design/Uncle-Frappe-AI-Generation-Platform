"""
SiliconFlow — Free Flux & other models, generous free tier.
https://siliconflow.cn
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

from .base import ImageProvider, GenerationResult, ProviderTier, ProviderCapability

logger = logging.getLogger(__name__)


class SiliconFlowProvider(ImageProvider):
    """SiliconFlow — free tier for Flux and other image models."""

    name = "siliconflow"
    tier = ProviderTier.FREE
    requires_api_key = True
    cloud_first = True
    base_url = "https://api.siliconflow.cn/v1/images/generations"
    supported_models = [
        "stabilityai/stable-diffusion-3-5-large",
        "black-forest-labs/FLUX.1-schnell",
        "black-forest-labs/FLUX.1-dev",
        "Pro/black-forest-labs/FLUX.1-schnell",
    ]
    default_model = "black-forest-labs/FLUX.1-schnell"

    capabilities = [
        ProviderCapability(
            name="text_to_image",
            description="Generate images via SiliconFlow",
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
                request_id=request_id, error="No SILICONFLOW_API_KEY set",
                latency_ms=0, prompt=prompt,
            )

        if not model:
            model = self.default_model

        payload = {
            "model": model,
            "prompt": prompt,
            "image_size": f"{min(width, 1024)}x{min(height, 1024)}",
            "batch_size": 1,
        }
        if negative_prompt:
            payload["negative_prompt"] = negative_prompt
        if seed is not None:
            payload["seed"] = seed

        try:
            async with httpx.AsyncClient(timeout=120) as client:
                response = await client.post(
                    self.base_url, json=payload,
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                )
                latency_ms = round((time.time() - start) * 1000, 1)

                if response.status_code == 200:
                    data = response.json()
                    images = data.get("images", [])
                    output_url = images[0].get("url", "") if images else ""
                    self.record_success(latency_ms)
                    return GenerationResult(
                        provider=self.name, provider_type="image",
                        status="success", request_id=request_id,
                        output_url=output_url, output_format="png",
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


