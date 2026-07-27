"""
Audio Providers — TTS and STT implementations.

Providers:
- PiperTTS: CPU-based TTS server (MIT, 30+ languages)
- KokoroTTS: High-quality TTS server (Apache 2.0)
- OpenAITTS: Cloud TTS API (paid, highest quality)
- WhisperSTT: Speech-to-text server (MIT, 99 languages)
"""
import asyncio
import base64
import hashlib
import logging
import os
import time
from typing import Optional

import httpx

from .base import (
    AudioProvider, STTProvider, GenerationResult,
    ProviderTier, ProviderCapability,
)

logger = logging.getLogger(__name__)


class PiperTTSProvider(AudioProvider):
    """Piper TTS — fast CPU-based text-to-speech server.
    Requires a running Piper HTTP server (e.g., docker run rhasspy/piper).
    https://github.com/rhasspy/piper
    """

    name = "piper_tts"
    tier = ProviderTier.FREE
    requires_api_key = False
    cloud_first = False
    base_url = "http://localhost:11000"
    supported_models = ["en_US-lessac-medium", "en_US-amy-medium", "en_GB-alba-medium"]
    default_model = "en_US-lessac-medium"

    capabilities = [
        ProviderCapability(
            name="text_to_speech",
            description="Generate speech from text via Piper TTS",
            input_types=["text"],
            output_types=["audio/wav"],
            supports_seed=False,
        ),
    ]

    async def generate_audio(
        self,
        text: str,
        voice: str = "default",
        speed: float = 1.0,
        output_format: str = "wav",
        **kwargs,
    ) -> GenerationResult:
        request_id = self._make_request_id()
        start = time.time()

        model = kwargs.get("model", self.default_model)
        url = f"{self.base_url}/api/tts"

        payload = {
            "text": text,
            "voice": model,
            "speed": speed,
        }

        try:
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(url, json=payload)
                latency_ms = round((time.time() - start) * 1000, 1)

                if response.status_code == 200:
                    self.record_success(latency_ms)
                    return GenerationResult(
                        provider=self.name,
                        provider_type="audio",
                        status="success",
                        request_id=request_id,
                        output_bytes=response.content,
                        output_format="wav",
                        latency_ms=latency_ms,
                        prompt=text,
                        cost_estimate=0.0,
                        metadata={"model": model, "voice": voice, "speed": speed},
                    )
                else:
                    error = f"HTTP {response.status_code}: {response.text[:200]}"
                    self.record_error(error)
                    return GenerationResult(
                        provider=self.name, provider_type="audio", status="error",
                        request_id=request_id, error=error, latency_ms=latency_ms,
                        prompt=text,
                    )
        except httpx.ConnectError:
            latency_ms = round((time.time() - start) * 1000, 1)
            error = "Piper TTS server not running. Start with: docker run -p 11000:11000 rhasspy/piper"
            self.record_error(error)
            return GenerationResult(
                provider=self.name, provider_type="audio", status="error",
                request_id=request_id, error=error, latency_ms=latency_ms,
                prompt=text,
            )
        except Exception as e:
            latency_ms = round((time.time() - start) * 1000, 1)
            self.record_error(str(e))
            return GenerationResult(
                provider=self.name, provider_type="audio", status="error",
                request_id=request_id, error=str(e)[:200], latency_ms=latency_ms,
                prompt=text,
            )


