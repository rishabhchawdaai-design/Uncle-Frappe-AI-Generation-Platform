"""
Voice Cloning — XTTS (Coqui), Fish Speech, OpenVoice.
All providers attempt local inference or HTTP API.
Gracefully degrade when backends are unavailable.
"""
import asyncio
import hashlib
import logging
import os
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)


class VoiceCloningProvider(str, Enum):
    XTTS = "xtts"
    FISH_SPEECH = "fish_speech"
    OPENVOICE = "openvoice"


class VoiceCloneStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    DEPENDENCY_MISSING = "dependency_missing"


@dataclass
class VoiceCloneProfile:
    provider: VoiceCloningProvider
    name: str
    description: str
    license: str
    languages: List[str]
    requires_gpu: bool
    min_vram_gb: float
    voice_cloning: bool
    streaming: bool
    quality: str
    default_url: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "provider": self.provider.value,
            "name": self.name,
            "description": self.description,
            "license": self.license,
            "languages": self.languages,
            "requires_gpu": self.requires_gpu,
            "min_vram_gb": self.min_vram_gb,
            "voice_cloning": self.voice_cloning,
            "streaming": self.streaming,
            "quality": self.quality,
            "default_url": self.default_url,
        }


VOICE_CLONE_PROFILES: Dict[VoiceCloningProvider, VoiceCloneProfile] = {
    VoiceCloningProvider.XTTS: VoiceCloneProfile(
        provider=VoiceCloningProvider.XTTS,
        name="Coqui XTTS v2",
        description="Multilingual voice cloning TTS (17 languages, 6-sec sample)",
        license="CPML (non-commercial)",
        languages=["en", "es", "fr", "de", "it", "pt", "pl", "tr", "ru", "nl", "cs", "ar", "zh", "ja", "hu", "ko", "hi"],
        requires_gpu=True, min_vram_gb=2.0, voice_cloning=True, streaming=True,
        quality="high", default_url="http://localhost:5002",
    ),
    VoiceCloningProvider.FISH_SPEECH: VoiceCloneProfile(
        provider=VoiceCloningProvider.FISH_SPEECH,
        name="Fish Speech",
        description="Multilingual voice cloning TTS with streaming",
        license="CC-BY-NC-SA 4.0",
        languages=["en", "zh", "ja", "de", "fr", "es"],
        requires_gpu=True, min_vram_gb=4.0, voice_cloning=True, streaming=True,
        quality="high", default_url="http://localhost:8080",
    ),
    VoiceCloningProvider.OPENVOICE: VoiceCloneProfile(
        provider=VoiceCloningProvider.OPENVOICE,
        name="OpenVoice (MyShell)",
        description="Cross-lingual voice cloning with tone color converter",
        license="MIT",
        languages=["en", "zh", "ja", "ko"],
        requires_gpu=True, min_vram_gb=2.0, voice_cloning=True, streaming=False,
        quality="medium", default_url="http://localhost:5003",
    ),
}


@dataclass
class VoiceCloneResult:
    provider: str = ""
    status: VoiceCloneStatus = VoiceCloneStatus.PENDING
    request_id: str = ""
    output_path: str = ""
    output_format: str = "wav"
    latency_ms: float = 0.0
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "provider": self.provider,
            "status": self.status.value,
            "request_id": self.request_id,
            "output_path": self.output_path,
            "output_format": self.output_format,
            "latency_ms": self.latency_ms,
            "error": self.error,
            "metadata": self.metadata,
            "created_at": self.created_at,
        }


