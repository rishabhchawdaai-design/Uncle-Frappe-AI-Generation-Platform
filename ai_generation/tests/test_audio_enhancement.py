"""Tests for AUD-09 — Audio Enhancement & Restoration."""
import pytest


def test_audio_enhance_operation_enum():
    from ai_generation.audio_enhancement import AudioEnhanceOperation
    assert AudioEnhanceOperation.DENOISE.value == "denoise"
    assert AudioEnhanceOperation.NORMALIZE.value == "normalize"
    assert AudioEnhanceOperation.EQUALIZE.value == "equalize"
    assert AudioEnhanceOperation.REMOVE_SILENCE.value == "remove_silence"
    assert AudioEnhanceOperation.CONVERT_FORMAT.value == "convert_format"
    assert AudioEnhanceOperation.RESAMPLE.value == "resample"
    assert AudioEnhanceOperation.COMPRESS.value == "compress"
    assert AudioEnhanceOperation.LIMIT.value == "limit"
    assert AudioEnhanceOperation.FADE_IN.value == "fade_in"
    assert AudioEnhanceOperation.FADE_OUT.value == "fade_out"
    assert AudioEnhanceOperation.TRIM_SILENCE.value == "trim_silence"
    assert AudioEnhanceOperation.SPEED.value == "speed"
    assert AudioEnhanceOperation.PITCH.value == "pitch"
    assert AudioEnhanceOperation.REVERSE.value == "reverse"
    assert AudioEnhanceOperation.CONCAT.value == "concat"
    assert AudioEnhanceOperation.MIX.value == "mix"
    assert AudioEnhanceOperation.GAIN.value == "gain"


def test_audio_enhance_status_enum():
    from ai_generation.audio_enhancement import AudioEnhanceStatus
    assert AudioEnhanceStatus.COMPLETED.value == "completed"
    assert AudioEnhanceStatus.FAILED.value == "failed"
    assert AudioEnhanceStatus.DEPENDENCY_MISSING.value == "dependency_missing"


def test_audio_enhance_result_serialization():
    from ai_generation.audio_enhancement import AudioEnhanceResult, AudioEnhanceOperation, AudioEnhanceStatus
    r = AudioEnhanceResult(
        operation=AudioEnhanceOperation.DENOISE,
        provider="ffmpeg", status=AudioEnhanceStatus.COMPLETED,
        input_path="in.wav", output_path="out.wav",
    )
    d = r.to_dict()
    assert d["operation"] == "denoise"
    assert d["provider"] == "ffmpeg"
    assert d["status"] == "completed"


def test_audio_enhancement_engine_import():
    from ai_generation.audio_enhancement import AudioEnhancementEngine
    e = AudioEnhancementEngine()
    assert e is not None


def test_audio_enhancement_engine_stats():
    from ai_generation.audio_enhancement import AudioEnhancementEngine
    e = AudioEnhancementEngine()
    stats = e.get_stats()
    assert stats["total_enhancements"] == 0
    assert "supported_operations" in stats


def test_audio_enhancement_no_ffmpeg():
    from ai_generation.audio_enhancement import AudioEnhancementEngine
    e = AudioEnhancementEngine()
    if not e._ffmpeg_available:
        assert e.get_available_operations() == []


@pytest.mark.asyncio
async def test_denoise_no_ffmpeg():
    from ai_generation.audio_enhancement import AudioEnhancementEngine, AudioEnhanceStatus
    e = AudioEnhancementEngine()
    if not e._ffmpeg_available:
        result = await e.denoise("input.wav")
        assert result.status == AudioEnhanceStatus.DEPENDENCY_MISSING


@pytest.mark.asyncio
async def test_normalize_no_ffmpeg():
    from ai_generation.audio_enhancement import AudioEnhancementEngine, AudioEnhanceStatus
    e = AudioEnhancementEngine()
    if not e._ffmpeg_available:
        result = await e.normalize("input.wav")
        assert result.status == AudioEnhanceStatus.DEPENDENCY_MISSING


@pytest.mark.asyncio
async def test_convert_no_ffmpeg():
    from ai_generation.audio_enhancement import AudioEnhancementEngine, AudioEnhanceStatus
    e = AudioEnhancementEngine()
    if not e._ffmpeg_available:
        result = await e.convert_format("input.wav", format="mp3")
        assert result.status == AudioEnhanceStatus.DEPENDENCY_MISSING


# ── SDK Integration ──

def test_sdk_audio_enhancement_import():
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    assert ai.audio_enhancement is not None
    assert type(ai.audio_enhancement).__name__ == "AudioEnhancementEngine"


def test_sdk_audio_enhancement_in_stats():
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    stats = ai.get_stats()
    assert "audio_enhancement" in stats


# ── MCP Tools ──

def test_mcp_audio_enhance_tools_exist():
    from ai_generation.mcp_tools import MCP_GENERATION_TOOLS
    assert "enhance_audio" in MCP_GENERATION_TOOLS
    assert "denoise_audio" in MCP_GENERATION_TOOLS
    assert "normalize_audio" in MCP_GENERATION_TOOLS
    assert "convert_audio" in MCP_GENERATION_TOOLS
    assert "mix_audio" in MCP_GENERATION_TOOLS
    assert "concat_audio" in MCP_GENERATION_TOOLS


def test_mcp_enhance_audio_schema():
    from ai_generation.mcp_tools import MCP_GENERATION_TOOLS
    tool = MCP_GENERATION_TOOLS["enhance_audio"]
    schema = tool["inputSchema"]
    assert "operation" in schema["properties"]
    assert "input_path" in schema["properties"]


def test_mcp_denoise_audio_schema():
    from ai_generation.mcp_tools import MCP_GENERATION_TOOLS
    tool = MCP_GENERATION_TOOLS["denoise_audio"]
    schema = tool["inputSchema"]
    assert "input_path" in schema["properties"]
    assert "strength" in schema["properties"]


@pytest.mark.asyncio
async def test_mcp_enhance_audio_handler():
    from ai_generation.mcp_tools import MCPGenerationTools
    mcp = MCPGenerationTools()
    assert hasattr(mcp, "_handle_enhance_audio")


@pytest.mark.asyncio
async def test_mcp_denoise_no_ffmpeg():
    from ai_generation.mcp_tools import MCPGenerationTools
    mcp = MCPGenerationTools()
    if not mcp.sdk.audio_enhancement._ffmpeg_available:
        result = await mcp.handle("denoise_audio", {"input_path": "test.wav"})
        assert result["status"] == "dependency_missing"