class KokoroTTSProvider(AudioProvider):
    """Kokoro TTS — high-quality text-to-speech.
    Apache 2.0 license, excellent quality, fast inference.
    https://github.com/hexgrad/kokoro
    """

    name = "kokoro_tts"
    tier = ProviderTier.FREE
    requires_api_key = False
    cloud_first = False
    base_url = "http://localhost:8880"
    supported_models = ["kokoro-v1"]
    default_model = "kokoro-v1"

    capabilities = [
        ProviderCapability(
            name="text_to_speech",
            description="Generate high-quality speech from text",
            input_types=["text"],
            output_types=["audio/wav"],
            supports_seed=False,
        ),
    ]

    async def generate_audio(
        self,
        text: str,
        voice: str = "af_heart",
        speed: float = 1.0,
        output_format: str = "wav",
        **kwargs,
    ) -> GenerationResult:
        request_id = self._make_request_id()
        start = time.time()

        url = f"{self.base_url}/v1/tts"

        payload = {
            "text": text,
            "voice": voice,
            "speed": speed,
            "format": output_format,
        }

        try:
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(url, json=payload)
                latency_ms = round((time.time() - start) * 1000, 1)

                if response.status_code == 200:
                    self.record_success(latency_ms)
                    return GenerationResult(
                        provider=self.name,
                        provider_type="audio",
                        status="success",
                        request_id=request_id,
                        output_bytes=response.content,
                        output_format=output_format,
                        latency_ms=latency_ms,
                        prompt=text,
                        cost_estimate=0.0,
                        metadata={"model": self.default_model, "voice": voice, "speed": speed},
                    )
                else:
                    error = f"HTTP {response.status_code}: {response.text[:200]}"
                    self.record_error(error)
                    return GenerationResult(
                        provider=self.name, provider_type="audio", status="error",
                        request_id=request_id, error=error, latency_ms=latency_ms,
                        prompt=text,
                    )
        except httpx.ConnectError:
            latency_ms = round((time.time() - start) * 1000, 1)
            error = "Kokoro TTS server not running. Install from: https://github.com/hexgrad/kokoro"
            self.record_error(error)
            return GenerationResult(
                provider=self.name, provider_type="audio", status="error",
                request_id=request_id, error=error, latency_ms=latency_ms,
                prompt=text,
            )
        except Exception as e:
            latency_ms = round((time.time() - start) * 1000, 1)
            self.record_error(str(e))
            return GenerationResult(
                provider=self.name, provider_type="audio", status="error",
                request_id=request_id, error=str(e)[:200], latency_ms=latency_ms,
                prompt=text,
            )


class OpenAITTSProvider(AudioProvider):
    """OpenAI TTS — cloud text-to-speech API.
    Requires OPENAI_API_KEY environment variable.
    https://platform.openai.com/docs/guides/text-to-speech
    """

    name = "openai_tts"
    tier = ProviderTier.PAID
    requires_api_key = True
    cloud_first = True
    base_url = "https://api.openai.com/v1/audio/speech"
    supported_models = ["tts-1", "tts-1-hd"]
    default_model = "tts-1"

    capabilities = [
        ProviderCapability(
            name="text_to_speech",
            description="Generate high-quality speech via OpenAI TTS API",
            input_types=["text"],
            output_types=["audio/mp3", "audio/wav", "audio/opus"],
            supports_seed=False,
        ),
    ]

    async def generate_audio(
        self,
        text: str,
        voice: str = "alloy",
        speed: float = 1.0,
        output_format: str = "mp3",
        **kwargs,
    ) -> GenerationResult:
        request_id = self._make_request_id()
        start = time.time()

        api_key = self.api_key
        if not api_key:
            latency_ms = round((time.time() - start) * 1000, 1)
            return GenerationResult(
                provider=self.name, provider_type="audio", status="error",
                request_id=request_id,
                error="No OPENAI_API_KEY set",
                latency_ms=latency_ms, prompt=text,
            )

        model = kwargs.get("model", self.default_model)
        payload = {
            "model": model,
            "input": text,
            "voice": voice,
            "speed": speed,
            "response_format": output_format,
        }

        try:
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(
                    self.base_url,
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                )
                latency_ms = round((time.time() - start) * 1000, 1)

                if response.status_code == 200:
                    self.record_success(latency_ms)
                    return GenerationResult(
                        provider=self.name,
                        provider_type="audio",
                        status="success",
                        request_id=request_id,
                        output_bytes=response.content,
                        output_format=output_format,
                        latency_ms=latency_ms,
                        prompt=text,
                        cost_estimate=0.015 * len(text) / 1000,  # ~$0.015/1K chars
                        metadata={"model": model, "voice": voice, "speed": speed},
                    )
                else:
                    error = f"HTTP {response.status_code}: {response.text[:200]}"
                    is_rl = response.status_code == 429
                    self.record_error(error, is_rate_limit=is_rl)
                    return GenerationResult(
                        provider=self.name, provider_type="audio",
                        status="rate_limited" if is_rl else "error",
                        request_id=request_id, error=error, latency_ms=latency_ms,
                        prompt=text,
                    )
        except Exception as e:
            latency_ms = round((time.time() - start) * 1000, 1)
            self.record_error(str(e))
            return GenerationResult(
                provider=self.name, provider_type="audio", status="error",
                request_id=request_id, error=str(e)[:200], latency_ms=latency_ms,
                prompt=text,
            )


