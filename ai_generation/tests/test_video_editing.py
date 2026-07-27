"""
Tests for VID-05/06/07 — Video Editing, Frame Interpolation, Video Upscaling.
"""
import pytest


# ── Enum Tests ────────────────────────────────────────────────────

def test_video_edit_operation_enum():
    from ai_generation.video_editing import VideoEditOperation
    assert VideoEditOperation.TRIM.value == "trim"
    assert VideoEditOperation.CONCAT.value == "concat"
    assert VideoEditOperation.TRANSITION.value == "transition"
    assert VideoEditOperation.SPEED.value == "speed"
    assert VideoEditOperation.FRAME_INTERPOLATION.value == "frame_interpolation"
    assert VideoEditOperation.UPSCALE.value == "upscale"
    assert VideoEditOperation.ENHANCE.value == "enhance"
    assert VideoEditOperation.WATERMARK.value == "watermark"
    assert VideoEditOperation.CROP.value == "crop"
    assert VideoEditOperation.RESIZE.value == "resize"
    assert VideoEditOperation.ROTATE.value == "rotate"
    assert VideoEditOperation.REVERSE.value == "reverse"
    assert VideoEditOperation.STABILIZE.value == "stabilize"
    assert VideoEditOperation.AUDIO_EXTRACT.value == "audio_extract"
    assert VideoEditOperation.AUDIO_REPLACE.value == "audio_replace"
    assert VideoEditOperation.SUBTITLE_BURN.value == "subtitle_burn"


def test_video_edit_status_enum():
    from ai_generation.video_editing import VideoEditStatus
    assert VideoEditStatus.PENDING.value == "pending"
    assert VideoEditStatus.COMPLETED.value == "completed"
    assert VideoEditStatus.FAILED.value == "failed"
    assert VideoEditStatus.UNSUPPORTED.value == "unsupported"
    assert VideoEditStatus.DEPENDENCY_MISSING.value == "dependency_missing"


def test_interpolation_model_enum():
    from ai_generation.video_editing import InterpolationModel
    assert InterpolationModel.RIFE.value == "rife"
    assert InterpolationModel.FILM.value == "film"
    assert InterpolationModel.OPENCV.value == "opencv"


def test_upscale_model_enum():
    from ai_generation.video_editing import UpscaleModel
    assert UpscaleModel.REAL_ESRGAN.value == "real_esrgan"
    assert UpscaleModel.LANCZOS.value == "lanctos"


# ── Result Serialization Tests ────────────────────────────────────

def test_video_edit_result_serialization():
    from ai_generation.video_editing import VideoEditResult, VideoEditOperation, VideoEditStatus
    r = VideoEditResult(
        operation=VideoEditOperation.TRIM,
        provider="ffmpeg",
        status=VideoEditStatus.COMPLETED,
        input_path="input.mp4",
        output_path="output.mp4",
        width=1920, height=1080, duration_secs=10.0, fps=30.0,
    )
    d = r.to_dict()
    assert d["operation"] == "trim"
    assert d["provider"] == "ffmpeg"
    assert d["status"] == "completed"
    assert d["width"] == 1920
    assert d["height"] == 1080
    assert d["duration_secs"] == 10.0
    assert d["fps"] == 30.0


def test_video_edit_result_defaults():
    from ai_generation.video_editing import VideoEditResult, VideoEditOperation, VideoEditStatus
    r = VideoEditResult()
    assert r.operation == VideoEditOperation.TRIM
    assert r.status == VideoEditStatus.PENDING
    assert r.latency_ms == 0.0
    assert r.error is None
    d = r.to_dict()
    assert "created_at" in d


# ── Profile Tests ─────────────────────────────────────────────────

def test_edit_profiles_complete():
    from ai_generation.video_editing import EDIT_PROFILES, VideoEditOperation
    assert len(EDIT_PROFILES) == 16
    for op in VideoEditOperation:
        assert op in EDIT_PROFILES, f"Missing profile for {op.value}"


def test_edit_profile_serialization():
    from ai_generation.video_editing import EDIT_PROFILES, VideoEditOperation
    p = EDIT_PROFILES[VideoEditOperation.TRIM]
    d = p.to_dict()
    assert d["operation"] == "trim"
    assert d["requires_ffmpeg"] is True
    assert "mp4" in d["supported_formats"]


