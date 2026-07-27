"""
Audio Enhancement & Restoration — denoise, normalize, EQ, remove silence,
convert format, extract stems. Uses ffmpeg for all operations.
"""
import asyncio
import logging
import os
import shutil
import subprocess
import tempfile
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class AudioEnhanceOperation(str, Enum):
    DENOISE = "denoise"
    NORMALIZE = "normalize"
    EQUALIZE = "equalize"
    REMOVE_SILENCE = "remove_silence"
    CONVERT_FORMAT = "convert_format"
    RESAMPLE = "resample"
    COMPRESS = "compress"
    LIMIT = "limit"
    FADE_IN = "fade_in"
    FADE_OUT = "fade_out"
    TRIM_SILENCE = "trim_silence"
    EXTRACT_STEMS = "extract_stems"
    SPEED = "speed"
    PITCH = "pitch"
    REVERSE = "reverse"
    CONCAT = "concat"
    MIX = "mix"
    GAIN = "gain"


class AudioEnhanceStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    DEPENDENCY_MISSING = "dependency_missing"


@dataclass
class AudioEnhanceResult:
    operation: AudioEnhanceOperation = AudioEnhanceOperation.DENOISE
    provider: str = ""
    status: AudioEnhanceStatus = AudioEnhanceStatus.PENDING
    request_id: str = ""
    input_path: str = ""
    output_path: str = ""
    output_format: str = "wav"
    latency_ms: float = 0.0
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "operation": self.operation.value,
            "provider": self.provider,
            "status": self.status.value,
            "request_id": self.request_id,
            "input_path": self.input_path,
            "output_path": self.output_path,
            "output_format": self.output_format,
            "latency_ms": self.latency_ms,
            "error": self.error,
            "metadata": self.metadata,
            "created_at": self.created_at,
        }


def _has_ffmpeg() -> bool:
    return shutil.which("ffmpeg") is not None


