"""
Pollinations Text Provider — free anonymous text/chat generation.

Official API: https://text.pollinations.ai/{prompt} (GET, no API key).
Documentation: https://pollinations.ai / https://github.com/pollinations/pollinations

Live-verified 2026-08-01: anonymous GET requests return plain text (200).
The OpenAI-compatible POST endpoint is deprecated for anonymous users
(HTTP 402 with migration notice to https://enter.pollinations.ai), so this
provider uses the officially documented anonymous GET path only.
"""
import asyncio
import logging
import time
from typing import Any, Dict, Optional
import urllib.parse

import httpx

from .base import GenerationResult, ProviderCapability, ProviderTier, TextProvider

logger = logging.getLogger(__name__)


class PollinationsTextProvider(TextProvider):
    """Free anonymous text generation via Pollinations.ai."""

    name = "pollinations_text"
    provider_type = TextProvider.provider_type
    tier = ProviderTier.FREE
    requires_api_key = False
    cloud_first = True
    base_url = "https://text.pollinations.ai"
    # Models advertised on the anonymous tier per official docs + /models endpoint.
    supported_models = ["openai-fast", "openai", "mistral", "searchgpt"]
    default_model = "openai"

    capabilities = [
        ProviderCapability(
            name="chat",
            description="Free anonymous text generation via Pollinations.ai",
            input_types=["text"],
            output_types=["text/plain"],
            supports_seed=True,
        ),
    ]

    async def generate_text(
        self,
        prompt: str,
        system_prompt: str = "",
        model: str = "",
        **kwargs,
    ) -> GenerationResult:
        request_id = self._make_request_id()
        start = time.time()

        if not model:
            model = self.default_model

        encoded_prompt = urllib.parse.quote(prompt)
        params: Dict[str, Any] = {"model": model}
        if kwargs.get("temperature") is not None:
            params["temperature"] = str(kwargs["temperature"])
        if kwargs.get("seed") is not None:
            params["seed"] = str(kwargs["seed"])
        if system_prompt:
            params["system"] = system_prompt

        url = f"{self.base_url}/{encoded_prompt}"
        timeout_secs = float(kwargs.get("timeout_secs", 60.0))
        retries = max(0, int(kwargs.get("retries", 1)))

        # Retryable statuses: 402/429 = anonymous quota exhausted, 5xx = transient.
        retryable = {402, 429, 500, 502, 503, 504}
        last_error: Optional[str] = None

        for attempt in range(retries + 1):
            try:
                async with httpx.AsyncClient(timeout=timeout_secs, follow_redirects=True) as client:
                    response = await client.get(url, params=params)
                    latency_ms = round((time.time() - start) * 1000, 1)

                    if response.status_code == 200:
                        text = response.text.strip()
                        if not text:
                            self.record_error("empty response")
                            return GenerationResult(
                                provider=self.name,
                                provider_type=self.provider_type.value,
                                status="error",
                                request_id=request_id,
                                error="Empty response from Pollinations text API",
                                latency_ms=latency_ms,
                                prompt=prompt,
                            )
                        self.record_success(latency_ms)
                        return GenerationResult(
                            provider=self.name,
                            provider_type=self.provider_type.value,
                            status="success",
                            request_id=request_id,
                            output_format="text",
                            latency_ms=latency_ms,
                            prompt=prompt,
                            cost_estimate=0.0,
                            metadata={
                                "text": text,
                                "model": model,
                                "content_type": response.headers.get("content-type", "text/plain"),
                            },
                        )

                    error = f"HTTP {response.status_code}: {response.text[:200]}"
                    if response.status_code in retryable and attempt < retries:
                        last_error = error
                        self.record_error(error, is_rate_limit=response.status_code == 429)
                        await asyncio.sleep(3.0 + attempt * 2.0)
                        continue
                    self.record_error(error, is_rate_limit=response.status_code == 429)
                    return GenerationResult(
                        provider=self.name,
                        provider_type=self.provider_type.value,
                        status="rate_limited" if response.status_code == 429 else "error",
                        request_id=request_id,
                        error=error,
                        latency_ms=latency_ms,
                        prompt=prompt,
                    )
            except httpx.TimeoutException:
                latency_ms = round((time.time() - start) * 1000, 1)
                last_error = f"Pollinations text API timed out after {timeout_secs}s"
                self.record_error("timeout")
                if attempt < retries:
                    await asyncio.sleep(3.0 + attempt * 2.0)
                    continue
                return GenerationResult(
                    provider=self.name,
                    provider_type=self.provider_type.value,
                    status="timeout",
                    request_id=request_id,
                    error=last_error,
                    latency_ms=latency_ms,
                    prompt=prompt,
                )
            except httpx.HTTPError as e:
                latency_ms = round((time.time() - start) * 1000, 1)
                last_error = str(e)[:200]
                self.record_error(last_error)
                if attempt < retries:
                    await asyncio.sleep(3.0 + attempt * 2.0)
                    continue
                return GenerationResult(
                    provider=self.name,
                    provider_type=self.provider_type.value,
                    status="error",
                    request_id=request_id,
                    error=last_error,
                    latency_ms=latency_ms,
                    prompt=prompt,
                )

        latency_ms = round((time.time() - start) * 1000, 1)
        self.record_error(last_error or "unknown error")
        return GenerationResult(
            provider=self.name,
            provider_type=self.provider_type.value,
            status="error",
            request_id=request_id,
            error=last_error or "unknown error",
            latency_ms=latency_ms,
            prompt=prompt,
        )
