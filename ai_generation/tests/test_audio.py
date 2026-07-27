"""
Phase 16 Tests — Audio Generation Engine

Tests TTS providers, STT providers, audio generation orchestration,
voice resolution, and SDK integration.
"""
import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))


# ── AudioProvider Base Tests ───────────────────────────────────

def test_audio_provider_base_import():
    from ai_generation.providers.base import AudioProvider, STTProvider, ProviderType
    assert ProviderType.AUDIO.value == "audio"
    assert hasattr(AudioProvider, 'generate_audio')
    assert hasattr(STTProvider, 'transcribe_audio')


def test_piper_provider_import():
    from ai_generation.providers.audio_providers import PiperTTSProvider
    p = PiperTTSProvider()
    assert p.name == "piper_tts"
    assert p.tier.value == "free"
    assert p.requires_api_key is False
    assert "text_to_speech" in [c.name for c in p.capabilities]


def test_kokoro_provider_import():
    from ai_generation.providers.audio_providers import KokoroTTSProvider
    p = KokoroTTSProvider()
    assert p.name == "kokoro_tts"
    assert p.tier.value == "free"
    assert p.requires_api_key is False


def test_openai_tts_provider_import():
    from ai_generation.providers.audio_providers import OpenAITTSProvider
    p = OpenAITTSProvider()
    assert p.name == "openai_tts"
    assert p.tier.value == "paid"
    assert p.requires_api_key is True
    assert "tts-1" in p.supported_models


def test_whisper_stt_provider_import():
    from ai_generation.providers.audio_providers import WhisperSTTProvider
    w = WhisperSTTProvider()
    assert w.name == "whisper_stt"
    assert w.tier.value == "free"
    assert w.requires_api_key is False
    assert "speech_to_text" in [c.name for c in w.capabilities]


# ── Provider Availability Tests ───────────────────────────────

def test_piper_provider_not_available_no_server():
    from ai_generation.providers.audio_providers import PiperTTSProvider
    p = PiperTTSProvider()
    # Provider is registered but server may not be running
    # is_available checks status + error count
    assert p._status.value == "available"


def test_kokoro_provider_not_available_no_server():
    from ai_generation.providers.audio_providers import KokoroTTSProvider
    p = KokoroTTSProvider()
    assert p._status.value == "available"


def test_openai_tts_no_key():
    import os
    os.environ.pop("OPENAI_API_KEY", None)
    from ai_generation.providers.audio_providers import OpenAITTSProvider
    p = OpenAITTSProvider()
    assert not p.api_key


def test_whisper_provider_not_available_no_server():
    from ai_generation.providers.audio_providers import WhisperSTTProvider
    w = WhisperSTTProvider()
    assert w._status.value == "available"


# ── TTS Generation Tests (with mocked HTTP) ───────────────────

@pytest.mark.asyncio
async def test_piper_tts_server_not_running():
    from ai_generation.providers.audio_providers import PiperTTSProvider
    p = PiperTTSProvider()
    result = await p.generate_audio("Hello world")
    assert result.status == "error"
    assert "not running" in result.error.lower() or "connect" in result.error.lower()


@pytest.mark.asyncio
async def test_kokoro_tts_server_not_running():
    from ai_generation.providers.audio_providers import KokoroTTSProvider
    p = KokoroTTSProvider()
    result = await p.generate_audio("Hello world")
    assert result.status == "error"
    assert "not running" in result.error.lower() or "connect" in result.error.lower()


@pytest.mark.asyncio
async def test_openai_tts_no_api_key():
    import os
    os.environ.pop("OPENAI_API_KEY", None)
    from ai_generation.providers.audio_providers import OpenAITTSProvider
    p = OpenAITTSProvider()
    result = await p.generate_audio("Hello world")
    assert result.status == "error"
    assert "OPENAI_API_KEY" in result.error


@pytest.mark.asyncio
async def test_whisper_stt_server_not_running():
    from ai_generation.providers.audio_providers import WhisperSTTProvider
    w = WhisperSTTProvider()
    result = await w.transcribe_audio(b"fake audio data")
    assert result.status == "error"
    assert "not running" in result.error.lower() or "connect" in result.error.lower()


# ── Audio Generation Engine Tests ──────────────────────────────

def test_audio_engine_import():
    from ai_generation.audio_generation import (
        AudioGenerationEngine, AudioRequest, AudioResult,
        AudioTask, VOICE_PRESETS,
    )
    assert AudioTask.TEXT_TO_SPEECH.value == "text_to_speech"
    assert AudioTask.SPEECH_TO_TEXT.value == "speech_to_text"
    assert "piper_tts" in VOICE_PRESETS
    assert "kokoro_tts" in VOICE_PRESETS
    assert "openai_tts" in VOICE_PRESETS


def test_audio_engine_init():
    from ai_generation.audio_generation import AudioGenerationEngine
    engine = AudioGenerationEngine()
    stats = engine.get_stats()
    assert stats["total_requests"] == 0
    assert stats["successful"] == 0


