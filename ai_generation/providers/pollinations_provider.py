"""
Pollinations.ai — Free image generation, no API key required.
https://pollinations.ai
"""
import asyncio
from typing import Optional
import hashlib
from typing import Optional
import logging
from typing import Optional
import time
from typing import Optional
import urllib.parse
from typing import Optional

import httpx
from typing import Optional

from .base import ImageProvider, GenerationResult, ProviderTier, ProviderCapability

logger = logging.getLogger(__name__)


class PollinationsProvider(ImageProvider):
    """Free AI image generation via Pollinations.ai API."""

    name = "pollinations"
    tier = ProviderTier.FREE
    requires_api_key = False
    cloud_first = True
    base_url = "https://image.pollinations.ai/prompt"
    supported_models = ["flux", "flux-realism", "flux-anime", "flux-3d", "turbo"]
    default_model = "flux"

    capabilities = [
        ProviderCapability(
            name="text_to_image",
            description="Generate images from text prompts",
            input_types=["text"],
            output_types=["image/png", "image/jpeg"],
            max_resolution="2048x2048",
            supports_negative_prompt=True,
            supports_seed=True,
            supports_style=False,
        ),
    ]

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
        request_id = self._make_request_id()
        start = time.time()

        if not model:
            model = self.default_model

        full_prompt = prompt
        if negative_prompt:
            full_prompt = f"{prompt}. Avoid: {negative_prompt}"

        encoded_prompt = urllib.parse.quote(full_prompt)
        params = {
            "width": str(width),
            "height": str(height),
            "model": model,
            "nologo": "true",
            "enhance": "true",
        }
        if seed is not None:
            params["seed"] = str(seed)

        query_string = "&".join(f"{k}={v}" for k, v in params.items())
        url = f"{self.base_url}/{encoded_prompt}?{query_string}"

        try:
            async with httpx.AsyncClient(timeout=120, follow_redirects=True) as client:
                response = await client.get(url, headers={"Accept": "image/*"})
                latency_ms = round((time.time() - start) * 1000, 1)

                if response.status_code == 200:
                    content_type = response.headers.get("content-type", "image/png")
                    ext = "png" if "png" in content_type else "jpg" if "jpeg" in content_type else "webp"
                    output_bytes = response.content

                    self.record_success(latency_ms)

                    return GenerationResult(
                        provider=self.name,
                        provider_type="image",
                        status="success",
                        request_id=request_id,
                        output_bytes=output_bytes,
                        output_format=ext,
                        width=width,
                        height=height,
                        latency_ms=latency_ms,
                        prompt=prompt,
                        seed=seed,
                        cost_estimate=0.0,
                        metadata={
                            "model": model,
                            "content_type": content_type,
                            "content_length": len(output_bytes),
                        },
                    )
                else:
                    error = f"HTTP {response.status_code}"
                    self.record_error(error)
                    return GenerationResult(
                        provider=self.name,
                        provider_type="image",
                        status="error",
                        request_id=request_id,
                        error=error,
                        latency_ms=latency_ms,
                        prompt=prompt,
                    )

        except httpx.TimeoutException:
            latency_ms = round((time.time() - start) * 1000, 1)
            self.record_error("timeout")
            return GenerationResult(
                provider=self.name, provider_type="image", status="timeout",
                request_id=request_id, error="Request timed out",
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


