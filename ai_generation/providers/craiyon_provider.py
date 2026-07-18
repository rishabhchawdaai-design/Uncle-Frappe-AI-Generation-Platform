"""
Craiyon (DALL-E Mini) — Free image generation, no API key required.
https://www.craiyon.com
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


class CraiyonProvider(ImageProvider):
    """Craiyon — free, community-powered image generation."""

    name = "craiyon"
    tier = ProviderTier.FREE
    requires_api_key = False
    cloud_first = True
    base_url = "https://api.craiyon.com/v3"
    supported_models = ["craiyon-v3"]
    default_model = "craiyon-v3"

    capabilities = [
        ProviderCapability(
            name="text_to_image",
            description="Free image generation via Craiyon",
            input_types=["text"],
            output_types=["image/webp"],
            max_resolution="512x512",
            supports_negative_prompt=False,
            supports_seed=False,
        ),
    ]

    async def generate_image(
        self, prompt, width=512, height=512, negative_prompt="",
        seed=None, model="", style="", **kwargs
    ) -> GenerationResult:
        request_id = self._make_request_id()
        start = time.time()

        payload = {
            "prompt": prompt,
            "version": "craiyon",
            "token": None,
        }

        try:
            async with httpx.AsyncClient(timeout=180) as client:
                response = await client.post(
                    self.base_url, json=payload,
                    headers={"Content-Type": "application/json"},
                )
                latency_ms = round((time.time() - start) * 1000, 1)

                if response.status_code == 200:
                    data = response.json()
                    images = data.get("images", [])
                    output_bytes = b""
                    if images:
                        output_bytes = base64.b64decode(images[0])

                    self.record_success(latency_ms)
                    return GenerationResult(
                        provider=self.name, provider_type="image",
                        status="success", request_id=request_id,
                        output_bytes=output_bytes, output_format="webp",
                        width=512, height=512, latency_ms=latency_ms,
                        prompt=prompt, seed=seed, metadata={"model": "craiyon"},
                    )
                else:
                    error = f"HTTP {response.status_code}"
                    self.record_error(error)
                    return GenerationResult(
                        provider=self.name, provider_type="image", status="error",
                        request_id=request_id, error=error,
                        latency_ms=latency_ms, prompt=prompt,
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


