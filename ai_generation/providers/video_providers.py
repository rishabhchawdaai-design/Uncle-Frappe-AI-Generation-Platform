"""
Video generation providers — framework for true AI video.
Supports Replicate (Stable Video Diffusion), Runway (if key available),
and community/free options.
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

from .base import VideoProvider, GenerationResult, ProviderTier, ProviderCapability

logger = logging.getLogger(__name__)


class ReplicateVideoProvider(VideoProvider):
    """Replicate video generation — SVD, AnimateDiff, etc."""

    name = "replicate_video"
    tier = ProviderTier.COMMUNITY
    requires_api_key = True
    cloud_first = True
    base_url = "https://api.replicate.com/v1/predictions"
    supported_models = [
        "stability-ai/stable-video-diffusion",
        "guoyww/animatediff",
        "lucataco/animate-diff-v2-1",
        "minimax/video-01",
    ]
    default_model = "stability-ai/stable-video-diffusion"

    capabilities = [
        ProviderCapability(
            name="text_to_video",
            description="Generate videos via Replicate models",
            input_types=["text", "image"],
            output_types=["video/mp4", "video/webm"],
            max_duration_secs=6.0,
            supports_seed=True,
        ),
    ]

    async def generate_video(
        self, prompt, duration_secs=4.0, width=1024, height=576,
        fps=24, negative_prompt="", seed=None, model="", **kwargs
    ) -> GenerationResult:
        request_id = self._make_request_id()
        start = time.time()
        api_key = self.api_key

        if not api_key:
            return GenerationResult(
                provider=self.name, provider_type="video", status="error",
                request_id=request_id, error="No REPLICATE_API_TOKEN set",
                latency_ms=0, prompt=prompt,
            )

        if not model:
            model = self.default_model

        input_data = {
            "prompt": prompt,
            "num_frames": int(duration_secs * fps),
            "fps": fps,
        }
        if negative_prompt:
            input_data["negative_prompt"] = negative_prompt
        if seed is not None:
            input_data["seed"] = seed

        try:
            async with httpx.AsyncClient(timeout=300) as client:
                response = await client.post(
                    self.base_url,
                    json={"version": model, "input": input_data},
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
                        output_url = output if isinstance(output, str) else (output[0] if output else "")
                        self.record_success(latency_ms)
                        return GenerationResult(
                            provider=self.name, provider_type="video",
                            status="success", request_id=request_id,
                            output_url=output_url, output_format="mp4",
                            width=width, height=height,
                            duration_secs=duration_secs,
                            latency_ms=latency_ms, prompt=prompt, seed=seed,
                            metadata={"model": model, "prediction_id": prediction_id},
                        )

                    if data.get("status") in ("starting", "processing"):
                        return await self._poll(client, api_key, prediction_id, request_id, start, prompt, seed, width, height, duration_secs, model)

                    error = f"Prediction failed: {data.get('error', 'unknown')}"
                    self.record_error(error)
                    return GenerationResult(
                        provider=self.name, provider_type="video", status="error",
                        request_id=request_id, error=error,
                        latency_ms=latency_ms, prompt=prompt,
                    )
                else:
                    error = f"HTTP {response.status_code}"
                    self.record_error(error)
                    return GenerationResult(
                        provider=self.name, provider_type="video", status="error",
                        request_id=request_id, error=error,
                        latency_ms=latency_ms, prompt=prompt,
                    )
        except Exception as e:
            latency_ms = round((time.time() - start) * 1000, 1)
            self.record_error(str(e))
            return GenerationResult(
                provider=self.name, provider_type="video", status="error",
                request_id=request_id, error=str(e)[:200],
                latency_ms=latency_ms, prompt=prompt,
            )

    async def _poll(self, client, api_key, prediction_id, request_id, start, prompt, seed, width, height, duration_secs, model):
        poll_url = f"{self.base_url}/{prediction_id}"
        headers = {"Authorization": f"Bearer {api_key}"}

        for _ in range(120):
            await asyncio.sleep(3)
            try:
                r = await client.get(poll_url, headers=headers)
                if r.status_code == 200:
                    data = r.json()
                    if data.get("status") == "succeeded":
                        output = data.get("output", [])
                        output_url = output if isinstance(output, str) else (output[0] if output else "")
                        latency_ms = round((time.time() - start) * 1000, 1)
                        self.record_success(latency_ms)
                        return GenerationResult(
                            provider=self.name, provider_type="video",
                            status="success", request_id=request_id,
                            output_url=output_url, output_format="mp4",
                            width=width, height=height, duration_secs=duration_secs,
                            latency_ms=latency_ms, prompt=prompt, seed=seed,
                            metadata={"model": model, "prediction_id": prediction_id},
                        )
                    elif data.get("status") == "failed":
                        latency_ms = round((time.time() - start) * 1000, 1)
                        error = data.get("error", "Prediction failed")
                        self.record_error(error)
                        return GenerationResult(
                            provider=self.name, provider_type="video", status="error",
                            request_id=request_id, error=error,
                            latency_ms=latency_ms, prompt=prompt,
                        )
            except Exception:
                pass

        latency_ms = round((time.time() - start) * 1000, 1)
        self.record_error("poll timeout")
        return GenerationResult(
            provider=self.name, provider_type="video", status="timeout",
            request_id=request_id, error="Video generation polling timed out",
            latency_ms=latency_ms, prompt=prompt,
        )