def test_edit_profile_concat_multi_input():
    from ai_generation.video_editing import EDIT_PROFILES, VideoEditOperation
    p = EDIT_PROFILES[VideoEditOperation.CONCAT]
    assert p.min_inputs == 2
    assert p.max_inputs == 50


def test_edit_profile_transition_multi_input():
    from ai_generation.video_editing import EDIT_PROFILES, VideoEditOperation
    p = EDIT_PROFILES[VideoEditOperation.TRANSITION]
    assert p.min_inputs == 2
    assert p.max_inputs == 20


def test_edit_profile_interpolation_requires_model():
    from ai_generation.video_editing import EDIT_PROFILES, VideoEditOperation
    p = EDIT_PROFILES[VideoEditOperation.FRAME_INTERPOLATION]
    assert p.requires_model is True
    assert p.model_name == "rife"


def test_edit_profile_upscale_requires_model():
    from ai_generation.video_editing import EDIT_PROFILES, VideoEditOperation
    p = EDIT_PROFILES[VideoEditOperation.UPSCALE]
    assert p.requires_model is True
    assert p.model_name == "real_esrgan"


# ── Engine Tests ──────────────────────────────────────────────────

def test_video_editing_engine_import():
    from ai_generation.video_editing import VideoEditingEngine
    e = VideoEditingEngine()
    assert e is not None


def test_video_editing_engine_get_profiles():
    from ai_generation.video_editing import VideoEditingEngine
    e = VideoEditingEngine()
    profiles = e.get_profiles()
    assert len(profiles) == 16
    ops = [p["operation"] for p in profiles]
    assert "trim" in ops
    assert "frame_interpolation" in ops
    assert "upscale" in ops
    assert "enhance" in ops


def test_video_editing_engine_stats():
    from ai_generation.video_editing import VideoEditingEngine
    e = VideoEditingEngine()
    stats = e.get_stats()
    assert stats["total_edits"] == 0
    assert stats["supported_operations"] == 16
    assert "ffmpeg_available" in stats
    assert "ffprobe_available" in stats


def test_video_editing_engine_no_ffmpeg():
    from ai_generation.video_editing import VideoEditingEngine
    e = VideoEditingEngine()
    if not e._ffmpeg_available:
        ops = e.get_available_operations()
        assert ops == []


# ── Async Operation Tests ─────────────────────────────────────────

@pytest.mark.asyncio
async def test_trim_no_ffmpeg():
    from ai_generation.video_editing import VideoEditingEngine, VideoEditStatus
    e = VideoEditingEngine()
    if not e._ffmpeg_available:
        result = await e.trim("input.mp4", "output.mp4")
        assert result.status == VideoEditStatus.DEPENDENCY_MISSING
        assert "ffmpeg" in result.error.lower()


@pytest.mark.asyncio
async def test_concat_no_ffmpeg():
    from ai_generation.video_editing import VideoEditingEngine, VideoEditStatus
    e = VideoEditingEngine()
    if not e._ffmpeg_available:
        result = await e.concat(["a.mp4", "b.mp4"], "output.mp4")
        assert result.status == VideoEditStatus.DEPENDENCY_MISSING


@pytest.mark.asyncio
async def test_upscale_no_ffmpeg():
    from ai_generation.video_editing import VideoEditingEngine, VideoEditStatus
    e = VideoEditingEngine()
    if not e._ffmpeg_available:
        result = await e.upscale("input.mp4", "output.mp4", scale_factor=2)
        assert result.status == VideoEditStatus.DEPENDENCY_MISSING


@pytest.mark.asyncio
async def test_enhance_no_ffmpeg():
    from ai_generation.video_editing import VideoEditingEngine, VideoEditStatus
    e = VideoEditingEngine()
    if not e._ffmpeg_available:
        result = await e.enhance("input.mp4", "output.mp4")
        assert result.status == VideoEditStatus.DEPENDENCY_MISSING


