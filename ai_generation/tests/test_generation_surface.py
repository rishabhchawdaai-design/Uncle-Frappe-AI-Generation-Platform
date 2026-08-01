"""
Tests for the SDK generation surface (3D, speech, audio aliases) and
truthful failure reporting for credential/local-gated modalities.
"""
import pytest

from ai_generation.music_generation import MusicGenStatus


@pytest.mark.asyncio
async def test_generate_3d_returns_truthful_result():
    from ai_generation import UncleFrappeAI
    ai = UncleFrappeAI()
    result = await ai.generate_3d("a red cube")
    assert isinstance(result, dict)
    assert result["status"] in ("unavailable", "dependency_missing")
    assert result["error"]
    assert result["backend"] in ("none", "microsoft/trellis", "tencent/hunyuan3d", "openai/point-e", "openai/shap-e")
    assert result["request_id"].startswith("3d-")


@pytest.mark.asyncio
async def test_generate_3d_specific_model_requires_local_gpu():
    from ai_generation import UncleFrappeAI
    ai = UncleFrappeAI()
    result = await ai.generate_3d("a red cube", model_id="microsoft/trellis")
    assert result["status"] == "dependency_missing"
    assert "VRAM" in result["error"]
    assert result["backend"] == "microsoft/trellis"
    assert result["metadata"]["model"]["model_id"] == "microsoft/trellis"


@pytest.mark.asyncio
async def test_generate_3d_unknown_mode_returns_unavailable():
    from ai_generation import UncleFrappeAI
    ai = UncleFrappeAI()
    result = await ai.generate_3d("a red cube", mode="text_to_3d", max_vram_gb=0.0)
    assert result["status"] in ("unavailable", "dependency_missing")


@pytest.mark.asyncio
async def test_generate_speech_returns_clean_error_without_keys():
    from ai_generation import UncleFrappeAI
    ai = UncleFrappeAI()
    result = await ai.generate_speech("Hello from the platform")
    assert result.status == "error"
    assert result.error
    assert "failed" in result.error.lower() or "not running" in result.error.lower()


@pytest.mark.asyncio
async def test_generate_audio_is_speech_alias():
    from ai_generation import UncleFrappeAI
    ai = UncleFrappeAI()
    result = await ai.generate_audio("Hello from the platform")
    assert result.status == "error"
    assert result.error


@pytest.mark.asyncio
async def test_music_connect_error_is_actionable():
    from ai_generation import UncleFrappeAI
    ai = UncleFrappeAI()
    result = await ai.generate_music("upbeat jazz", duration_secs=1.0)
    assert result.status == MusicGenStatus.DEPENDENCY_MISSING
    assert "AudioCraft server not reachable" in result.error
    assert "MUSICGEN_URL" in result.error


@pytest.mark.asyncio
async def test_sfx_connect_error_is_actionable():
    from ai_generation import UncleFrappeAI
    ai = UncleFrappeAI()
    result = await ai.generate_sfx("thunder", duration_secs=1.0)
    assert result.status == MusicGenStatus.DEPENDENCY_MISSING
    assert "AudioCraft server not reachable" in result.error


def test_3d_engine_stats_and_models():
    from ai_generation import UncleFrappeAI
    ai = UncleFrappeAI()
    stats = ai.generation_3d.get_stats()
    assert stats["model_count"] == 4
    models = ai.generation_3d.list_models()
    assert {m["model_id"] for m in models} >= {
        "microsoft/trellis", "tencent/hunyuan3d", "openai/point-e", "openai/shap-e"}