async def _run_ffmpeg(args: List[str], timeout: int = 300) -> Dict[str, Any]:
    if not _has_ffmpeg():
        return {"error": "ffmpeg not installed", "returncode": -1, "stdout": "", "stderr": ""}
    try:
        proc = await asyncio.create_subprocess_exec(
            "ffmpeg", *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        return {
            "returncode": proc.returncode,
            "stdout": stdout.decode(errors="replace"),
            "stderr": stderr.decode(errors="replace"),
        }
    except asyncio.TimeoutError:
        return {"error": "ffmpeg timed out", "returncode": -1, "stdout": "", "stderr": ""}
    except Exception as e:
        return {"error": str(e)[:200], "returncode": -1, "stdout": "", "stderr": ""}


class AudioEnhancementEngine:
    """Unified audio enhancement and restoration engine."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._ffmpeg_available = _has_ffmpeg()
        self._history: List[AudioEnhanceResult] = []

    def get_available_operations(self) -> List[str]:
        if not self._ffmpeg_available:
            return []
        return [op.value for op in AudioEnhanceOperation]

    async def execute(self, operation: AudioEnhanceOperation, input_path: str = "", output_path: str = "", **kwargs) -> AudioEnhanceResult:
        start = time.time()
        if not output_path:
            ext = Path(input_path or "audio.wav").suffix or ".wav"
            output_path = f"./output/audio/enhanced_{int(time.time()*1000)}{ext}"
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        if not self._ffmpeg_available:
            result = AudioEnhanceResult(
                operation=operation, status=AudioEnhanceStatus.DEPENDENCY_MISSING,
                input_path=input_path, output_path=output_path, error="ffmpeg not installed",
            )
            self._history.append(result)
            return result

        handlers = {
            AudioEnhanceOperation.DENOISE: self._denoise,
            AudioEnhanceOperation.NORMALIZE: self._normalize,
            AudioEnhanceOperation.EQUALIZE: self._equalize,
            AudioEnhanceOperation.REMOVE_SILENCE: self._remove_silence,
            AudioEnhanceOperation.CONVERT_FORMAT: self._convert_format,
            AudioEnhanceOperation.RESAMPLE: self._resample,
            AudioEnhanceOperation.COMPRESS: self._compress,
            AudioEnhanceOperation.LIMIT: self._limit,
            AudioEnhanceOperation.FADE_IN: self._fade_in,
            AudioEnhanceOperation.FADE_OUT: self._fade_out,
            AudioEnhanceOperation.TRIM_SILENCE: self._trim_silence,
            AudioEnhanceOperation.SPEED: self._speed,
            AudioEnhanceOperation.PITCH: self._pitch,
            AudioEnhanceOperation.REVERSE: self._reverse,
            AudioEnhanceOperation.CONCAT: self._concat,
            AudioEnhanceOperation.MIX: self._mix,
            AudioEnhanceOperation.GAIN: self._gain,
        }
        handler = handlers.get(operation)
        if not handler:
            result = AudioEnhanceResult(
                operation=operation, status=AudioEnhanceStatus.FAILED,
                input_path=input_path, error=f"No handler for {operation.value}",
            )
            self._history.append(result)
            return result

        result = await handler(input_path, output_path, **kwargs)
        result.latency_ms = round((time.time() - start) * 1000, 1)
        self._history.append(result)
        return result

    async def _denoise(self, input_path, output_path, strength="medium", **kw):
        filters = {"light": "afftdn=nf=-25", "medium": "afftdn=nf=-30", "strong": "afftdn=nf=-35"}
        vf = filters.get(strength, filters["medium"])
        res = await _run_ffmpeg(["-y", "-i", input_path, "-af", vf, "-c:a", "pcm_s16le", output_path])
        return self._result(AudioEnhanceOperation.DENOISE, input_path, output_path, res, {"strength": strength})

    async def _normalize(self, input_path, output_path, target_level=-16, **kw):
        res = await _run_ffmpeg(["-y", "-i", input_path, "-af", f"loudnorm=I={target_level}:TP=-1.5:LRA=11", "-c:a", "pcm_s16le", output_path])
        return self._result(AudioEnhanceOperation.NORMALIZE, input_path, output_path, res, {"target_level": target_level})

    async def _equalize(self, input_path, output_path, preset="voice", **kw):
        presets = {
            "voice": "highpass=f=80,lowpass=f=8000,anequalizer=c0 f=1000 w=200 g=3 t=1",
            "music": "bass=g=3:f=100,treble=g=2:f=8000",
            "podcast": "highpass=f=80,lowpass=f=12000,compand=0.3|0.3:1|1:-90/-60|-60/-40|-40/-30|-20/-20:6:0:-90:0.2",
        }
        vf = presets.get(preset, presets["voice"])
        res = await _run_ffmpeg(["-y", "-i", input_path, "-af", vf, "-c:a", "pcm_s16le", output_path])
        return self._result(AudioEnhanceOperation.EQUALIZE, input_path, output_path, res, {"preset": preset})

    async def _remove_silence(self, input_path, output_path, threshold=-40, min_duration=0.5, **kw):
        res = await _run_ffmpeg(["-y", "-i", input_path, "-af", f"silenceremove=start_periods=1:start_duration={min_duration}:start_threshold={threshold}dB", "-c:a", "pcm_s16le", output_path])
        return self._result(AudioEnhanceOperation.REMOVE_SILENCE, input_path, output_path, res, {"threshold": threshold, "min_duration": min_duration})

    async def _convert_format(self, input_path, output_path, format="wav", bitrate="192k", **kw):
        ext_map = {"wav": "pcm_s16le", "mp3": "libmp3lame", "aac": "aac", "ogg": "libvorbis", "flac": "flac"}
        codec = ext_map.get(format, "pcm_s16le")
        args = ["-y", "-i", input_path, "-c:a", codec]
        if format == "mp3":
            args += ["-b:a", bitrate]
        args.append(output_path)
        res = await _run_ffmpeg(args)
        return self._result(AudioEnhanceOperation.CONVERT_FORMAT, input_path, output_path, res, {"format": format, "bitrate": bitrate})

    async def _resample(self, input_path, output_path, sample_rate=44100, **kw):
        res = await _run_ffmpeg(["-y", "-i", input_path, "-ar", str(sample_rate), "-c:a", "pcm_s16le", output_path])
        return self._result(AudioEnhanceOperation.RESAMPLE, input_path, output_path, res, {"sample_rate": sample_rate})

    async def _compress(self, input_path, output_path, ratio=4, threshold=-20, attack=5, release=50, **kw):
        res = await _run_ffmpeg(["-y", "-i", input_path, "-af", f"acompressor=threshold={threshold}dB:ratio={ratio}:attack={attack}:release={release}", "-c:a", "pcm_s16le", output_path])
        return self._result(AudioEnhanceOperation.COMPRESS, input_path, output_path, res, {"ratio": ratio, "threshold": threshold})

    async def _limit(self, input_path, output_path, limit=-1.0, **kw):
        res = await _run_ffmpeg(["-y", "-i", input_path, "-af", f"alimiter=limit={limit}", "-c:a", "pcm_s16le", output_path])
        return self._result(AudioEnhanceOperation.LIMIT, input_path, output_path, res, {"limit_db": limit})

    async def _fade_in(self, input_path, output_path, duration=1.0, **kw):
        res = await _run_ffmpeg(["-y", "-i", input_path, "-af", f"afade=t=in:st=0:d={duration}", "-c:a", "pcm_s16le", output_path])
        return self._result(AudioEnhanceOperation.FADE_IN, input_path, output_path, res, {"duration": duration})

    async def _fade_out(self, input_path, output_path, duration=1.0, **kw):
        res = await _run_ffmpeg(["-y", "-i", input_path, "-af", f"afade=t=out:st=0:d={duration}", "-c:a", "pcm_s16le", output_path])
        return self._result(AudioEnhanceOperation.FADE_OUT, input_path, output_path, res, {"duration": duration})

    async def _trim_silence(self, input_path, output_path, threshold=-40, **kw):
        res = await _run_ffmpeg(["-y", "-i", input_path, "-af", f"silenceremove=start_periods=1:start_duration=0:start_threshold={threshold}dB:stop_periods=-1:stop_duration=0.5:stop_threshold={threshold}dB", "-c:a", "pcm_s16le", output_path])
        return self._result(AudioEnhanceOperation.TRIM_SILENCE, input_path, output_path, res, {"threshold": threshold})

    async def _speed(self, input_path, output_path, factor=1.0, **kw):
        res = await _run_ffmpeg(["-y", "-i", input_path, "-af", f"atempo={factor}", "-c:a", "pcm_s16le", output_path])
        return self._result(AudioEnhanceOperation.SPEED, input_path, output_path, res, {"factor": factor})

    async def _pitch(self, input_path, output_path, semitones=0, **kw):
        factor = 2 ** (semitones / 12.0)
        res = await _run_ffmpeg(["-y", "-i", input_path, "-af", f"rubberband=pitch={factor}", "-c:a", "pcm_s16le", output_path])
        return self._result(AudioEnhanceOperation.PITCH, input_path, output_path, res, {"semitones": semitones, "factor": factor})

    async def _reverse(self, input_path, output_path, **kw):
        res = await _run_ffmpeg(["-y", "-i", input_path, "-af", "areverse", "-c:a", "pcm_s16le", output_path])
        return self._result(AudioEnhanceOperation.REVERSE, input_path, output_path, res, {})

    async def _concat(self, input_path, output_path, input_paths=None, **kw):
        paths = input_paths or []
        if not paths:
            return AudioEnhanceResult(operation=AudioEnhanceOperation.CONCAT, status=AudioEnhanceStatus.FAILED, error="input_paths required")
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            for p in paths:
                f.write(f"file '{os.path.abspath(p)}'\n")
            concat_file = f.name
        res = await _run_ffmpeg(["-y", "-f", "concat", "-safe", "0", "-i", concat_file, "-c", "copy", output_path])
        os.unlink(concat_file)
        return self._result(AudioEnhanceOperation.CONCAT, input_path, output_path, res, {"input_count": len(paths)})

    async def _mix(self, input_path, output_path, input_paths=None, weights=None, **kw):
        paths = input_paths or []
        if not paths:
            return AudioEnhanceResult(operation=AudioEnhanceOperation.MIX, status=AudioEnhanceStatus.FAILED, error="input_paths required")
        args = ["-y"]
        for p in paths:
            args += ["-i", p]
        n = len(paths)
        filter_parts = []
        for i in range(n):
            w = (weights[i] if weights and i < len(weights) else 1.0)
            filter_parts.append(f"[{i}]volume={w}[v{i}];")
        mix_inputs = "".join(f"[v{i}]" for i in range(n))
        filter_parts.append(f"{mix_inputs}amix=inputs={n}:duration=longest")
        filter_str = "".join(filter_parts)
        args += ["-filter_complex", filter_str, "-c:a", "pcm_s16le", output_path]
        res = await _run_ffmpeg(args)
        return self._result(AudioEnhanceOperation.MIX, input_path, output_path, res, {"input_count": n})

    async def _gain(self, input_path, output_path, gain_db=0, **kw):
        res = await _run_ffmpeg(["-y", "-i", input_path, "-af", f"volume={gain_db}dB", "-c:a", "pcm_s16le", output_path])
        return self._result(AudioEnhanceOperation.GAIN, input_path, output_path, res, {"gain_db": gain_db})

    def _result(self, operation, input_path, output_path, ffmpeg_res, metadata):
        status = AudioEnhanceStatus.COMPLETED if ffmpeg_res.get("returncode") == 0 else AudioEnhanceStatus.FAILED
        error = None if status == AudioEnhanceStatus.COMPLETED else (ffmpeg_res.get("error") or ffmpeg_res.get("stderr", "")[:200])
        return AudioEnhanceResult(
            operation=operation, provider="ffmpeg", status=status,
            input_path=input_path, output_path=output_path,
            error=error, metadata=metadata,
        )

    async def denoise(self, input_path, output_path="", **kw): return await self.execute(AudioEnhanceOperation.DENOISE, input_path, output_path, **kw)
    async def normalize(self, input_path, output_path="", **kw): return await self.execute(AudioEnhanceOperation.NORMALIZE, input_path, output_path, **kw)
    async def equalize(self, input_path, output_path="", **kw): return await self.execute(AudioEnhanceOperation.EQUALIZE, input_path, output_path, **kw)
    async def remove_silence(self, input_path, output_path="", **kw): return await self.execute(AudioEnhanceOperation.REMOVE_SILENCE, input_path, output_path, **kw)
    async def convert_format(self, input_path, output_path="", **kw): return await self.execute(AudioEnhanceOperation.CONVERT_FORMAT, input_path, output_path, **kw)
    async def resample(self, input_path, output_path="", **kw): return await self.execute(AudioEnhanceOperation.RESAMPLE, input_path, output_path, **kw)
    async def compress(self, input_path, output_path="", **kw): return await self.execute(AudioEnhanceOperation.COMPRESS, input_path, output_path, **kw)
    async def speed(self, input_path, output_path="", **kw): return await self.execute(AudioEnhanceOperation.SPEED, input_path, output_path, **kw)
    async def pitch(self, input_path, output_path="", **kw): return await self.execute(AudioEnhanceOperation.PITCH, input_path, output_path, **kw)
    async def fade_in(self, input_path, output_path="", **kw): return await self.execute(AudioEnhanceOperation.FADE_IN, input_path, output_path, **kw)
    async def fade_out(self, input_path, output_path="", **kw): return await self.execute(AudioEnhanceOperation.FADE_OUT, input_path, output_path, **kw)
    async def gain(self, input_path, output_path="", **kw): return await self.execute(AudioEnhanceOperation.GAIN, input_path, output_path, **kw)

    def get_stats(self) -> Dict[str, Any]:
        ops: Dict[str, int] = {}
        for r in self._history:
            ops[r.operation.value] = ops.get(r.operation.value, 0) + 1
        return {
            "total_enhancements": len(self._history),
            "by_operation": ops,
            "ffmpeg_available": self._ffmpeg_available,
            "supported_operations": len(self.get_available_operations()),
        }
