"""
Audio Generation Engine — orchestrates TTS and STT across providers.

Based on ACOS Research: AUDIO_SPEECH_RESEARCH.md
Supports: Piper TTS, Kokoro TTS, OpenAI TTS, Whisper STT
"""
import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from .providers.base import GenerationResult, ProviderType
from .providers.registry import get_registry

logger = logging.getLogger(__name__)


class AudioTask(str, Enum):
    TEXT_TO_SPEECH = "text_to_speech"
    SPEECH_TO_TEXT = "speech_to_text"
    VOICE_CLONING = "voice_cloning"
    AUDIO_TRANSLATION = "audio_translation"


@dataclass
class AudioRequest:
    """Request for audio generation or transcription."""
    task: AudioTask = AudioTask.TEXT_TO_SPEECH
    text: str = ""
    audio_data: bytes = field(default=b"")
    voice: str = "default"
    speed: float = 1.0
    language: str = "en"
    output_format: str = "wav"
    provider: Optional[str] = None
    model: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        pass


@dataclass
class AudioResult:
    """Result of audio generation or transcription."""
    task: AudioTask = AudioTask.TEXT_TO_SPEECH
    provider: str = ""
    status: str = "pending"
    request_id: str = ""
    output_bytes: Optional[bytes] = None
    output_path: str = ""
    output_format: str = "wav"
    transcription: str = ""
    latency_ms: float = 0.0
    cost_estimate: float = 0.0
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task": self.task.value,
            "provider": self.provider,
            "status": self.status,
            "request_id": self.request_id,
            "output_format": self.output_format,
            "output_size_bytes": len(self.output_bytes) if self.output_bytes else 0,
            "transcription": self.transcription[:200] if self.transcription else "",
            "latency_ms": round(self.latency_ms, 1),
            "cost_estimate": round(self.cost_estimate, 6),
            "error": self.error,
            "created_at": self.created_at,
        }


# Voice presets per provider
VOICE_PRESETS = {
    "piper_tts": {
        "default": "en_US-lessac-medium",
        "male": "en_US-lessac-medium",
        "female": "en_US-amy-medium",
        "british": "en_GB-alba-medium",
    },
    "kokoro_tts": {
        "default": "af_heart",
        "female": "af_heart",
        "male": "am_adam",
        "british": "bf_emma",
    },
    "openai_tts": {
        "default": "alloy",
        "alloy": "alloy",
        "echo": "echo",
        "fable": "fable",
        "onyx": "onyx",
        "nova": "nova",
        "shimmer": "shimmer",
    },
}


