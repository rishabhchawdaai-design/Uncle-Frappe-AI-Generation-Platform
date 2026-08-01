"""Tests for AUD-07/08 — Music & SFX Generation."""
import pytest


def test_music_task_enum():
    from ai_generation.music_generation import MusicTask
    assert MusicTask.TEXT_TO_MUSIC.value == "text_to_music"
    assert MusicTask.TEXT_TO_SFX.value == "text_to_sfx"
    assert MusicTask.MELODY_CONDITIONED.value == "melody_conditioned"


def test_music_gen_status_enum():
    from ai_generation.music_generation import MusicGenStatus
    assert MusicGenStatus.COMPLETED.value == "completed"
    assert MusicGenStatus.FAILED.value == "failed"
    assert MusicGenStatus.DEPENDENCY_MISSING.value == "dependency_missing"


def test_musicgen_model_enum():
    from ai_generation.music_generation import MusicGenModel
    assert MusicGenModel.SMALL.value == "facebook/musicgen-small"
    assert MusicGenModel.LARGE.value == "facebook/musicgen-large"


def test_audiogen_model_enum():
    from ai_generation.music_generation import AudioGenModel
    assert AudioGenModel.SMALL.value == "facebook/audiogen-small"


def test_music_profiles():
    from ai_generation.music_generation import MUSIC_PROFILES
    assert len(MUSIC_PROFILES) == 7
    music_profiles = [p for p in MUSIC_PROFILES if p.task.value == "text_to_music"]
    sfx_profiles = [p for p in MUSIC_PROFILES if p.task.value == "text_to_sfx"]
    melody_profiles = [p for p in MUSIC_PROFILES if p.task.value == "melody_conditioned"]
    assert len(music_profiles) == 3
    assert len(sfx_profiles) == 3
    assert len(melody_profiles) == 1


def test_music_profile_serialization():
    from ai_generation.music_generation import MUSIC_PROFILES
    p = MUSIC_PROFILES[0]
    d = p.to_dict()
    assert "name" in d
    assert "task" in d
    assert "model" in d
    assert "license" in d


def test_music_gen_result_serialization():
    from ai_generation.music_generation import MusicGenResult, MusicTask, MusicGenStatus
    r = MusicGenResult(
        provider="audiocraft", task=MusicTask.TEXT_TO_MUSIC,
        status=MusicGenStatus.COMPLETED, prompt="happy jazz",
        output_path="out.wav", duration_secs=10.0,
    )
    d = r.to_dict()
    assert d["provider"] == "audiocraft"
    assert d["task"] == "text_to_music"
    assert d["prompt"] == "happy jazz"
    assert d["duration_secs"] == 10.0


def test_music_generation_engine_import():
    from ai_generation.music_generation import MusicGenerationEngine
    e = MusicGenerationEngine()
    assert e is not None


def test_music_generation_engine_profiles():
    from ai_generation.music_generation import MusicGenerationEngine
    e = MusicGenerationEngine()
    profiles = e.get_profiles()
    assert len(profiles) == 7


def test_music_generation_engine_models_for_task():
    from ai_generation.music_generation import MusicGenerationEngine, MusicTask
    e = MusicGenerationEngine()
    music = e.get_models_for_task(MusicTask.TEXT_TO_MUSIC)
    assert len(music) == 3
    sfx = e.get_models_for_task(MusicTask.TEXT_TO_SFX)
    assert len(sfx) == 3


def test_music_generation_engine_stats():
    from ai_generation.music_generation import MusicGenerationEngine
    e = MusicGenerationEngine()
    stats = e.get_stats()
    assert stats["total_generations"] == 0
    assert stats["profiles"] == 7


@pytest.mark.asyncio
async def test_music_generate_fails_no_server():
    from ai_generation.music_generation import MusicGenerationEngine, MusicGenStatus
    e = MusicGenerationEngine()
    result = await e.generate_music("happy jazz", duration_secs=5.0)
    # no local AudioCraft server -> actionable dependency_missing, not generic failure
    assert result.status == MusicGenStatus.DEPENDENCY_MISSING
    assert "AudioCraft server not reachable" in result.error


@pytest.mark.asyncio
async def test_sfx_generate_fails_no_server():
    from ai_generation.music_generation import MusicGenerationEngine, MusicGenStatus
    e = MusicGenerationEngine()
    result = await e.generate_sfx("thunder clap")
    assert result.status == MusicGenStatus.DEPENDENCY_MISSING
    assert "AudioCraft server not reachable" in result.error


# ── SDK Integration ──

def test_sdk_music_generation_import():
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    assert ai.music_generation is not None
    assert type(ai.music_generation).__name__ == "MusicGenerationEngine"


def test_sdk_music_generation_in_stats():
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    stats = ai.get_stats()
    assert "music_generation" in stats


# ── MCP Tools ──

def test_mcp_music_tools_exist():
    from ai_generation.mcp_tools import MCP_GENERATION_TOOLS
    assert "generate_music" in MCP_GENERATION_TOOLS
    assert "generate_sfx" in MCP_GENERATION_TOOLS
    assert "generate_melody" in MCP_GENERATION_TOOLS
    assert "get_music_profiles" in MCP_GENERATION_TOOLS


def test_mcp_generate_music_schema():
    from ai_generation.mcp_tools import MCP_GENERATION_TOOLS
    tool = MCP_GENERATION_TOOLS["generate_music"]
    schema = tool["inputSchema"]
    assert "prompt" in schema["properties"]
    assert "duration_secs" in schema["properties"]


def test_mcp_generate_sfx_schema():
    from ai_generation.mcp_tools import MCP_GENERATION_TOOLS
    tool = MCP_GENERATION_TOOLS["generate_sfx"]
    schema = tool["inputSchema"]
    assert "prompt" in schema["properties"]
    assert "duration_secs" in schema["properties"]


def test_mcp_generate_melody_schema():
    from ai_generation.mcp_tools import MCP_GENERATION_TOOLS
    tool = MCP_GENERATION_TOOLS["generate_melody"]
    schema = tool["inputSchema"]
    assert "prompt" in schema["properties"]
    assert "melody_path" in schema["properties"]


@pytest.mark.asyncio
async def test_mcp_generate_music_handler():
    from ai_generation.mcp_tools import MCPGenerationTools
    mcp = MCPGenerationTools()
    assert hasattr(mcp, "_handle_generate_music")


@pytest.mark.asyncio
async def test_mcp_music_profiles():
    from ai_generation.mcp_tools import MCPGenerationTools
    mcp = MCPGenerationTools()
    result = await mcp.handle("get_music_profiles", {})
    assert "profiles" in result
    assert len(result["profiles"]) == 7