class VoiceCloningProviderBase:
    """Base class for voice cloning providers."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}

    async def clone_voice(
        self, reference_audio_path: str, text: str, language: str = "en",
        output_path: str = "", **kwargs,
    ) -> VoiceCloneResult:
        raise NotImplementedError


class XTVoiceCloningProvider(VoiceCloningProviderBase):
    """Coqui XTTS v2 — multilingual voice cloning."""

    name = "xtts"

    async def clone_voice(
        self, reference_audio_path: str, text: str, language: str = "en",
        output_path: str = "", **kwargs,
    ) -> VoiceCloneResult:
        request_id = f"xtts-{int(time.time()*1000)}"
        start = time.time()
        url = self.config.get("url", VOICE_CLONE_PROFILES[VoiceCloningProvider.XTTS].default_url)
        try:
            import base64
            with open(reference_audio_path, "rb") as f:
                ref_b64 = base64.b64encode(f.read()).decode()
            async with httpx.AsyncClient(timeout=120) as client:
                resp = await client.post(
                    f"{url}/clone",
                    json={"text": text, "language": language, "reference_audio": ref_b64},
                )
                latency_ms = round((time.time() - start) * 1000, 1)
                if resp.status_code == 200:
                    out = output_path or f"./output/audio/{request_id}.wav"
                    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
                    with open(out, "wb") as f:
                        f.write(resp.content)
                    return VoiceCloneResult(
                        provider="xtts", status=VoiceCloneStatus.COMPLETED,
                        request_id=request_id, output_path=out, latency_ms=latency_ms,
                    )
                return VoiceCloneResult(
                    provider="xtts", status=VoiceCloneStatus.FAILED,
                    request_id=request_id, latency_ms=latency_ms,
                    error=f"HTTP {resp.status_code}: {resp.text[:200]}",
                )
        except Exception as e:
            latency_ms = round((time.time() - start) * 1000, 1)
            return VoiceCloneResult(
                provider="xtts", status=VoiceCloneStatus.FAILED,
                request_id=request_id, latency_ms=latency_ms, error=str(e)[:200],
            )


class FishSpeechVoiceCloningProvider(VoiceCloningProviderBase):
    """Fish Speech — multilingual voice cloning with streaming."""

    name = "fish_speech"

    async def clone_voice(
        self, reference_audio_path: str, text: str, language: str = "en",
        output_path: str = "", **kwargs,
    ) -> VoiceCloneResult:
        request_id = f"fish-{int(time.time()*1000)}"
        start = time.time()
        url = self.config.get("url", VOICE_CLONE_PROFILES[VoiceCloningProvider.FISH_SPEECH].default_url)
        try:
            async with httpx.AsyncClient(timeout=120) as client:
                with open(reference_audio_path, "rb") as f:
                    files = {"reference": (os.path.basename(reference_audio_path), f, "audio/wav")}
                    data = {"text": text, "language": language}
                    resp = await client.post(f"{url}/clone", files=files, data=data)
                latency_ms = round((time.time() - start) * 1000, 1)
                if resp.status_code == 200:
                    out = output_path or f"./output/audio/{request_id}.wav"
                    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
                    with open(out, "wb") as f:
                        f.write(resp.content)
                    return VoiceCloneResult(
                        provider="fish_speech", status=VoiceCloneStatus.COMPLETED,
                        request_id=request_id, output_path=out, latency_ms=latency_ms,
                    )
                return VoiceCloneResult(
                    provider="fish_speech", status=VoiceCloneStatus.FAILED,
                    request_id=request_id, latency_ms=latency_ms,
                    error=f"HTTP {resp.status_code}: {resp.text[:200]}",
                )
        except Exception as e:
            latency_ms = round((time.time() - start) * 1000, 1)
            return VoiceCloneResult(
                provider="fish_speech", status=VoiceCloneStatus.FAILED,
                request_id=request_id, latency_ms=latency_ms, error=str(e)[:200],
            )


class OpenVoiceCloningProvider(VoiceCloningProviderBase):
    """OpenVoice (MyShell) — cross-lingual voice cloning."""

    name = "openvoice"

    async def clone_voice(
        self, reference_audio_path: str, text: str, language: str = "en",
        output_path: str = "", **kwargs,
    ) -> VoiceCloneResult:
        request_id = f"ov-{int(time.time()*1000)}"
        start = time.time()
        url = self.config.get("url", VOICE_CLONE_PROFILES[VoiceCloningProvider.OPENVOICE].default_url)
        try:
            async with httpx.AsyncClient(timeout=120) as client:
                with open(reference_audio_path, "rb") as f:
                    files = {"reference": (os.path.basename(reference_audio_path), f, "audio/wav")}
                    data = {"text": text, "language": language}
                    resp = await client.post(f"{url}/clone", files=files, data=data)
                latency_ms = round((time.time() - start) * 1000, 1)
                if resp.status_code == 200:
                    out = output_path or f"./output/audio/{request_id}.wav"
                    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
                    with open(out, "wb") as f:
                        f.write(resp.content)
                    return VoiceCloneResult(
                        provider="openvoice", status=VoiceCloneStatus.COMPLETED,
                        request_id=request_id, output_path=out, latency_ms=latency_ms,
                    )
                return VoiceCloneResult(
                    provider="openvoice", status=VoiceCloneStatus.FAILED,
                    request_id=request_id, latency_ms=latency_ms,
                    error=f"HTTP {resp.status_code}: {resp.text[:200]}",
                )
        except Exception as e:
            latency_ms = round((time.time() - start) * 1000, 1)
            return VoiceCloneResult(
                provider="openvoice", status=VoiceCloneStatus.FAILED,
                request_id=request_id, latency_ms=latency_ms, error=str(e)[:200],
            )


# ── Voice Cloning Engine ─────────────────────────────────────────

class VoiceCloningEngine:
    """Unified voice cloning engine across XTTS, Fish Speech, OpenVoice."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._providers: Dict[str, VoiceCloningProviderBase] = {
            "xtts": XTVoiceCloningProvider(self.config.get("xtts", {})),
            "fish_speech": FishSpeechVoiceCloningProvider(self.config.get("fish_speech", {})),
            "openvoice": OpenVoiceCloningProvider(self.config.get("openvoice", {})),
        }
        self._history: List[VoiceCloneResult] = []

    def get_profiles(self) -> List[Dict[str, Any]]:
        return [p.to_dict() for p in VOICE_CLONE_PROFILES.values()]

    def get_provider_names(self) -> List[str]:
        return list(self._providers.keys())

    async def clone_voice(
        self, reference_audio_path: str, text: str, language: str = "en",
        provider: Optional[str] = None, output_path: str = "", **kwargs,
    ) -> VoiceCloneResult:
        start = time.time()
        providers_to_try = []
        if provider and provider in self._providers:
            providers_to_try.append(provider)
        providers_to_try.extend([n for n in self._providers if n != provider])

        for pname in providers_to_try:
            result = await self._providers[pname].clone_voice(
                reference_audio_path=reference_audio_path, text=text,
                language=language, output_path=output_path, **kwargs,
            )
            if result.status == VoiceCloneStatus.COMPLETED:
                self._history.append(result)
                return result
            logger.warning(f"Voice clone provider {pname} failed: {result.error}")

        result = VoiceCloneResult(
            provider="none", status=VoiceCloneStatus.FAILED,
            error="All voice cloning providers failed or unavailable",
            latency_ms=round((time.time() - start) * 1000, 1),
        )
        self._history.append(result)
        return result

    def get_stats(self) -> Dict[str, Any]:
        statuses: Dict[str, int] = {}
        for r in self._history:
            statuses[r.status.value] = statuses.get(r.status.value, 0) + 1
        return {
            "total_clones": len(self._history),
            "by_status": statuses,
            "providers": self.get_provider_names(),
            "profiles": len(VOICE_CLONE_PROFILES),
        }