@pytest.mark.asyncio
async def test_interpolate_no_ffmpeg():
    from ai_generation.video_editing import VideoEditingEngine, VideoEditStatus
    e = VideoEditingEngine()
    if not e._ffmpeg_available:
        result = await e.interpolate_frames("input.mp4", "output.mp4", target_fps=60.0)
        assert result.status == VideoEditStatus.DEPENDENCY_MISSING


@pytest.mark.asyncio
async def test_speed_no_ffmpeg():
    from ai_generation.video_editing import VideoEditingEngine, VideoEditStatus
    e = VideoEditingEngine()
    if not e._ffmpeg_available:
        result = await e.speed("input.mp4", "output.mp4", factor=2.0)
        assert result.status == VideoEditStatus.DEPENDENCY_MISSING


@pytest.mark.asyncio
async def test_crop_no_ffmpeg():
    from ai_generation.video_editing import VideoEditingEngine, VideoEditStatus
    e = VideoEditingEngine()
    if not e._ffmpeg_available:
        result = await e.crop("input.mp4", "output.mp4", x=10, y=10, width=640, height=480)
        assert result.status == VideoEditStatus.DEPENDENCY_MISSING


@pytest.mark.asyncio
async def test_resize_no_ffmpeg():
    from ai_generation.video_editing import VideoEditingEngine, VideoEditStatus
    e = VideoEditingEngine()
    if not e._ffmpeg_available:
        result = await e.resize("input.mp4", "output.mp4", width=1920, height=1080)
        assert result.status == VideoEditStatus.DEPENDENCY_MISSING


@pytest.mark.asyncio
async def test_watermark_no_ffmpeg():
    from ai_generation.video_editing import VideoEditingEngine, VideoEditStatus
    e = VideoEditingEngine()
    if not e._ffmpeg_available:
        result = await e.watermark("input.mp4", "output.mp4", text="Test")
        assert result.status == VideoEditStatus.DEPENDENCY_MISSING


@pytest.mark.asyncio
async def test_extract_audio_no_ffmpeg():
    from ai_generation.video_editing import VideoEditingEngine, VideoEditStatus
    e = VideoEditingEngine()
    if not e._ffmpeg_available:
        result = await e.extract_audio("input.mp4", "output.mp4")
        assert result.status == VideoEditStatus.DEPENDENCY_MISSING


# ── SDK Integration Tests ────────────────────────────────────────

def test_sdk_video_editing_import():
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    assert ai.video_editing is not None
    assert type(ai.video_editing).__name__ == "VideoEditingEngine"


def test_sdk_video_editing_stats():
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    stats = ai.video_editing.get_stats()
    assert "total_edits" in stats
    assert "supported_operations" in stats


def test_sdk_video_editing_profiles():
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    profiles = ai.video_editing.get_profiles()
    assert len(profiles) == 16


def test_sdk_video_edit_in_stats():
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    all_stats = ai.get_stats()
    assert "video_editing" in all_stats
    assert all_stats["video_editing"]["total_edits"] == 0


# ── MCP Tool Integration Tests ───────────────────────────────────

def test_mcp_video_edit_tools_exist():
    from ai_generation.mcp_tools import MCP_GENERATION_TOOLS
    assert "edit_video" in MCP_GENERATION_TOOLS
    assert "trim_video" in MCP_GENERATION_TOOLS
    assert "concat_videos" in MCP_GENERATION_TOOLS
    assert "interpolate_video_frames" in MCP_GENERATION_TOOLS
    assert "upscale_video" in MCP_GENERATION_TOOLS
    assert "enhance_video" in MCP_GENERATION_TOOLS
    assert "get_video_edit_profiles" in MCP_GENERATION_TOOLS
    assert "probe_video" in MCP_GENERATION_TOOLS


def test_mcp_edit_video_schema():
    from ai_generation.mcp_tools import MCP_GENERATION_TOOLS
    tool = MCP_GENERATION_TOOLS["edit_video"]
    assert tool["name"] == "edit_video"
    schema = tool["inputSchema"]
    assert "operation" in schema["properties"]
    assert "input_path" in schema["properties"]
    assert "input_paths" in schema["properties"]


