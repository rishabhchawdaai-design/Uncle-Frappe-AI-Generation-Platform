"""
Replicate — Community models, many free/affordable options.
https://replicate.com
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


class ReplicateImageProvider(ImageProvider):
    """Replicate image generation — wide model selection."""

    name = "replicate"
    tier = ProviderTier.COMMUNITY
    requires_api_key = True
    cloud_first = True
    base_url = "https://api.replicate.com/v1/predictions"
    supported_models = [
        "black-forest-labs/flux-schnell",
        "black-forest-labs/flux-dev",
        "stability-ai/sdxl",
        "adirik/ambient-diffusion",
        "tencentarc/photomaker",
    ]
    default_model = "black-forest-labs/flux-schnell"

    capabilities = [
        ProviderCapability(
            name="text_to_image",
            description="Generate images via Replicate models",
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
                request_id=request_id, error="No REPLICATE_API_TOKEN set",
                latency_ms=0, prompt=prompt,
            )

        if not model:
            model = self.default_model

        payload = {
            "version": model,
            "input": {
                "prompt": prompt,
                "width": min(width, 1024),
                "height": min(height, 1024),
                "num_outputs": 1,
            },
        }
        if negative_prompt:
            payload["input"]["negative_prompt"] = negative_prompt
        if seed is not None:
            payload["input"]["seed"] = seed

        try:
            async with httpx.AsyncClient(timeout=180) as client:
                response = await client.post(
                    self.base_url, json=payload,
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                )
                latency_ms = round((time.time() - start) * 1000, 1)

                if response.status_code in (200, 201):
                    data = response.json()
                    prediction_id = data.get("id", "")

                    if data.get("status") == "succeeded":
                        output = data.get("output", [])
                        output_url = output[0] if output else ""
                        self.record_success(latency_ms)
                        return GenerationResult(
                            provider=self.name, provider_type="image",
                            status="success", request_id=request_id,
                            output_url=output_url, output_format="png",
                            width=width, height=height, latency_ms=latency_ms,
                            prompt=prompt, seed=seed,
                            metadata={"model": model, "prediction_id": prediction_id},
                        )

                    if data.get("status") == "processing":
                        return await self._poll_prediction(client, api_key, prediction_id, request_id, start, prompt, seed, width, height, model)

                    error = f"Prediction failed: {data.get('error', 'unknown')}"
                    self.record_error(error)
                    return GenerationResult(
                        provider=self.name, provider_type="image", status="error",
                        request_id=request_id, error=error,
                        latency_ms=latency_ms, prompt=prompt,
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

    async def _poll_prediction(self, client, api_key, prediction_id, request_id, start, prompt, seed, width, height, model):
        """Poll for prediction completion."""
        poll_url = f"{self.base_url}/{prediction_id}"
        headers = {"Authorization": f"Bearer {api_key}"}

        for _ in range(60):
            await asyncio.sleep(2)
            try:
                r = await client.get(poll_url, headers=headers)
                if r.status_code == 200:
                    data = r.json()
                    status = data.get("status", "")
                    if status == "succeeded":
                        output = data.get("output", [])
                        output_url = output[0] if output else ""
                        latency_ms = round((time.time() - start) * 1000, 1)
                        self.record_success(latency_ms)
                        return GenerationResult(
                            provider=self.name, provider_type="image",
                            status="success", request_id=request_id,
                            output_url=output_url, output_format="png",
                            width=width, height=height, latency_ms=latency_ms,
                            prompt=prompt, seed=seed,
                            metadata={"model": model, "prediction_id": prediction_id},
                        )
                    elif status == "failed":
                        latency_ms = round((time.time() - start) * 1000, 1)
                        error = data.get("error", "Prediction failed")
                        self.record_error(error)
                        return GenerationResult(
                            provider=self.name, provider_type="image", status="error",
                            request_id=request_id, error=error,
                            latency_ms=latency_ms, prompt=prompt,
                        )
            except Exception:
                pass

        latency_ms = round((time.time() - start) * 1000, 1)
        self.record_error("poll timeout")
        return GenerationResult(
            provider=self.name, provider_type="image", status="timeout",
            request_id=request_id, error="Prediction polling timed out",
            latency_ms=latency_ms, prompt=prompt,
        )