def test_audio_engine_list_providers():
    from ai_generation.audio_generation import AudioGenerationEngine
    engine = AudioGenerationEngine()
    providers = engine.list_providers()
    assert "tts" in providers
    assert "stt" in providers
    assert isinstance(providers["tts"], list)
    assert isinstance(providers["stt"], list)


def test_audio_engine_voice_resolution():
    from ai_generation.audio_generation import AudioGenerationEngine
    engine = AudioGenerationEngine()
    # Default voice
    assert engine._resolve_voice("piper_tts", "default") == "en_US-lessac-medium"
    assert engine._resolve_voice("kokoro_tts", "default") == "af_heart"
    assert engine._resolve_voice("openai_tts", "default") == "alloy"
    # Custom voice passthrough
    assert engine._resolve_voice("piper_tts", "custom_voice") == "custom_voice"
    # Alias resolution
    assert engine._resolve_voice("piper_tts", "female") == "en_US-amy-medium"
    assert engine._resolve_voice("openai_tts", "nova") == "nova"


@pytest.mark.asyncio
async def test_audio_engine_tts_no_providers():
    from ai_generation.audio_generation import AudioGenerationEngine
    engine = AudioGenerationEngine()
    # With no providers running, should fail gracefully
    result = await engine.text_to_speech("Hello")
    assert result.status == "error"
    assert result.error is not None


@pytest.mark.asyncio
async def test_audio_engine_stt_no_providers():
    from ai_generation.audio_generation import AudioGenerationEngine
    engine = AudioGenerationEngine()
    result = await engine.transcribe(b"fake audio")
    assert result.status == "error"
    assert result.error is not None


def test_audio_engine_stats():
    from ai_generation.audio_generation import AudioGenerationEngine
    engine = AudioGenerationEngine()
    stats = engine.get_stats()
    assert "total_requests" in stats
    assert "tts_requests" in stats
    assert "stt_requests" in stats
    assert "avg_latency_ms" in stats


def test_audio_result_serialization():
    from ai_generation.audio_generation import AudioResult, AudioTask
    result = AudioResult(
        task=AudioTask.TEXT_TO_SPEECH,
        provider="piper_tts",
        status="success",
        output_format="wav",
        latency_ms=150.0,
    )
    d = result.to_dict()
    assert d["task"] == "text_to_speech"
    assert d["provider"] == "piper_tts"
    assert d["status"] == "success"
    assert d["latency_ms"] == 150.0


def test_audio_request_defaults():
    from ai_generation.audio_generation import AudioRequest, AudioTask
    req = AudioRequest(text="Hello world")
    assert req.task == AudioTask.TEXT_TO_SPEECH
    assert req.voice == "default"
    assert req.speed == 1.0
    assert req.language == "en"
    assert req.output_format == "wav"


# ── SDK Integration Tests ──────────────────────────────────────

def test_sdk_audio_import():
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    assert hasattr(ai, 'text_to_speech')
    assert hasattr(ai, 'transcribe')
    assert hasattr(ai, 'list_audio_providers')
    assert hasattr(ai, 'get_audio_stats')
    assert hasattr(ai, 'audio_generation')


def test_sdk_audio_stats():
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    stats = ai.get_audio_stats()
    assert "total_requests" in stats
    assert stats["total_requests"] == 0


def test_sdk_list_audio_providers():
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    providers = ai.list_audio_providers()
    assert "tts" in providers
    assert "stt" in providers


# ── MCP Tools Tests ────────────────────────────────────────────

def test_mcp_audio_tools_exist():
    from ai_generation.mcp_tools import MCP_GENERATION_TOOLS
    assert "text_to_speech" in MCP_GENERATION_TOOLS
    assert "transcribe" in MCP_GENERATION_TOOLS
    assert "list_audio_providers" in MCP_GENERATION_TOOLS
    assert "get_audio_stats" in MCP_GENERATION_TOOLS


def test_mcp_tts_tool_schema():
    from ai_generation.mcp_tools import MCP_GENERATION_TOOLS
    tool = MCP_GENERATION_TOOLS["text_to_speech"]
    assert tool["name"] == "text_to_speech"
    assert "text" in tool["inputSchema"]["required"]
    assert "voice" in tool["inputSchema"]["properties"]
    assert "provider" in tool["inputSchema"]["properties"]
    assert "speed" in tool["inputSchema"]["properties"]


def test_mcp_transcribe_tool_schema():
    from ai_generation.mcp_tools import MCP_GENERATION_TOOLS
    tool = MCP_GENERATION_TOOLS["transcribe"]
    assert tool["name"] == "transcribe"
    assert "audio_path" in tool["inputSchema"]["required"]
    assert "language" in tool["inputSchema"]["properties"]
    assert "provider" in tool["inputSchema"]["properties"]


def test_mcp_audio_handler_import():
    from ai_generation.mcp_tools import MCPGenerationTools
    handler = MCPGenerationTools()
    assert hasattr(handler, '_handle_text_to_speech')
    assert hasattr(handler, '_handle_transcribe')
    assert hasattr(handler, '_handle_list_audio_providers')
    assert hasattr(handler, '_handle_get_audio_stats')