class WhisperSTTProvider(STTProvider):
    """Whisper STT — speech-to-text via Whisper API.
    Requires a running Whisper server (e.g., faster-whisper-server).
    https://github.com/SYSTRAN/faster-whisper
    """

    name = "whisper_stt"
    tier = ProviderTier.FREE
    requires_api_key = False
    cloud_first = False
    base_url = "http://localhost:8000"
    supported_models = ["whisper-large-v3", "whisper-medium", "whisper-small", "whisper-turbo"]
    default_model = "whisper-large-v3"

    capabilities = [
        ProviderCapability(
            name="speech_to_text",
            description="Transcribe audio to text via Whisper",
            input_types=["audio/wav", "audio/mp3", "audio/opus"],
            output_types=["text"],
            supports_seed=False,
        ),
    ]

    async def transcribe_audio(
        self,
        audio_data: bytes,
        language: str = "en",
        **kwargs,
    ) -> GenerationResult:
        request_id = self._make_request_id()
        start = time.time()

        model = kwargs.get("model", self.default_model)

        try:
            async with httpx.AsyncClient(timeout=120) as client:
                files = {
                    "file": ("audio.wav", audio_data, "audio/wav"),
                }
                data = {
                    "model": model,
                    "language": language,
                }
                response = await client.post(
                    f"{self.base_url}/v1/audio/transcriptions",
                    files=files,
                    data=data,
                )
                latency_ms = round((time.time() - start) * 1000, 1)

                if response.status_code == 200:
                    result_data = response.json()
                    text = result_data.get("text", "")
                    self.record_success(latency_ms)
                    return GenerationResult(
                        provider=self.name,
                        provider_type="audio",
                        status="success",
                        request_id=request_id,
                        output_url="",
                        output_format="text",
                        latency_ms=latency_ms,
                        prompt=f"[transcription of {len(audio_data)} bytes]",
                        cost_estimate=0.0,
                        metadata={
                            "model": model,
                            "language": language,
                            "transcription": text,
                        },
                    )
                else:
                    error = f"HTTP {response.status_code}: {response.text[:200]}"
                    self.record_error(error)
                    return GenerationResult(
                        provider=self.name, provider_type="audio", status="error",
                        request_id=request_id, error=error, latency_ms=latency_ms,
                        prompt="[transcription]",
                    )
        except httpx.ConnectError:
            latency_ms = round((time.time() - start) * 1000, 1)
            error = "Whisper server not running. Install: pip install faster-whisper"
            self.record_error(error)
            return GenerationResult(
                provider=self.name, provider_type="audio", status="error",
                request_id=request_id, error=error, latency_ms=latency_ms,
                prompt="[transcription]",
            )
        except Exception as e:
            latency_ms = round((time.time() - start) * 1000, 1)
            self.record_error(str(e))
            return GenerationResult(
                provider=self.name, provider_type="audio", status="error",
                request_id=request_id, error=str(e)[:200], latency_ms=latency_ms,
                prompt="[transcription]",
            )
