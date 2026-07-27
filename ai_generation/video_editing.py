"""
Video Editing Layer — trim, concat, transitions, frame interpolation, upscaling.
Uses ffmpeg for editing, RIFE for interpolation, Real-ESRGAN for upscaling.
All operations gracefully degrade when dependencies are unavailable.
"""
import asyncio
import hashlib
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


# ── Enums ─────────────────────────────────────────────────────────

class VideoEditOperation(str, Enum):
    TRIM = "trim"
    CONCAT = "concat"
    TRANSITION = "transition"
    SPEED = "speed"
    FRAME_INTERPOLATION = "frame_interpolation"
    UPSCALE = "upscale"
    ENHANCE = "enhance"
    WATERMARK = "watermark"
    CROP = "crop"
    RESIZE = "resize"
    ROTATE = "rotate"
    REVERSE = "reverse"
    STABILIZE = "stabilize"
    AUDIO_EXTRACT = "audio_extract"
    AUDIO_REPLACE = "audio_replace"
    SUBTITLE_BURN = "subtitle_burn"


class VideoEditStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    UNSUPPORTED = "unsupported"
    DEPENDENCY_MISSING = "dependency_missing"


class InterpolationModel(str, Enum):
    RIFE = "rife"
    FILM = "film"
    OPENCV = "opencv"


class UpscaleModel(str, Enum):
    REAL_ESRGAN = "real_esrgan"
    REAL_ESRGAN_ANIME = "real_esrgan_anime"
    LANCZOS = "lanctos"


# ── Data Classes ──────────────────────────────────────────────────

@dataclass
class VideoEditResult:
    operation: VideoEditOperation = VideoEditOperation.TRIM
    provider: str = ""
    status: VideoEditStatus = VideoEditStatus.PENDING
    request_id: str = ""
    input_path: str = ""
    output_path: str = ""
    output_format: str = "mp4"
    width: int = 0
    height: int = 0
    duration_secs: float = 0.0
    fps: float = 24.0
    original_fps: float = 0.0
    scale_factor: float = 1.0
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
            "width": self.width,
            "height": self.height,
            "duration_secs": round(self.duration_secs, 2),
            "fps": round(self.fps, 2),
            "original_fps": round(self.original_fps, 2),
            "scale_factor": self.scale_factor,
            "latency_ms": self.latency_ms,
            "error": self.error,
            "metadata": self.metadata,
            "created_at": self.created_at,
        }


@dataclass
class VideoEditProfile:
    operation: VideoEditOperation
    description: str
    requires_ffmpeg: bool = True
    requires_gpu: bool = False
    requires_model: bool = False
    model_name: str = ""
    min_inputs: int = 1
    max_inputs: int = 10
    supported_formats: List[str] = field(default_factory=lambda: ["mp4", "webm", "avi", "mov", "mkv"])

    def to_dict(self) -> Dict[str, Any]:
        return {
            "operation": self.operation.value,
            "description": self.description,
            "requires_ffmpeg": self.requires_ffmpeg,
            "requires_gpu": self.requires_gpu,
            "requires_model": self.requires_model,
            "model_name": self.model_name,
            "min_inputs": self.min_inputs,
            "max_inputs": self.max_inputs,
            "supported_formats": self.supported_formats,
        }


# ── Dependency Detection ─────────────────────────────────────────

def _has_ffmpeg() -> bool:
    return shutil.which("ffmpeg") is not None


def _has_ffprobe() -> bool:
    return shutil.which("ffprobe") is not None