def test_mcp_trim_video_schema():
    from ai_generation.mcp_tools import MCP_GENERATION_TOOLS
    tool = MCP_GENERATION_TOOLS["trim_video"]
    schema = tool["inputSchema"]
    assert "input_path" in schema["properties"]
    assert "start" in schema["properties"]
    assert "end" in schema["properties"]


def test_mcp_interpolate_video_schema():
    from ai_generation.mcp_tools import MCP_GENERATION_TOOLS
    tool = MCP_GENERATION_TOOLS["interpolate_video_frames"]
    schema = tool["inputSchema"]
    assert "input_path" in schema["properties"]
    assert "target_fps" in schema["properties"]


def test_mcp_upscale_video_schema():
    from ai_generation.mcp_tools import MCP_GENERATION_TOOLS
    tool = MCP_GENERATION_TOOLS["upscale_video"]
    schema = tool["inputSchema"]
    assert "input_path" in schema["properties"]
    assert "scale_factor" in schema["properties"]


def test_mcp_enhance_video_schema():
    from ai_generation.mcp_tools import MCP_GENERATION_TOOLS
    tool = MCP_GENERATION_TOOLS["enhance_video"]
    schema = tool["inputSchema"]
    assert "input_path" in schema["properties"]
    assert "denoise" in schema["properties"]
    assert "sharpen" in schema["properties"]


@pytest.mark.asyncio
async def test_mcp_edit_video_handler_import():
    from ai_generation.mcp_tools import MCPGenerationTools
    mcp = MCPGenerationTools()
    assert hasattr(mcp, "_handle_edit_video")
    assert hasattr(mcp, "_handle_trim_video")
    assert hasattr(mcp, "_handle_concat_videos")
    assert hasattr(mcp, "_handle_interpolate_frames")
    assert hasattr(mcp, "_handle_upscale_video")
    assert hasattr(mcp, "_handle_enhance_video")
    assert hasattr(mcp, "_handle_video_edit_profiles")
    assert hasattr(mcp, "_handle_probe_video")


@pytest.mark.asyncio
async def test_mcp_get_video_edit_profiles():
    from ai_generation.mcp_tools import MCPGenerationTools
    mcp = MCPGenerationTools()
    result = await mcp.handle("get_video_edit_profiles", {})
    assert "profiles" in result
    assert "available" in result
    assert len(result["profiles"]) == 16


@pytest.mark.asyncio
async def test_mcp_edit_video_no_ffmpeg():
    from ai_generation.mcp_tools import MCPGenerationTools
    mcp = MCPGenerationTools()
    if not mcp.sdk.video_editing._ffmpeg_available:
        result = await mcp.handle("edit_video", {"operation": "trim", "input_path": "test.mp4"})
        assert result["status"] == "dependency_missing"


@pytest.mark.asyncio
async def test_mcp_trim_video_no_ffmpeg():
    from ai_generation.mcp_tools import MCPGenerationTools
    mcp = MCPGenerationTools()
    if not mcp.sdk.video_editing._ffmpeg_available:
        result = await mcp.handle("trim_video", {"input_path": "test.mp4"})
        assert result["status"] == "dependency_missing"


@pytest.mark.asyncio
async def test_mcp_upscale_video_no_ffmpeg():
    from ai_generation.mcp_tools import MCPGenerationTools
    mcp = MCPGenerationTools()
    if not mcp.sdk.video_editing._ffmpeg_available:
        result = await mcp.handle("upscale_video", {"input_path": "test.mp4"})
        assert result["status"] == "dependency_missing"


@pytest.mark.asyncio
async def test_mcp_enhance_video_no_ffmpeg():
    from ai_generation.mcp_tools import MCPGenerationTools
    mcp = MCPGenerationTools()
    if not mcp.sdk.video_editing._ffmpeg_available:
        result = await mcp.handle("enhance_video", {"input_path": "test.mp4"})
        assert result["status"] == "dependency_missing"


@pytest.mark.asyncio
async def test_mcp_interpolate_no_ffmpeg():
    from ai_generation.mcp_tools import MCPGenerationTools
    mcp = MCPGenerationTools()
    if not mcp.sdk.video_editing._ffmpeg_available:
        result = await mcp.handle("interpolate_video_frames", {"input_path": "test.mp4"})
        assert result["status"] == "dependency_missing"