class AudioGenerationEngine:
    """
    Orchestrates audio generation across multiple providers.

    Pipeline:
    1. Parse request (TTS or STT)
    2. Select provider (auto or specified)
    3. Execute with fallback
    4. Return result
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._registry = get_registry()
        self._history: List[AudioResult] = []
        self._output_dir = self.config.get("output_dir", "./output/audio")

    async def text_to_speech(
        self,
        text: str,
        voice: str = "default",
        speed: float = 1.0,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        output_format: str = "wav",
        **kwargs,
    ) -> AudioResult:
        """Generate speech from text using the best available TTS provider."""
        request = AudioRequest(
            task=AudioTask.TEXT_TO_SPEECH,
            text=text,
            voice=voice,
            speed=speed,
            provider=provider,
            model=model,
            output_format=output_format,
        )
        return await self._execute_tts(request)

    async def transcribe(
        self,
        audio_data: bytes,
        language: str = "en",
        provider: Optional[str] = None,
        model: Optional[str] = None,
        **kwargs,
    ) -> AudioResult:
        """Transcribe audio to text using the best available STT provider."""
        request = AudioRequest(
            task=AudioTask.SPEECH_TO_TEXT,
            audio_data=audio_data,
            language=language,
            provider=provider,
            model=model,
        )
        return await self._execute_stt(request)

    async def _execute_tts(self, request: AudioRequest) -> AudioResult:
        """Execute TTS with provider selection and fallback."""
        start = time.time()

        # Get TTS providers
        tts_providers = self._get_tts_providers()

        if not tts_providers:
            return AudioResult(
                task=request.task,
                provider="none",
                status="error",
                error="No TTS providers available",
                latency_ms=(time.time() - start) * 1000,
            )

        # If specific provider requested, try that first
        if request.provider:
            named = [p for p in tts_providers if p.name == request.provider]
            if named:
                tts_providers = named + [p for p in tts_providers if p.name != request.provider]

        # Try each provider
        last_error = None
        for provider in tts_providers:
            if not provider.is_available:
                continue

            # Resolve voice
            voice = self._resolve_voice(provider.name, request.voice)

            result = await provider.generate_audio(
                text=request.text,
                voice=voice,
                speed=request.speed,
                output_format=request.output_format,
                model=request.model or "",
            )

            if result.status == "success":
                audio_result = AudioResult(
                    task=request.task,
                    provider=provider.name,
                    status="success",
                    request_id=result.request_id,
                    output_bytes=result.output_bytes,
                    output_format=request.output_format,
                    latency_ms=result.latency_ms,
                    cost_estimate=result.cost_estimate,
                    metadata=result.metadata,
                )
                self._history.append(audio_result)
                return audio_result

            last_error = result.error
            logger.warning(f"TTS provider {provider.name} failed: {result.error}")

        return AudioResult(
            task=request.task,
            provider="none",
            status="error",
            error=f"All TTS providers failed. Last error: {last_error}",
            latency_ms=(time.time() - start) * 1000,
        )

    async def _execute_stt(self, request: AudioRequest) -> AudioResult:
        """Execute STT with provider selection and fallback."""
        start = time.time()

        stt_providers = self._get_stt_providers()

        if not stt_providers:
            return AudioResult(
                task=request.task,
                provider="none",
                status="error",
                error="No STT providers available",
                latency_ms=(time.time() - start) * 1000,
            )

        if request.provider:
            named = [p for p in stt_providers if p.name == request.provider]
            if named:
                stt_providers = named + [p for p in stt_providers if p.name != request.provider]

        last_error = None
        for provider in stt_providers:
            if not provider.is_available:
                continue

            result = await provider.transcribe_audio(
                audio_data=request.audio_data,
                language=request.language,
                model=request.model or "",
            )

            if result.status == "success":
                transcription = result.metadata.get("transcription", "")
                audio_result = AudioResult(
                    task=request.task,
                    provider=provider.name,
                    status="success",
                    request_id=result.request_id,
                    transcription=transcription,
                    latency_ms=result.latency_ms,
                    cost_estimate=result.cost_estimate,
                    metadata=result.metadata,
                )
                self._history.append(audio_result)
                return audio_result

            last_error = result.error
            logger.warning(f"STT provider {provider.name} failed: {result.error}")

        return AudioResult(
            task=request.task,
            provider="none",
            status="error",
            error=f"All STT providers failed. Last error: {last_error}",
            latency_ms=(time.time() - start) * 1000,
        )

    def _get_tts_providers(self):
        """Get all registered TTS providers."""
        from .providers.audio_providers import AudioProvider as AudioProv
        providers = []
        for p in self._registry.get_all():
            if isinstance(p, AudioProv) and hasattr(p, 'generate_audio'):
                providers.append(p)
        return providers

    def _get_stt_providers(self):
        """Get all registered STT providers."""
        from .providers.audio_providers import STTProvider as STTProv
        providers = []
        for p in self._registry.get_all():
            if isinstance(p, STTProv) and hasattr(p, 'transcribe_audio'):
                providers.append(p)
        return providers

    def _resolve_voice(self, provider_name: str, voice: str) -> str:
        """Resolve voice alias to provider-specific voice ID."""
        presets = VOICE_PRESETS.get(provider_name, {})
        return presets.get(voice, voice)

    def list_providers(self) -> List[Dict[str, Any]]:
        """List all audio providers."""
        tts = self._get_tts_providers()
        stt = self._get_stt_providers()
        return {
            "tts": [{"name": p.name, "tier": p.tier.value, "available": p.is_available} for p in tts],
            "stt": [{"name": p.name, "tier": p.tier.value, "available": p.is_available} for p in stt],
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get audio generation statistics."""
        total = len(self._history)
        success = sum(1 for r in self._history if r.status == "success")
        tts_count = sum(1 for r in self._history if r.task == AudioTask.TEXT_TO_SPEECH)
        stt_count = sum(1 for r in self._history if r.task == AudioTask.SPEECH_TO_TEXT)
        return {
            "total_requests": total,
            "successful": success,
            "failed": total - success,
            "tts_requests": tts_count,
            "stt_requests": stt_count,
            "avg_latency_ms": round(
                sum(r.latency_ms for r in self._history) / max(total, 1), 1
            ),
        }