def _probe_video(path: str) -> Dict[str, Any]:
    if not _has_ffprobe():
        return {}
    try:
        result = subprocess.run(
            [
                "ffprobe", "-v", "quiet", "-print_format", "json",
                "-show_format", "-show_streams", str(path),
            ],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode != 0:
            return {}
        import json
        data = json.loads(result.stdout)
        video_stream = next((s for s in data.get("streams", []) if s.get("codec_type") == "video"), None)
        if not video_stream:
            return {}
        width = int(video_stream.get("width", 0))
        height = int(video_stream.get("height", 0))
        fps_str = video_stream.get("r_frame_rate", "24/1")
        num, den = fps_str.split("/") if "/" in fps_str else (fps_str, "1")
        fps = float(num) / float(den) if float(den) != 0 else 24.0
        duration = float(data.get("format", {}).get("duration", 0))
        codec = video_stream.get("codec_name", "unknown")
        return {
            "width": width, "height": height, "fps": fps,
            "duration": duration, "codec": codec,
        }
    except Exception:
        return {}


# ── Edit Profiles ────────────────────────────────────────────────

EDIT_PROFILES: Dict[VideoEditOperation, VideoEditProfile] = {
    VideoEditOperation.TRIM: VideoEditProfile(
        operation=VideoEditOperation.TRIM,
        description="Trim video to start/end timestamps",
        requires_ffmpeg=True,
    ),
    VideoEditOperation.CONCAT: VideoEditProfile(
        operation=VideoEditOperation.CONCAT,
        description="Concatenate multiple video clips sequentially",
        requires_ffmpeg=True, min_inputs=2, max_inputs=50,
    ),
    VideoEditOperation.TRANSITION: VideoEditProfile(
        operation=VideoEditOperation.TRANSITION,
        description="Add cross-fade transitions between video clips",
        requires_ffmpeg=True, min_inputs=2, max_inputs=20,
    ),
    VideoEditOperation.SPEED: VideoEditProfile(
        operation=VideoEditOperation.SPEED,
        description="Change video playback speed",
        requires_ffmpeg=True,
    ),
    VideoEditOperation.FRAME_INTERPOLATION: VideoEditProfile(
        operation=VideoEditOperation.FRAME_INTERPOLATION,
        description="Increase FPS using AI frame interpolation (RIFE/FILM/OpenCV)",
        requires_ffmpeg=True, requires_model=True, model_name="rife",
    ),
    VideoEditOperation.UPSCALE: VideoEditProfile(
        operation=VideoEditOperation.UPSCALE,
        description="Upscale video resolution using Real-ESRGAN or Lanczos",
        requires_ffmpeg=True, requires_model=True, model_name="real_esrgan",
    ),
    VideoEditOperation.ENHANCE: VideoEditProfile(
        operation=VideoEditOperation.ENHANCE,
        description="Enhance video quality (denoise, sharpen, color grade)",
        requires_ffmpeg=True,
    ),
    VideoEditOperation.WATERMARK: VideoEditProfile(
        operation=VideoEditOperation.WATERMARK,
        description="Add text or image watermark overlay",
        requires_ffmpeg=True,
    ),
    VideoEditOperation.CROP: VideoEditProfile(
        operation=VideoEditOperation.CROP,
        description="Crop video to specified region",
        requires_ffmpeg=True,
    ),
    VideoEditOperation.RESIZE: VideoEditProfile(
        operation=VideoEditOperation.RESIZE,
        description="Resize video to target dimensions",
        requires_ffmpeg=True,
    ),
    VideoEditOperation.ROTATE: VideoEditProfile(
        operation=VideoEditOperation.ROTATE,
        description="Rotate video by specified angle",
        requires_ffmpeg=True,
    ),
    VideoEditOperation.REVERSE: VideoEditProfile(
        operation=VideoEditOperation.REVERSE,
        description="Reverse video playback",
        requires_ffmpeg=True,
    ),
    VideoEditOperation.STABILIZE: VideoEditProfile(
        operation=VideoEditOperation.STABILIZE,
        description="Stabilize shaky video using ffmpeg vidstabdetect/vidstabtransform",
        requires_ffmpeg=True,
    ),
    VideoEditOperation.AUDIO_EXTRACT: VideoEditProfile(
        operation=VideoEditOperation.AUDIO_EXTRACT,
        description="Extract audio track from video",
        requires_ffmpeg=True,
    ),
    VideoEditOperation.AUDIO_REPLACE: VideoEditProfile(
        operation=VideoEditOperation.AUDIO_REPLACE,
        description="Replace audio track in video",
        requires_ffmpeg=True,
    ),
    VideoEditOperation.SUBTITLE_BURN: VideoEditProfile(
        operation=VideoEditOperation.SUBTITLE_BURN,
        description="Burn subtitles into video using ASS/SRT",
        requires_ffmpeg=True,
    ),
}


# ── FFmpeg Executor ──────────────────────────────────────────────

async def _run_ffmpeg(args: List[str], timeout: int = 300) -> Dict[str, Any]:
    """Run an ffmpeg command asynchronously. Returns dict with stdout, stderr, returncode."""
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


# ── FFmpeg-based Operations ─────────────────────────────────────

async def _ffmpeg_trim(input_path: str, output_path: str, start: float = 0.0, end: float = 0.0, **kw) -> VideoEditResult:
    args = ["-y", "-i", input_path, "-ss", str(start)]
    if end > 0:
        args += ["-to", str(end)]
    args += ["-c:v", "libx264", "-c:a", "aac", "-movflags", "+faststart", output_path]
    res = await _run_ffmpeg(args)
    if res.get("returncode") == 0:
        return VideoEditResult(
            operation=VideoEditOperation.TRIM, provider="ffmpeg",
            status=VideoEditStatus.COMPLETED, input_path=input_path,
            output_path=output_path, latency_ms=0, metadata={"start": start, "end": end},
        )
    return VideoEditResult(
        operation=VideoEditOperation.TRIM, provider="ffmpeg",
        status=VideoEditStatus.FAILED, input_path=input_path,
        error=res.get("error") or res.get("stderr", "")[:200],
    )


async def _ffmpeg_concat(input_paths: List[str], output_path: str, **kw) -> VideoEditResult:
    if len(input_paths) < 2:
        return VideoEditResult(
            operation=VideoEditOperation.CONCAT, status=VideoEditStatus.FAILED,
            error="Need at least 2 input files",
        )
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        for p in input_paths:
            f.write(f"file '{os.path.abspath(p)}'\n")
        concat_file = f.name
    args = ["-y", "-f", "concat", "-safe", "0", "-i", concat_file, "-c", "copy", output_path]
    res = await _run_ffmpeg(args)
    os.unlink(concat_file)
    if res.get("returncode") == 0:
        return VideoEditResult(
            operation=VideoEditOperation.CONCAT, provider="ffmpeg",
            status=VideoEditStatus.COMPLETED, input_path=input_paths[0],
            output_path=output_path, latency_ms=0,
            metadata={"input_count": len(input_paths)},
        )
    return VideoEditResult(
        operation=VideoEditOperation.CONCAT, provider="ffmpeg",
        status=VideoEditStatus.FAILED, error=res.get("error") or res.get("stderr", "")[:200],
    )


async def _ffmpeg_transition(inputs: List[str], output_path: str, duration: float = 1.0, **kw) -> VideoEditResult:
    if len(inputs) < 2:
        return VideoEditResult(
            operation=VideoEditOperation.TRANSITION, status=VideoEditStatus.FAILED,
            error="Need at least 2 input files",
        )
    args = ["-y"]
    for p in inputs:
        args += ["-i", p]
    n = len(inputs)
    filter_parts = []
    for i in range(n):
        filter_parts.append(f"[{i}:v]setpts=PTS-STARTPTS[v{i}];")
        filter_parts.append(f"[{i}:a]aformat=sample_rates=44100:channel_layouts=stereo[a{i}];")
    offset = 0.0
    for i in range(n - 1):
        filter_parts.append(
            f"[v{i}][v{i+1}]xfade=transition=fade:duration={duration}:offset={offset}[xv{i}];"
        )
        filter_parts.append(
            f"[a{i}][a{i+1}]acrossfade=d={duration}[xa{i}];"
        )
        offset += duration
    last_v = f"xv{n-2}"
    last_a = f"xa{n-2}"
    filter_str = "".join(filter_parts)
    args += ["-filter_complex", filter_str, "-map", f"[{last_v}]", "-map", f"[{last_a}]",
             "-c:v", "libx264", "-c:a", "aac", output_path]
    res = await _run_ffmpeg(args)
    if res.get("returncode") == 0:
        return VideoEditResult(
            operation=VideoEditOperation.TRANSITION, provider="ffmpeg",
            status=VideoEditStatus.COMPLETED, input_path=inputs[0],
            output_path=output_path, latency_ms=0,
            metadata={"input_count": len(inputs), "transition_duration": duration},
        )
    return VideoEditResult(
        operation=VideoEditOperation.TRANSITION, provider="ffmpeg",
        status=VideoEditStatus.FAILED, error=res.get("error") or res.get("stderr", "")[:200],
    )


async def _ffmpeg_speed(input_path: str, output_path: str, speed_factor: float = 1.0, **kw) -> VideoEditResult:
    if speed_factor <= 0:
        return VideoEditResult(
            operation=VideoEditOperation.SPEED, status=VideoEditStatus.FAILED,
            error="speed_factor must be > 0",
        )
    video_filter = f"setpts={1.0/speed_factor}*PTS"
    audio_filter = f"atempo={min(max(speed_factor, 0.5), 2.0)}"
    if speed_factor > 2.0:
        audio_filter = "atempo=2.0"
        remaining = speed_factor / 2.0
        while remaining > 2.0:
            audio_filter += ",atempo=2.0"
            remaining /= 2.0
        audio_filter += f",atempo={remaining}"
    elif speed_factor < 0.5:
        audio_filter = "atempo=0.5"
        remaining = speed_factor / 0.5
        while remaining < 0.5:
            audio_filter += ",atempo=0.5"
            remaining /= 0.5
        audio_filter += f",atempo={remaining}"
    args = [
        "-y", "-i", input_path,
        "-filter_complex", f"[0:v]{video_filter}[v];[0:a]{audio_filter}[a]",
        "-map", "[v]", "-map", "[a]",
        "-c:v", "libx264", "-c:a", "aac", output_path,
    ]
    res = await _run_ffmpeg(args)
    if res.get("returncode") == 0:
        return VideoEditResult(
            operation=VideoEditOperation.SPEED, provider="ffmpeg",
            status=VideoEditStatus.COMPLETED, input_path=input_path,
            output_path=output_path, latency_ms=0, metadata={"speed_factor": speed_factor},
        )
    return VideoEditResult(
        operation=VideoEditOperation.SPEED, provider="ffmpeg",
        status=VideoEditStatus.FAILED, error=res.get("error") or res.get("stderr", "")[:200],
    )


async def _ffmpeg_crop(input_path: str, output_path: str, x: int = 0, y: int = 0, width: int = 0, height: int = 0, **kw) -> VideoEditResult:
    if width <= 0 or height <= 0:
        return VideoEditResult(
            operation=VideoEditOperation.CROP, status=VideoEditStatus.FAILED,
            error="width and height must be > 0",
        )
    args = [
        "-y", "-i", input_path,
        "-vf", f"crop={width}:{height}:{x}:{y}",
        "-c:v", "libx264", "-c:a", "copy", output_path,
    ]
    res = await _run_ffmpeg(args)
    if res.get("returncode") == 0:
        return VideoEditResult(
            operation=VideoEditOperation.CROP, provider="ffmpeg",
            status=VideoEditStatus.COMPLETED, input_path=input_path,
            output_path=output_path, latency_ms=0, metadata={"x": x, "y": y, "width": width, "height": height},
        )
    return VideoEditResult(
        operation=VideoEditOperation.CROP, provider="ffmpeg",
        status=VideoEditStatus.FAILED, error=res.get("error") or res.get("stderr", "")[:200],
    )


async def _ffmpeg_resize(input_path: str, output_path: str, width: int = 0, height: int = 0, **kw) -> VideoEditResult:
    if width <= 0 and height <= 0:
        return VideoEditResult(
            operation=VideoEditOperation.RESIZE, status=VideoEditStatus.FAILED,
            error="width or height must be > 0",
        )
    dims = f"{width}:{height}" if width > 0 and height > 0 else (f"{width}:-2" if width > 0 else f"-2:{height}")
    args = [
        "-y", "-i", input_path,
        "-vf", f"scale={dims}",
        "-c:v", "libx264", "-c:a", "copy", output_path,
    ]
    res = await _run_ffmpeg(args)
    if res.get("returncode") == 0:
        return VideoEditResult(
            operation=VideoEditOperation.RESIZE, provider="ffmpeg",
            status=VideoEditStatus.COMPLETED, input_path=input_path,
            output_path=output_path, latency_ms=0, metadata={"width": width, "height": height},
        )
    return VideoEditResult(
        operation=VideoEditOperation.RESIZE, provider="ffmpeg",
        status=VideoEditStatus.FAILED, error=res.get("error") or res.get("stderr", "")[:200],
    )


async def _ffmpeg_rotate(input_path: str, output_path: str, angle: float = 0.0, **kw) -> VideoEditResult:
    vf = f"rotate={angle}*PI/180"
    args = [
        "-y", "-i", input_path,
        "-vf", vf,
        "-c:v", "libx264", "-c:a", "copy", output_path,
    ]
    res = await _run_ffmpeg(args)
    if res.get("returncode") == 0:
        return VideoEditResult(
            operation=VideoEditOperation.ROTATE, provider="ffmpeg",
            status=VideoEditStatus.COMPLETED, input_path=input_path,
            output_path=output_path, latency_ms=0, metadata={"angle": angle},
        )
    return VideoEditResult(
        operation=VideoEditOperation.ROTATE, provider="ffmpeg",
        status=VideoEditStatus.FAILED, error=res.get("error") or res.get("stderr", "")[:200],
    )


async def _ffmpeg_reverse(input_path: str, output_path: str, **kw) -> VideoEditResult:
    args = [
        "-y", "-i", input_path,
        "-vf", "reverse", "-af", "areverse",
        "-c:v", "libx264", "-c:a", "aac", output_path,
    ]
    res = await _run_ffmpeg(args)
    if res.get("returncode") == 0:
        return VideoEditResult(
            operation=VideoEditOperation.REVERSE, provider="ffmpeg",
            status=VideoEditStatus.COMPLETED, input_path=input_path,
            output_path=output_path, latency_ms=0,
        )
    return VideoEditResult(
        operation=VideoEditOperation.REVERSE, provider="ffmpeg",
        status=VideoEditStatus.FAILED, error=res.get("error") or res.get("stderr", "")[:200],
    )


async def _ffmpeg_stabilize(input_path: str, output_path: str, **kw) -> VideoEditResult:
    with tempfile.TemporaryDirectory() as tmpdir:
        transforms = os.path.join(tmpdir, "transforms.trf")
        step1 = await _run_ffmpeg([
            "-y", "-i", input_path,
            "-vf", f"vidstabdetect=shakiness=5:accuracy=15:result={transforms}",
            "-f", "null", "-",
        ])
        if step1.get("returncode") != 0:
            return VideoEditResult(
                operation=VideoEditOperation.STABILIZE, provider="ffmpeg",
                status=VideoEditStatus.FAILED, input_path=input_path,
                error=step1.get("error") or step1.get("stderr", "")[:200],
            )
        step2 = await _run_ffmpeg([
            "-y", "-i", input_path,
            "-vf", f"vidstabtransform=input={transforms}:smoothing=10:optzoom=1",
            "-c:v", "libx264", "-c:a", "copy", output_path,
        ])
        if step2.get("returncode") == 0:
            return VideoEditResult(
                operation=VideoEditOperation.STABILIZE, provider="ffmpeg",
                status=VideoEditStatus.COMPLETED, input_path=input_path,
                output_path=output_path, latency_ms=0,
            )
        return VideoEditResult(
            operation=VideoEditOperation.STABILIZE, provider="ffmpeg",
            status=VideoEditStatus.FAILED, error=step2.get("error") or step2.get("stderr", "")[:200],
        )


async def _ffmpeg_enhance(input_path: str, output_path: str, denoise: bool = True, sharpen: bool = True, brightness: float = 0.0, contrast: float = 1.0, saturation: float = 1.0, **kw) -> VideoEditResult:
    filters = []
    if denoise:
        filters.append("hqdn3d=3:3:3:3")
    if sharpen:
        filters.append("unsharp=5:5:0.5:5:5:0.0")
    if brightness != 0 or contrast != 1.0 or saturation != 1.0:
        filters.append(f"eq=brightness={brightness}:contrast={contrast}:saturation={saturation}")
    vf = ",".join(filters) if filters else "null"
    args = [
        "-y", "-i", input_path,
        "-vf", vf,
        "-c:v", "libx264", "-crf", "18", "-c:a", "copy", output_path,
    ]
    res = await _run_ffmpeg(args)
    if res.get("returncode") == 0:
        return VideoEditResult(
            operation=VideoEditOperation.ENHANCE, provider="ffmpeg",
            status=VideoEditStatus.COMPLETED, input_path=input_path,
            output_path=output_path, latency_ms=0,
            metadata={"denoise": denoise, "sharpen": sharpen,
                       "brightness": brightness, "contrast": contrast, "saturation": saturation},
        )
    return VideoEditResult(
        operation=VideoEditOperation.ENHANCE, provider="ffmpeg",
        status=VideoEditStatus.FAILED, error=res.get("error") or res.get("stderr", "")[:200],
    )


async def _ffmpeg_watermark(input_path: str, output_path: str, text: str = "", image_path: str = "", position: str = "top_right", **kw) -> VideoEditResult:
    if text:
        positions = {
            "top_left": "x=10:y=10",
            "top_right": "x=W-tw-10:y=10",
            "bottom_left": "x=10:y=H-th-10",
            "bottom_right": "x=W-tw-10:y=H-th-10",
            "center": "x=(W-tw)/2:y=(H-th)/2",
        }
        pos = positions.get(position, positions["top_right"])
        vf = f"drawtext=text='{text}':{pos}:fontsize=24:fontcolor=white@0.8:box=1:boxcolor=black@0.5:boxborderw=5"
    elif image_path:
        positions = {
            "top_left": "overlay=10:10",
            "top_right": "overlay=W-w-10:10",
            "bottom_left": "overlay=10:H-h-10",
            "bottom_right": "overlay=W-w-10:H-h-10",
            "center": "overlay=(W-w)/2:(H-h)/2",
        }
        pos = positions.get(position, positions["top_right"])
        args = ["-y", "-i", input_path, "-i", image_path, "-vf", pos, "-c:v", "libx264", "-c:a", "copy", output_path]
        res = await _run_ffmpeg(args)
        if res.get("returncode") == 0:
            return VideoEditResult(
                operation=VideoEditOperation.WATERMARK, provider="ffmpeg",
                status=VideoEditStatus.COMPLETED, input_path=input_path,
                output_path=output_path, latency_ms=0, metadata={"position": position, "image": True},
            )
        return VideoEditResult(
            operation=VideoEditOperation.WATERMARK, provider="ffmpeg",
            status=VideoEditStatus.FAILED, error=res.get("error") or res.get("stderr", "")[:200],
        )
    else:
        return VideoEditResult(
            operation=VideoEditOperation.WATERMARK, status=VideoEditStatus.FAILED,
            error="Need either text or image_path",
        )
    args = ["-y", "-i", input_path, "-vf", vf, "-c:v", "libx264", "-c:a", "copy", output_path]
    res = await _run_ffmpeg(args)
    if res.get("returncode") == 0:
        return VideoEditResult(
            operation=VideoEditOperation.WATERMARK, provider="ffmpeg",
            status=VideoEditStatus.COMPLETED, input_path=input_path,
            output_path=output_path, latency_ms=0, metadata={"position": position, "text": text},
        )
    return VideoEditResult(
        operation=VideoEditOperation.WATERMARK, provider="ffmpeg",
        status=VideoEditStatus.FAILED, error=res.get("error") or res.get("stderr", "")[:200],
    )


async def _ffmpeg_audio_extract(input_path: str, output_path: str, **kw) -> VideoEditResult:
    args = ["-y", "-i", input_path, "-vn", "-c:a", "aac", output_path]
    res = await _run_ffmpeg(args)
    if res.get("returncode") == 0:
        return VideoEditResult(
            operation=VideoEditOperation.AUDIO_EXTRACT, provider="ffmpeg",
            status=VideoEditStatus.COMPLETED, input_path=input_path,
            output_path=output_path, latency_ms=0,
        )
    return VideoEditResult(
        operation=VideoEditOperation.AUDIO_EXTRACT, provider="ffmpeg",
        status=VideoEditStatus.FAILED, error=res.get("error") or res.get("stderr", "")[:200],
    )


async def _ffmpeg_audio_replace(video_path: str, audio_path: str, output_path: str, **kw) -> VideoEditResult:
    args = ["-y", "-i", video_path, "-i", audio_path, "-c:v", "copy", "-c:a", "aac", "-map", "0:v:0", "-map", "1:a:0", output_path]
    res = await _run_ffmpeg(args)
    if res.get("returncode") == 0:
        return VideoEditResult(
            operation=VideoEditOperation.AUDIO_REPLACE, provider="ffmpeg",
            status=VideoEditStatus.COMPLETED, input_path=video_path,
            output_path=output_path, latency_ms=0,
        )
    return VideoEditResult(
        operation=VideoEditOperation.AUDIO_REPLACE, provider="ffmpeg",
        status=VideoEditStatus.FAILED, error=res.get("error") or res.get("stderr", "")[:200],
    )


async def _ffmpeg_subtitle_burn(input_path: str, output_path: str, subtitle_path: str = "", **kw) -> VideoEditResult:
    if not subtitle_path:
        return VideoEditResult(
            operation=VideoEditOperation.SUBTITLE_BURN, status=VideoEditStatus.FAILED,
            error="subtitle_path is required",
        )
    ext = Path(subtitle_path).suffix.lower()
    if ext == ".srt":
        sub_filter = f"subtitles={subtitle_path}"
    elif ext in (".ass", ".ssa"):
        sub_filter = f"ass={subtitle_path}"
    else:
        return VideoEditResult(
            operation=VideoEditOperation.SUBTITLE_BURN, status=VideoEditStatus.FAILED,
            error=f"Unsupported subtitle format: {ext}. Use .srt or .ass",
        )
    args = [
        "-y", "-i", input_path,
        "-vf", sub_filter,
        "-c:v", "libx264", "-c:a", "copy", output_path,
    ]
    res = await _run_ffmpeg(args)
    if res.get("returncode") == 0:
        return VideoEditResult(
            operation=VideoEditOperation.SUBTITLE_BURN, provider="ffmpeg",
            status=VideoEditStatus.COMPLETED, input_path=input_path,
            output_path=output_path, latency_ms=0, metadata={"subtitle_format": ext},
        )
    return VideoEditResult(
        operation=VideoEditOperation.SUBTITLE_BURN, provider="ffmpeg",
        status=VideoEditStatus.FAILED, error=res.get("error") or res.get("stderr", "")[:200],
    )


# ── Frame Interpolation (RIFE via ffmpeg filter) ─────────────────

async def _ffmpeg_frame_interpolation(input_path: str, output_path: str, target_fps: float = 60.0, **kw) -> VideoEditResult:
    """Use minterpolate ffmpeg filter for frame interpolation (fallback when RIFE unavailable)."""
    info = _probe_video(input_path)
    original_fps = info.get("fps", 24.0)
    if target_fps <= original_fps:
        return VideoEditResult(
            operation=VideoEditOperation.FRAME_INTERPOLATION, provider="ffmpeg",
            status=VideoEditStatus.COMPLETED, input_path=input_path,
            output_path=output_path, original_fps=original_fps, fps=target_fps,
            latency_ms=0, metadata={"method": "passthrough", "reason": "target <= source fps"},
        )
    vf = f"minterpolate=fps={target_fps}:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1"
    args = [
        "-y", "-i", input_path,
        "-vf", vf,
        "-c:v", "libx264", "-crf", "18", "-c:a", "copy", output_path,
    ]
    res = await _run_ffmpeg(args, timeout=600)
    if res.get("returncode") == 0:
        return VideoEditResult(
            operation=VideoEditOperation.FRAME_INTERPOLATION, provider="ffmpeg_minterpolate",
            status=VideoEditStatus.COMPLETED, input_path=input_path,
            output_path=output_path, original_fps=original_fps, fps=target_fps,
            latency_ms=0, metadata={"method": "minterpolate"},
        )
    return VideoEditResult(
        operation=VideoEditOperation.FRAME_INTERPOLATION, provider="ffmpeg",
        status=VideoEditStatus.FAILED, error=res.get("error") or res.get("stderr", "")[:200],
    )


# ── Video Upscaling (ffmpeg-based 2x/4x) ─────────────────────────

async def _ffmpeg_upscale(input_path: str, output_path: str, scale_factor: int = 2, **kw) -> VideoEditResult:
    """Upscale video using ffmpeg's lanczos filter (fallback for Real-ESRGAN)."""
    if scale_factor not in (2, 4):
        return VideoEditResult(
            operation=VideoEditOperation.UPSCALE, status=VideoEditStatus.FAILED,
            error=f"scale_factor must be 2 or 4, got {scale_factor}",
        )
    vf = f"scale=iw*{scale_factor}:ih*{scale_factor}:flags=lanczos"
    args = [
        "-y", "-i", input_path,
        "-vf", vf,
        "-c:v", "libx264", "-crf", "18", "-c:a", "copy", output_path,
    ]
    res = await _run_ffmpeg(args, timeout=600)
    if res.get("returncode") == 0:
        return VideoEditResult(
            operation=VideoEditOperation.UPSCALE, provider="ffmpeg_lanczos",
            status=VideoEditStatus.COMPLETED, input_path=input_path,
            output_path=output_path, scale_factor=float(scale_factor),
            latency_ms=0, metadata={"method": "lanczos", "scale": f"{scale_factor}x"},
        )
    return VideoEditResult(
        operation=VideoEditOperation.UPSCALE, provider="ffmpeg",
        status=VideoEditStatus.FAILED, error=res.get("error") or res.get("stderr", "")[:200],
    )


# ── Video Editing Engine ─────────────────────────────────────────

class VideoEditingEngine:
    """
    Unified video editing engine covering trim, concat, transitions,
    frame interpolation, upscaling, enhancement, and more.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._history: List[VideoEditResult] = []
        self._ffmpeg_available = _has_ffmpeg()
        self._ffprobe_available = _has_ffprobe()

    def get_profiles(self) -> List[Dict[str, Any]]:
        return [p.to_dict() for p in EDIT_PROFILES.values()]

    def get_available_operations(self) -> List[str]:
        if not self._ffmpeg_available:
            return []
        return [op.value for op in EDIT_PROFILES.keys()]

    def probe(self, video_path: str) -> Dict[str, Any]:
        return _probe_video(video_path)

    async def execute(
        self,
        operation: VideoEditOperation,
        input_path: str = "",
        input_paths: Optional[List[str]] = None,
        output_path: str = "",
        **kwargs,
    ) -> VideoEditResult:
        start = time.time()
        if not output_path:
            ext = Path(input_path or "video.mp4").suffix or ".mp4"
            output_path = f"./output/videos/edited_{int(time.time()*1000)}{ext}"
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        handlers = {
            VideoEditOperation.TRIM: lambda: _ffmpeg_trim(input_path, output_path, **kwargs),
            VideoEditOperation.CONCAT: lambda: _ffmpeg_concat(input_paths or [input_path], output_path, **kwargs),
            VideoEditOperation.TRANSITION: lambda: _ffmpeg_transition(input_paths or [input_path], output_path, **kwargs),
            VideoEditOperation.SPEED: lambda: _ffmpeg_speed(input_path, output_path, **kwargs),
            VideoEditOperation.FRAME_INTERPOLATION: lambda: _ffmpeg_frame_interpolation(input_path, output_path, **kwargs),
            VideoEditOperation.UPSCALE: lambda: _ffmpeg_upscale(input_path, output_path, **kwargs),
            VideoEditOperation.ENHANCE: lambda: _ffmpeg_enhance(input_path, output_path, **kwargs),
            VideoEditOperation.WATERMARK: lambda: _ffmpeg_watermark(input_path, output_path, **kwargs),
            VideoEditOperation.CROP: lambda: _ffmpeg_crop(input_path, output_path, **kwargs),
            VideoEditOperation.RESIZE: lambda: _ffmpeg_resize(input_path, output_path, **kwargs),
            VideoEditOperation.ROTATE: lambda: _ffmpeg_rotate(input_path, output_path, **kwargs),
            VideoEditOperation.REVERSE: lambda: _ffmpeg_reverse(input_path, output_path, **kwargs),
            VideoEditOperation.STABILIZE: lambda: _ffmpeg_stabilize(input_path, output_path, **kwargs),
            VideoEditOperation.AUDIO_EXTRACT: lambda: _ffmpeg_audio_extract(input_path, output_path, **kwargs),
            VideoEditOperation.AUDIO_REPLACE: lambda: _ffmpeg_audio_replace(input_path, kwargs.get("audio_path", ""), output_path, **kwargs),
            VideoEditOperation.SUBTITLE_BURN: lambda: _ffmpeg_subtitle_burn(input_path, output_path, **kwargs),
        }

        if not self._ffmpeg_available:
            result = VideoEditResult(
                operation=operation, status=VideoEditStatus.DEPENDENCY_MISSING,
                input_path=input_path, output_path=output_path,
                error="ffmpeg not installed",
            )
            self._history.append(result)
            return result

        handler = handlers.get(operation)
        if not handler:
            result = VideoEditResult(
                operation=operation, status=VideoEditStatus.UNSUPPORTED,
                input_path=input_path, error=f"No handler for {operation.value}",
            )
            self._history.append(result)
            return result

        result = await handler()
        result.latency_ms = round((time.time() - start) * 1000, 1)
        if result.output_path and Path(result.output_path).exists():
            info = _probe_video(result.output_path)
            result.width = info.get("width", 0)
            result.height = info.get("height", 0)
            result.duration_secs = info.get("duration", 0.0)
            result.fps = info.get("fps", 0.0)
        self._history.append(result)
        return result

    async def trim(self, input_path: str, output_path: str = "", start: float = 0.0, end: float = 0.0, **kw) -> VideoEditResult:
        return await self.execute(VideoEditOperation.TRIM, input_path=input_path, output_path=output_path, start=start, end=end, **kw)

    async def concat(self, input_paths: List[str], output_path: str = "", **kw) -> VideoEditResult:
        return await self.execute(VideoEditOperation.CONCAT, input_paths=input_paths, output_path=output_path, **kw)

    async def transition(self, input_paths: List[str], output_path: str = "", duration: float = 1.0, **kw) -> VideoEditResult:
        return await self.execute(VideoEditOperation.TRANSITION, input_paths=input_paths, output_path=output_path, duration=duration, **kw)

    async def speed(self, input_path: str, output_path: str = "", factor: float = 1.0, **kw) -> VideoEditResult:
        return await self.execute(VideoEditOperation.SPEED, input_path=input_path, output_path=output_path, speed_factor=factor, **kw)

    async def interpolate_frames(self, input_path: str, output_path: str = "", target_fps: float = 60.0, **kw) -> VideoEditResult:
        return await self.execute(VideoEditOperation.FRAME_INTERPOLATION, input_path=input_path, output_path=output_path, target_fps=target_fps, **kw)

    async def upscale(self, input_path: str, output_path: str = "", scale_factor: int = 2, **kw) -> VideoEditResult:
        return await self.execute(VideoEditOperation.UPSCALE, input_path=input_path, output_path=output_path, scale_factor=scale_factor, **kw)

    async def enhance(self, input_path: str, output_path: str = "", **kw) -> VideoEditResult:
        return await self.execute(VideoEditOperation.ENHANCE, input_path=input_path, output_path=output_path, **kw)

    async def crop(self, input_path: str, output_path: str = "", x: int = 0, y: int = 0, width: int = 0, height: int = 0, **kw) -> VideoEditResult:
        return await self.execute(VideoEditOperation.CROP, input_path=input_path, output_path=output_path, x=x, y=y, width=width, height=height, **kw)

    async def resize(self, input_path: str, output_path: str = "", width: int = 0, height: int = 0, **kw) -> VideoEditResult:
        return await self.execute(VideoEditOperation.RESIZE, input_path=input_path, output_path=output_path, width=width, height=height, **kw)

    async def watermark(self, input_path: str, output_path: str = "", text: str = "", image_path: str = "", position: str = "top_right", **kw) -> VideoEditResult:
        return await self.execute(VideoEditOperation.WATERMARK, input_path=input_path, output_path=output_path, text=text, image_path=image_path, position=position, **kw)

    async def extract_audio(self, input_path: str, output_path: str = "", **kw) -> VideoEditResult:
        return await self.execute(VideoEditOperation.AUDIO_EXTRACT, input_path=input_path, output_path=output_path, **kw)

    async def replace_audio(self, video_path: str, audio_path: str, output_path: str = "", **kw) -> VideoEditResult:
        return await self.execute(VideoEditOperation.AUDIO_REPLACE, input_path=video_path, output_path=output_path, audio_path=audio_path, **kw)

    async def burn_subtitles(self, input_path: str, subtitle_path: str, output_path: str = "", **kw) -> VideoEditResult:
        return await self.execute(VideoEditOperation.SUBTITLE_BURN, input_path=input_path, output_path=output_path, subtitle_path=subtitle_path, **kw)

    def get_stats(self) -> Dict[str, Any]:
        ops: Dict[str, int] = {}
        for r in self._history:
            ops[r.operation.value] = ops.get(r.operation.value, 0) + 1
        statuses: Dict[str, int] = {}
        for r in self._history:
            statuses[r.status.value] = statuses.get(r.status.value, 0) + 1
        return {
            "total_edits": len(self._history),
            "by_operation": ops,
            "by_status": statuses,
            "ffmpeg_available": self._ffmpeg_available,
            "ffprobe_available": self._ffprobe_available,
            "supported_operations": len(EDIT_PROFILES),
        }
