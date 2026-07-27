"""Tests for AUD-06 — Voice Cloning."""
import pytest


def test_voice_cloning_provider_enum():
    from ai_generation.voice_cloning import VoiceCloningProvider
    assert VoiceCloningProvider.XTTS.value == "xtts"
    assert VoiceCloningProvider.FISH_SPEECH.value == "fish_speech"
    assert VoiceCloningProvider.OPENVOICE.value == "openvoice"


def test_voice_clone_status_enum():
    from ai_generation.voice_cloning import VoiceCloneStatus
    assert VoiceCloneStatus.COMPLETED.value == "completed"
    assert VoiceCloneStatus.FAILED.value == "failed"
    assert VoiceCloneStatus.DEPENDENCY_MISSING.value == "dependency_missing"


def test_voice_clone_profiles():
    from ai_generation.voice_cloning import VOICE_CLONE_PROFILES, VoiceCloningProvider
    assert len(VOICE_CLONE_PROFILES) == 3
    for p in VOICE_CLONE_PROFILES.values():
        assert p.voice_cloning is True
        assert len(p.languages) > 0


def test_voice_clone_profile_serialization():
    from ai_generation.voice_cloning import VOICE_CLONE_PROFILES, VoiceCloningProvider
    p = VOICE_CLONE_PROFILES[VoiceCloningProvider.XTTS]
    d = p.to_dict()
    assert d["provider"] == "xtts"
    assert d["voice_cloning"] is True
    assert "en" in d["languages"]


def test_voice_clone_result_serialization():
    from ai_generation.voice_cloning import VoiceCloneResult, VoiceCloneStatus
    r = VoiceCloneResult(provider="xtts", status=VoiceCloneStatus.COMPLETED, request_id="test-123")
    d = r.to_dict()
    assert d["provider"] == "xtts"
    assert d["status"] == "completed"
    assert d["request_id"] == "test-123"


def test_voice_cloning_engine_import():
    from ai_generation.voice_cloning import VoiceCloningEngine
    e = VoiceCloningEngine()
    assert e is not None


def test_voice_cloning_engine_profiles():
    from ai_generation.voice_cloning import VoiceCloningEngine
    e = VoiceCloningEngine()
    profiles = e.get_profiles()
    assert len(profiles) == 3


def test_voice_cloning_engine_providers():
    from ai_generation.voice_cloning import VoiceCloningEngine
    e = VoiceCloningEngine()
    names = e.get_provider_names()
    assert "xtts" in names
    assert "fish_speech" in names
    assert "openvoice" in names


def test_voice_cloning_engine_stats():
    from ai_generation.voice_cloning import VoiceCloningEngine
    e = VoiceCloningEngine()
    stats = e.get_stats()
    assert stats["total_clones"] == 0
    assert stats["profiles"] == 3


@pytest.mark.asyncio
async def test_voice_clone_all_fail():
    from ai_generation.voice_cloning import VoiceCloningEngine, VoiceCloneStatus
    e = VoiceCloningEngine()
    result = await e.clone_voice("ref.wav", "Hello world")
    assert result.status == VoiceCloneStatus.FAILED
    assert "failed" in result.error.lower() or "all" in result.error.lower()


# ── SDK Integration ──

def test_sdk_voice_cloning_import():
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    assert ai.voice_cloning is not None
    assert type(ai.voice_cloning).__name__ == "VoiceCloningEngine"


def test_sdk_voice_cloning_in_stats():
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    stats = ai.get_stats()
    assert "voice_cloning" in stats


# ── MCP Tools ──

def test_mcp_voice_tools_exist():
    from ai_generation.mcp_tools import MCP_GENERATION_TOOLS
    assert "clone_voice" in MCP_GENERATION_TOOLS
    assert "get_voice_clone_profiles" in MCP_GENERATION_TOOLS


def test_mcp_clone_voice_schema():
    from ai_generation.mcp_tools import MCP_GENERATION_TOOLS
    tool = MCP_GENERATION_TOOLS["clone_voice"]
    schema = tool["inputSchema"]
    assert "reference_audio_path" in schema["properties"]
    assert "text" in schema["properties"]
    assert "language" in schema["properties"]


@pytest.mark.asyncio
async def test_mcp_clone_voice_handler():
    from ai_generation.mcp_tools import MCPGenerationTools
    mcp = MCPGenerationTools()
    assert hasattr(mcp, "_handle_clone_voice")


@pytest.mark.asyncio
async def test_mcp_voice_clone_profiles():
    from ai_generation.mcp_tools import MCPGenerationTools
    mcp = MCPGenerationTools()
    result = await mcp.handle("get_voice_clone_profiles", {})
    assert "profiles" in result
    assert "providers" in result
    assert len(result["profiles"]) == 3
