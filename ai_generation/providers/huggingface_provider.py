"""
Hugging Face Inference API — Free tier for many image/video models.
https://huggingface.co/inference-api
"""
import asyncio
from typing import Optional
import hashlib
from typing import Optional
import logging
from typing import Optional
import time
from typing import Optional

import httpx
from typing import Optional

from .base import ImageProvider, GenerationResult, ProviderTier, ProviderCapability

logger = logging.getLogger(__name__)


class HuggingFaceProvider(ImageProvider):
    """Hugging Face Inference API — free tier with generous limits."""

    name = "huggingface"
    tier = ProviderTier.FREE
    requires_api_key = True
    cloud_first = True
    base_url = "https://api-inference.huggingface.co/models"
    supported_models = [
        "stabilityai/stable-diffusion-xl-base-1.0",
        "stabilityai/stable-diffusion-2-1",
        "runwayml/stable-diffusion-v1-5",
        "CompVis/stable-diffusion-v1-4",
        "prompthero/openjourney-v4",
        "ByteDance/Hyper-SDXL-1Step-T2I",
        "Kwai-Kolors/Kolors-Virtual-Try-On",
    ]
    default_model = "stabilityai/stable-diffusion-xl-base-1.0"

    capabilities = [
        ProviderCapability(
            name="text_to_image",
            description="Generate images from text via HF Inference",
            input_types=["text"],
            output_types=["image/png"],
            max_resolution="1024x1024",
            supports_negative_prompt=True,
            supports_seed=True,
        ),
    ]

    def __init__(self, config=None):
        super().__init__(config)

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

        api_key = self.api_key
        if not api_key:
            latency_ms = round((time.time() - start) * 1000, 1)
            return GenerationResult(
                provider=self.name, provider_type="image", status="error",
                request_id=request_id, error="No HUGGINGFACE_API_KEY set",
                latency_ms=latency_ms, prompt=prompt,
            )

        if not model:
            model = self.default_model

        url = f"{self.base_url}/{model}"

        payload = {
            "inputs": prompt,
            "parameters": {
                "width": min(width, 1024),
                "height": min(height, 1024),
                "num_inference_steps": kwargs.get("steps", 30),
                "guidance_scale": kwargs.get("guidance_scale", 7.5),
            },
        }
        if negative_prompt:
            payload["parameters"]["negative_prompt"] = negative_prompt
        if seed is not None:
            payload["parameters"]["seed"] = seed

        headers = {"Authorization": f"Bearer {api_key}"}

        try:
            async with httpx.AsyncClient(timeout=120) as client:
                response = await client.post(url, json=payload, headers=headers)
                latency_ms = round((time.time() - start) * 1000, 1)

                if response.status_code == 200:
                    content_type = response.headers.get("content-type", "")
                    if "image" in content_type:
                        self.record_success(latency_ms)
                        return GenerationResult(
                            provider=self.name, provider_type="image",
                            status="success", request_id=request_id,
                            output_bytes=response.content, output_format="png",
                            width=width, height=height, latency_ms=latency_ms,
                            prompt=prompt, seed=seed, cost_estimate=0.0,
                            metadata={"model": model, "content_type": content_type},
                        )
                    else:
                        error = f"Unexpected content type: {content_type}"
                        self.record_error(error)
                        return GenerationResult(
                            provider=self.name, provider_type="image",
                            status="error", request_id=request_id,
                            error=error, latency_ms=latency_ms, prompt=prompt,
                        )
                elif response.status_code == 503:
                    error = "Model is loading, please retry"
                    self.record_error(error, is_rate_limit=True)
                    return GenerationResult(
                        provider=self.name, provider_type="image",
                        status="rate_limited", request_id=request_id,
                        error=error, latency_ms=latency_ms, prompt=prompt,
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


