"""
Music & SFX Generation — Meta AudioCraft, MusicGen, AudioGen.
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


class MusicGenModel(str, Enum):
    SMALL = "facebook/musicgen-small"
    MEDIUM = "facebook/musicgen-medium"
    LARGE = "facebook/musicgen-large"
    MELODY = "facebook/musicgen-melody"


class AudioGenModel(str, Enum):
    SMALL = "facebook/audiogen-small"
    MEDIUM = "facebook/audiogen-medium"
    LARGE = "facebook/audiogen-large"


class MusicTask(str, Enum):
    TEXT_TO_MUSIC = "text_to_music"
    TEXT_TO_SFX = "text_to_sfx"
    MELODY_CONDITIONED = "melody_conditioned"


class MusicGenStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    DEPENDENCY_MISSING = "dependency_missing"


@dataclass
class MusicGenProfile:
    name: str
    task: MusicTask
    model: str
    description: str
    license: str
    max_duration_secs: float
    sample_rate: int
    requires_gpu: bool
    min_vram_gb: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "task": self.task.value,
            "model": self.model,
            "description": self.description,
            "license": self.license,
            "max_duration_secs": self.max_duration_secs,
            "sample_rate": self.sample_rate,
            "requires_gpu": self.requires_gpu,
            "min_vram_gb": self.min_vram_gb,
        }


MUSIC_PROFILES: List[MusicGenProfile] = [
    MusicGenProfile(
        name="MusicGen Small", task=MusicTask.TEXT_TO_MUSIC,
        model=MusicGenModel.SMALL.value,
        description="Fast music generation (300M params, CPU-capable)",
        license="CC-BY-NC-4.0", max_duration_secs=30.0, sample_rate=32000,
        requires_gpu=False, min_vram_gb=0.0,
    ),
    MusicGenProfile(
        name="MusicGen Medium", task=MusicTask.TEXT_TO_MUSIC,
        model=MusicGenModel.MEDIUM.value,
        description="Balanced quality/speed (1.5B params)",
        license="CC-BY-NC-4.0", max_duration_secs=30.0, sample_rate=32000,
        requires_gpu=True, min_vram_gb=4.0,
    ),
    MusicGenProfile(
        name="MusicGen Large", task=MusicTask.TEXT_TO_MUSIC,
        model=MusicGenModel.LARGE.value,
        description="Highest quality music generation (3.3B params)",
        license="CC-BY-NC-4.0", max_duration_secs=30.0, sample_rate=32000,
        requires_gpu=True, min_vram_gb=8.0,
    ),
    MusicGenProfile(
        name="MusicGen Melody", task=MusicTask.MELODY_CONDITIONED,
        model=MusicGenModel.MELODY.value,
        description="Melody-conditioned music generation",
        license="CC-BY-NC-4.0", max_duration_secs=30.0, sample_rate=32000,
        requires_gpu=True, min_vram_gb=4.0,
    ),
    MusicGenProfile(
        name="AudioGen Small", task=MusicTask.TEXT_TO_SFX,
        model=AudioGenModel.SMALL.value,
        description="Sound effects generation (300M params)",
        license="CC-BY-NC-4.0", max_duration_secs=8.0, sample_rate=16000,
        requires_gpu=False, min_vram_gb=0.0,
    ),
    MusicGenProfile(
        name="AudioGen Medium", task=MusicTask.TEXT_TO_SFX,
        model=AudioGenModel.MEDIUM.value,
        description="Higher quality SFX generation",
        license="CC-BY-NC-4.0", max_duration_secs=8.0, sample_rate=16000,
        requires_gpu=True, min_vram_gb=4.0,
    ),
    MusicGenProfile(
        name="AudioGen Large", task=MusicTask.TEXT_TO_SFX,
        model=AudioGenModel.LARGE.value,
        description="Highest quality SFX generation",
        license="CC-BY-NC-4.0", max_duration_secs=8.0, sample_rate=16000,
        requires_gpu=True, min_vram_gb=8.0,
    ),
]


@dataclass
class MusicGenResult:
    provider: str = ""
    task: MusicTask = MusicTask.TEXT_TO_MUSIC
    status: MusicGenStatus = MusicGenStatus.PENDING
    request_id: str = ""
    prompt: str = ""
    output_path: str = ""
    output_format: str = "wav"
    duration_secs: float = 0.0
    sample_rate: int = 32000
    latency_ms: float = 0.0
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "provider": self.provider,
            "task": self.task.value,
            "status": self.status.value,
            "request_id": self.request_id,
            "prompt": self.prompt[:200],
            "output_path": self.output_path,
            "output_format": self.output_format,
            "duration_secs": round(self.duration_secs, 2),
            "sample_rate": self.sample_rate,
            "latency_ms": self.latency_ms,
            "error": self.error,
            "metadata": self.metadata,
            "created_at": self.created_at,
        }


# ── AudioCraft HTTP Provider ─────────────────────────────────────

class AudioCraftProvider:
    """Meta AudioCraft via HTTP API (MusicGen + AudioGen)."""

    name = "audiocraft"

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.base_url = self.config.get("url", "http://localhost:9876")

    async def generate_music(
        self, prompt: str, duration_secs: float = 10.0, model: str = "",
        output_path: str = "", **kwargs,
    ) -> MusicGenResult:
        request_id = f"ac-{int(time.time()*1000)}"
        start = time.time()
        if not model:
            model = MusicGenModel.SMALL.value
        try:
            async with httpx.AsyncClient(timeout=180) as client:
                resp = await client.post(
                    f"{self.base_url}/generate",
                    json={"prompt": prompt, "duration": duration_secs, "model": model},
                )
                latency_ms = round((time.time() - start) * 1000, 1)
                if resp.status_code == 200:
                    out = output_path or f"./output/audio/{request_id}.wav"
                    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
                    with open(out, "wb") as f:
                        f.write(resp.content)
                    return MusicGenResult(
                        provider="audiocraft", task=MusicTask.TEXT_TO_MUSIC,
                        status=MusicGenStatus.COMPLETED, request_id=request_id,
                        prompt=prompt, output_path=out, duration_secs=duration_secs,
                        latency_ms=latency_ms, metadata={"model": model},
                    )
                return MusicGenResult(
                    provider="audiocraft", task=MusicTask.TEXT_TO_MUSIC,
                    status=MusicGenStatus.FAILED, request_id=request_id,
                    prompt=prompt, latency_ms=latency_ms,
                    error=f"HTTP {resp.status_code}: {resp.text[:200]}",
                )
        except Exception as e:
            latency_ms = round((time.time() - start) * 1000, 1)
            return MusicGenResult(
                provider="audiocraft", task=MusicTask.TEXT_TO_MUSIC,
                status=MusicGenStatus.FAILED, request_id=request_id,
                prompt=prompt, latency_ms=latency_ms, error=str(e)[:200],
            )

    async def generate_sfx(
        self, prompt: str, duration_secs: float = 5.0,
        output_path: str = "", **kwargs,
    ) -> MusicGenResult:
        request_id = f"sfx-{int(time.time()*1000)}"
        start = time.time()
        try:
            async with httpx.AsyncClient(timeout=120) as client:
                resp = await client.post(
                    f"{self.base_url}/generate_sfx",
                    json={"prompt": prompt, "duration": duration_secs},
                )
                latency_ms = round((time.time() - start) * 1000, 1)
                if resp.status_code == 200:
                    out = output_path or f"./output/audio/{request_id}.wav"
                    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
                    with open(out, "wb") as f:
                        f.write(resp.content)
                    return MusicGenResult(
                        provider="audiocraft", task=MusicTask.TEXT_TO_SFX,
                        status=MusicGenStatus.COMPLETED, request_id=request_id,
                        prompt=prompt, output_path=out, duration_secs=duration_secs,
                        sample_rate=16000, latency_ms=latency_ms,
                    )
                return MusicGenResult(
                    provider="audiocraft", task=MusicTask.TEXT_TO_SFX,
                    status=MusicGenStatus.FAILED, request_id=request_id,
                    prompt=prompt, latency_ms=latency_ms,
                    error=f"HTTP {resp.status_code}: {resp.text[:200]}",
                )
        except Exception as e:
            latency_ms = round((time.time() - start) * 1000, 1)
            return MusicGenResult(
                provider="audiocraft", task=MusicTask.TEXT_TO_SFX,
                status=MusicGenStatus.FAILED, request_id=request_id,
                prompt=prompt, latency_ms=latency_ms, error=str(e)[:200],
            )

    async def generate_melody(
        self, prompt: str, melody_path: str, duration_secs: float = 10.0,
        output_path: str = "", **kwargs,
    ) -> MusicGenResult:
        request_id = f"mel-{int(time.time()*1000)}"
        start = time.time()
        try:
            async with httpx.AsyncClient(timeout=180) as client:
                with open(melody_path, "rb") as f:
                    files = {"melody": (os.path.basename(melody_path), f, "audio/wav")}
                    data = {"prompt": prompt, "duration": str(duration_secs)}
                    resp = await client.post(f"{self.base_url}/generate_melody", files=files, data=data)
                latency_ms = round((time.time() - start) * 1000, 1)
                if resp.status_code == 200:
                    out = output_path or f"./output/audio/{request_id}.wav"
                    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
                    with open(out, "wb") as f:
                        f.write(resp.content)
                    return MusicGenResult(
                        provider="audiocraft", task=MusicTask.MELODY_CONDITIONED,
                        status=MusicGenStatus.COMPLETED, request_id=request_id,
                        prompt=prompt, output_path=out, duration_secs=duration_secs,
                        latency_ms=latency_ms,
                    )
                return MusicGenResult(
                    provider="audiocraft", task=MusicTask.MELODY_CONDITIONED,
                    status=MusicGenStatus.FAILED, request_id=request_id,
                    prompt=prompt, latency_ms=latency_ms,
                    error=f"HTTP {resp.status_code}: {resp.text[:200]}",
                )
        except Exception as e:
            latency_ms = round((time.time() - start) * 1000, 1)
            return MusicGenResult(
                provider="audiocraft", task=MusicTask.MELODY_CONDITIONED,
                status=MusicGenStatus.FAILED, request_id=request_id,
                prompt=prompt, latency_ms=latency_ms, error=str(e)[:200],
            )


# ── Music Generation Engine ──────────────────────────────────────

class MusicGenerationEngine:
    """Unified music and SFX generation engine."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._audiocraft = AudioCraftProvider(self.config.get("audiocraft", {}))
        self._history: List[MusicGenResult] = []

    def get_profiles(self) -> List[Dict[str, Any]]:
        return [p.to_dict() for p in MUSIC_PROFILES]

    def get_models_for_task(self, task: MusicTask) -> List[Dict[str, Any]]:
        return [p.to_dict() for p in MUSIC_PROFILES if p.task == task]

    async def generate_music(
        self, prompt: str, duration_secs: float = 10.0, model: str = "",
        output_path: str = "", **kwargs,
    ) -> MusicGenResult:
        result = await self._audiocraft.generate_music(
            prompt=prompt, duration_secs=duration_secs,
            model=model, output_path=output_path, **kwargs,
        )
        self._history.append(result)
        return result

    async def generate_sfx(
        self, prompt: str, duration_secs: float = 5.0,
        output_path: str = "", **kwargs,
    ) -> MusicGenResult:
        result = await self._audiocraft.generate_sfx(
            prompt=prompt, duration_secs=duration_secs,
            output_path=output_path, **kwargs,
        )
        self._history.append(result)
        return result

    async def generate_melody(
        self, prompt: str, melody_path: str, duration_secs: float = 10.0,
        output_path: str = "", **kwargs,
    ) -> MusicGenResult:
        result = await self._audiocraft.generate_melody(
            prompt=prompt, melody_path=melody_path,
            duration_secs=duration_secs, output_path=output_path, **kwargs,
        )
        self._history.append(result)
        return result

    def get_stats(self) -> Dict[str, Any]:
        tasks: Dict[str, int] = {}
        statuses: Dict[str, int] = {}
        for r in self._history:
            tasks[r.task.value] = tasks.get(r.task.value, 0) + 1
            statuses[r.status.value] = statuses.get(r.status.value, 0) + 1
        return {
            "total_generations": len(self._history),
            "by_task": tasks,
            "by_status": statuses,
            "providers": ["audiocraft"],
            "profiles": len(MUSIC_PROFILES),
        }
