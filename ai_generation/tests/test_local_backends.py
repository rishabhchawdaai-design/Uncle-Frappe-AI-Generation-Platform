"""
Tests for the built-in free local backends: embeddings, TTS, STT,
translation, upscaling, and background removal.

All tests are offline: heavy third-party modules (torch, PIL, numpy,
sentence-transformers, piper, faster-whisper, transformers, spandrel,
rembg) are replaced with minimal fakes injected into ``sys.modules`` so
the suite runs in CI with only the stdlib + httpx requirements.
"""
import asyncio
import io as _io
import os
import sys
import types
from pathlib import Path

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from ai_generation.providers.registry import get_registry  # noqa: E402


# ── Minimal fakes for heavy third-party modules ──────────────────────────

class FakeArray:
    """List-backed array with a tiny numpy-like surface."""

    def __init__(self, data):
        self.data = data

    def astype(self, dtype):
        return self

    def __truediv__(self, x):
        return FakeArray(_div(self.data, x))

    def __mul__(self, x):
        return FakeArray(_mul(self.data, x))

    def tolist(self):
        return self.data


def _div(value, x):
    if isinstance(value, list):
        return [_div(v, x) for v in value]
    return value / x


def _mul(value, x):
    if isinstance(value, list):
        return [_mul(v, x) for v in value]
    return value * x


class FakeTensor:
    def __init__(self, arr):
        self.arr = arr

    def permute(self, *dims):
        return self

    def unsqueeze(self, dim):
        return self

    def squeeze(self, dim=0):
        return self

    def clamp(self, lo, hi):
        return self

    def numpy(self):
        return self.arr


class FakeNumpyModule(types.ModuleType):
    float32 = "float32"
    uint8 = "uint8"

    @staticmethod
    def array(obj, dtype=None):
        if hasattr(obj, "data"):
            return FakeArray(obj.data)
        if hasattr(obj, "arr"):
            return FakeArray(obj.arr)
        if isinstance(obj, list):
            return FakeArray(obj)
        return obj

    @staticmethod
    def repeat(a, repeats, axis=None):
        return a


class FakeTorchModule(types.ModuleType):
    class no_grad:
        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

    @staticmethod
    def from_numpy(arr):
        return FakeTensor(arr)


class FakePILImage:
    def __init__(self, arr=None):
        self.arr = arr or [[[0, 0, 0], [0, 0, 0]], [[0, 0, 0], [0, 0, 0]]]
        self.width = 4
        self.height = 4

    def convert(self, mode):
        return self

    def save(self, buf, format=None, **kwargs):
        buf.write(b"\x89PNG\r\n\x1a\nfake")


class FakePILModule(types.ModuleType):
    Image = None  # set after class definition

    @staticmethod
    def open(stream, *a, **k):
        return FakePILImage()

    @staticmethod
    def fromarray(arr, *a, **k):
        return FakePILImage()


FakePILModule.Image = FakePILModule


class FakeSentenceTransformer:
    def __init__(self, model_name="all-MiniLM-L6-v2"):
        self.model_name = model_name

    def encode(self, sentences, normalize_embeddings=True):
        return [FakeArray([0.1 + i * 0.001 for i in range(384)])]


class FakeSentenceTransformersModule(types.ModuleType):
    SentenceTransformer = FakeSentenceTransformer


class FakePiperVoice:
    @staticmethod
    def load(path):
        return FakePiperVoice()

    def synthesize(self, text, wav_file):
        wav_file.writeframes(b"\x00\x00" * 100)


class FakePiperModule(types.ModuleType):
    PiperVoice = FakePiperVoice


class FakeSegment:
    def __init__(self, text):
        self.text = text


class FakeWhisperInfo:
    language = "en"


class FakeWhisperModel:
    def __init__(self, *args, **kwargs):
        pass

    def transcribe(self, path):
        return ([FakeSegment("hello"), FakeSegment("world")], FakeWhisperInfo())


class FakeFasterWhisperModule(types.ModuleType):
    WhisperModel = FakeWhisperModel


class FakeMarianTokenizer:
    @staticmethod
    def from_pretrained(name):
        return FakeMarianTokenizer()

    def __call__(self, text, return_tensors="pt"):
        return {"input_ids": 1}

    @staticmethod
    def batch_decode(out, skip_special_tokens=True):
        return ["Bonjour, comment allez-vous aujourd'hui ?"]


class FakeMarianMTModel:
    @staticmethod
    def from_pretrained(name):
        return FakeMarianMTModel()

    def eval(self):
        return self

    def generate(self, **kwargs):
        return 1


class FakeTransformersModule(types.ModuleType):
    MarianTokenizer = FakeMarianTokenizer
    MarianMTModel = FakeMarianMTModel


class FakeUpscaleModel:
    def eval(self):
        return self

    def __call__(self, tensor):
        return tensor


class FakeSpandrelModule(types.ModuleType):
    ImageModelDescriptor = type("ImageModelDescriptor", (), {})

    class ModelLoader:
        def load_from_file(self, path):
            descriptor = types.SimpleNamespace()
            descriptor.model = FakeUpscaleModel().eval()
            return descriptor


class FakeRembgModule(types.ModuleType):
    @staticmethod
    def remove(image):
        return FakePILImage()


@pytest.fixture(autouse=True)
def reset_registry_caches():
    """Reset model/voice handles cached on registry singleton instances so
    fakes never leak into other test files."""
    yield
    reg = get_registry()
    for name in ("piper_local", "sentence_transformers", "faster_whisper",
                 "realesrgan", "rembg"):
        provider = reg.get(name)
        if provider is None:
            continue
        for attr in ("_voice", "_model", "_tok", "_remove"):
            if hasattr(provider, attr):
                setattr(provider, attr, None)


@pytest.fixture(autouse=True)
def fake_heavy_modules(monkeypatch):
    """Inject fake heavy modules so lazy imports never touch real packages."""
    fakes = {
        "numpy": FakeNumpyModule("numpy"),
        "torch": FakeTorchModule("torch"),
        "PIL": FakePILModule("PIL"),
        "sentence_transformers": FakeSentenceTransformersModule("sentence_transformers"),
        "piper": FakePiperModule("piper"),
        "faster_whisper": FakeFasterWhisperModule("faster_whisper"),
        "transformers": FakeTransformersModule("transformers"),
        "spandrel": FakeSpandrelModule("spandrel"),
        "rembg": FakeRembgModule("rembg"),
    }
    for name, module in fakes.items():
        monkeypatch.setitem(sys.modules, name, module)
    # Ensure submodules resolve to the same fake
    for sub in ("sentence_transformers.SentenceTransformer",
                "piper.PiperVoice", "faster_whisper.WhisperModel",
                "transformers.MarianTokenizer",
                "transformers.MarianMTModel",
                "spandrel.ImageModelDescriptor", "spandrel.ModelLoader"):
        monkeypatch.setitem(sys.modules, sub, fakes[sub.split(".")[0]])
    return fakes


def _png_bytes():
    import struct
    # Minimal valid-enough PNG-ish payload (1x1)
    return struct.pack(">II", 1, 1) + b"PNGDATA"


# ── Registry integration ────────────────────────────────────────────────

def test_local_backends_auto_registered():
    reg = get_registry()
    for name in ("sentence_transformers", "piper_local", "faster_whisper",
                 "helsinki_opus_mt", "realesrgan", "rembg"):
        provider = reg.get(name)
        assert provider is not None, f"{name} not registered"
        assert provider.requires_api_key is False
        assert provider.tier.value == "free"
        stats = provider.get_stats()
        assert stats["has_api_key"] is False


# ── Embeddings ──────────────────────────────────────────────────────────

def test_embedding_provider_success():
    from ai_generation.providers.local_backends import SentenceTransformersEmbeddingProvider

    provider = SentenceTransformersEmbeddingProvider()
    result = asyncio.run(provider.generate_text("hello world"))
    assert result.success
    assert result.metadata["vector_dim"] == 384
    assert result.metadata["model"] == "all-MiniLM-L6-v2"
    assert result.cost_estimate == 0.0
    assert provider.success_rate == 100.0


# ── TTS (Piper) ─────────────────────────────────────────────────────────

def test_piper_tts_success():
    from ai_generation.providers.local_backends import PiperTTSProvider

    provider = PiperTTSProvider()
    result = asyncio.run(provider.generate_audio("Hello there"))
    assert result.success
    assert result.output_format == "wav"
    assert result.output_bytes and len(result.output_bytes) > 0
    assert result.metadata["model"] == "en_US-lessac-medium"
    assert result.cost_estimate == 0.0


# ── STT (faster-whisper) ────────────────────────────────────────────────

def test_faster_whisper_transcribe():
    from ai_generation.providers.local_backends import FasterWhisperSTTProvider

    provider = FasterWhisperSTTProvider()
    result = asyncio.run(provider.transcribe_audio(audio_bytes=_png_bytes()))
    assert result.success
    assert result.metadata["text"] == "hello world"
    assert result.metadata["language"] == "en"
    assert result.output_format == "text"


def test_faster_whisper_no_audio_error():
    from ai_generation.providers.local_backends import FasterWhisperSTTProvider

    provider = FasterWhisperSTTProvider()
    result = asyncio.run(provider.transcribe_audio())
    assert result.status == "error"
    assert "No audio" in (result.error or "")


# ── Translation ─────────────────────────────────────────────────────────

def test_helsinki_translation_success():
    from ai_generation.providers.local_backends import HelsinkiTranslationProvider

    provider = HelsinkiTranslationProvider()
    result = asyncio.run(provider.generate_text("How are you today?"))
    assert result.success
    assert result.metadata["text"] == "Bonjour, comment allez-vous aujourd'hui ?"
    assert result.metadata["model"] == "opus-mt-en-fr"
    assert result.cost_estimate == 0.0


def test_helsinki_model_pair_selection():
    from ai_generation.providers.local_backends import HelsinkiTranslationProvider

    provider = HelsinkiTranslationProvider()
    assert "opus-mt-en-de" in provider.supported_models
    assert "opus-mt-en-es" in provider.supported_models


# ── Upscaling (Real-ESRGAN) ─────────────────────────────────────────────

def test_realesrgan_upscale_success():
    from ai_generation.providers.local_backends import RealESRGANUpscaleProvider

    provider = RealESRGANUpscaleProvider()
    result = asyncio.run(provider.generate_image(prompt="", output_bytes=_png_bytes()))
    assert result.success
    assert result.output_format == "png"
    assert result.output_bytes
    assert result.width > 0 and result.height > 0
    assert result.metadata["scale"] == 4
    assert result.cost_estimate == 0.0


def test_realesrgan_no_input_error():
    from ai_generation.providers.local_backends import RealESRGANUpscaleProvider

    provider = RealESRGANUpscaleProvider()
    result = asyncio.run(provider.generate_image(prompt=""))
    assert result.status == "error"
    assert "No image bytes" in (result.error or "")


# ── Background removal (rembg) ──────────────────────────────────────────

def test_rembg_removal_success():
    from ai_generation.providers.local_backends import RembgBGRemovalProvider

    provider = RembgBGRemovalProvider()
    result = asyncio.run(provider.generate_image(prompt="", output_bytes=_png_bytes()))
    assert result.success
    assert result.output_format == "png"
    assert result.output_bytes
    assert result.metadata["model"] == "u2net"
    assert result.cost_estimate == 0.0


# ── SDK integration ─────────────────────────────────────────────────────

def test_sdk_list_local_backends():
    from ai_generation import UncleFrappeAI

    ai = UncleFrappeAI()
    backends = ai.list_local_backends()
    names = {b["name"] for b in backends}
    assert {"sentence_transformers", "piper_local", "faster_whisper",
            "helsinki_opus_mt", "realesrgan", "rembg"} <= names
    for b in backends:
        assert b["requires_api_key"] is False
        assert b["tier"] == "free"


def test_sdk_generate_embedding():
    from ai_generation import UncleFrappeAI

    ai = UncleFrappeAI()
    result = asyncio.run(ai.generate_embedding("embed me"))
    assert result.success
    assert result.provider == "sentence_transformers"
    assert result.metadata["vector_dim"] == 384


def test_sdk_translate_text():
    from ai_generation import UncleFrappeAI

    ai = UncleFrappeAI()
    result = asyncio.run(ai.translate_text("Hello", target_lang="fr", source_lang="en"))
    assert result.success
    assert result.provider == "helsinki_opus_mt"
    assert "Bonjour" in result.metadata["text"]


def test_sdk_transcribe_audio():
    from ai_generation import UncleFrappeAI

    ai = UncleFrappeAI()
    result = asyncio.run(ai.transcribe_audio(audio_bytes=_png_bytes()))
    assert result.success
    assert result.provider == "faster_whisper"
    assert result.metadata["text"] == "hello world"


def test_sdk_generate_speech_local():
    from ai_generation import UncleFrappeAI

    ai = UncleFrappeAI()
    result = asyncio.run(ai.generate_speech_local("speak"))
    assert result.success
    assert result.provider == "piper_local"
    assert result.output_bytes and len(result.output_bytes) > 0


def test_sdk_upscale_image_local():
    from ai_generation import UncleFrappeAI

    ai = UncleFrappeAI()
    result = asyncio.run(ai.upscale_image_local(_png_bytes()))
    assert result.success
    assert result.provider == "realesrgan"
    assert result.output_bytes


def test_sdk_remove_background_local():
    from ai_generation import UncleFrappeAI

    ai = UncleFrappeAI()
    result = asyncio.run(ai.remove_background_local(_png_bytes()))
    assert result.success
    assert result.provider == "rembg"
    assert result.output_bytes


# ── CLI integration ─────────────────────────────────────────────────────

def test_cli_local_backends(capsys):
    import ai_generation.cli as cli

    result = asyncio.run(cli.cmd_local_backends())
    out = capsys.readouterr().out
    assert len(result) >= 6
    assert "sentence_transformers" in out
    assert "faster_whisper" in out
    assert "rembg" in out


def test_cli_embed(capsys):
    import ai_generation.cli as cli

    result = asyncio.run(cli.cmd_embed("hello"))
    out = capsys.readouterr().out
    assert result.success
    assert "Vector dim:  384" in out


def test_cli_translate(capsys):
    import ai_generation.cli as cli

    result = asyncio.run(cli.cmd_translate("How are you today?"))
    out = capsys.readouterr().out
    assert result.success
    assert "Bonjour" in out


def test_cli_tts(capsys, tmp_path):
    import ai_generation.cli as cli

    out_file = tmp_path / "speech.wav"
    result = asyncio.run(cli.cmd_tts("hello", output_path=str(out_file)))
    capsys.readouterr().out
    assert result.success
    assert out_file.exists()
    assert out_file.stat().st_size > 0


def test_cli_stt(tmp_path, capsys):
    import ai_generation.cli as cli

    audio_file = tmp_path / "in.wav"
    audio_file.write_bytes(_png_bytes())
    result = asyncio.run(cli.cmd_stt(str(audio_file)))
    out = capsys.readouterr().out
    assert result.success
    assert "hello world" in out


# ── MCP integration ─────────────────────────────────────────────────────

def test_mcp_local_backend_tools_registered():
    from ai_generation.mcp_tools import MCP_GENERATION_TOOLS, MCPGenerationTools

    for tool in ("list_local_backends", "generate_embedding", "translate_text",
                 "generate_speech_local", "transcribe_audio",
                 "upscale_image_local", "remove_background_local"):
        assert tool in MCP_GENERATION_TOOLS, f"missing {tool}"
        assert "inputSchema" in MCP_GENERATION_TOOLS[tool]
    handler = MCPGenerationTools()
    for tool in ("list_local_backends", "generate_embedding", "translate_text",
                 "generate_speech_local", "transcribe_audio",
                 "upscale_image_local", "remove_background_local"):
        assert hasattr(handler, f"_handle_{tool}"), f"missing handler {tool}"


def test_mcp_list_local_backends_dispatch():
    from ai_generation.mcp_tools import MCPGenerationTools

    handler = MCPGenerationTools()
    result = asyncio.run(handler.handle("list_local_backends", {}))
    names = {b["name"] for b in result["backends"]}
    assert "sentence_transformers" in names
    assert "rembg" in names


def test_mcp_generate_embedding_dispatch():
    from ai_generation.mcp_tools import MCPGenerationTools

    handler = MCPGenerationTools()
    result = asyncio.run(handler.handle("generate_embedding", {"text": "mcp"}))
    assert result["status"] == "success"
    assert result["provider"] == "sentence_transformers"
    assert result["metadata"]["vector_dim"] == 384


def test_mcp_translate_text_dispatch():
    from ai_generation.mcp_tools import MCPGenerationTools

    handler = MCPGenerationTools()
    result = asyncio.run(handler.handle("translate_text", {"text": "Hello"}))
    assert result["status"] == "success"
    assert "Bonjour" in result["metadata"]["text"]


def test_mcp_transcribe_audio_dispatch(tmp_path):
    from ai_generation.mcp_tools import MCPGenerationTools

    audio_file = tmp_path / "clip.wav"
    audio_file.write_bytes(_png_bytes())
    handler = MCPGenerationTools()
    result = asyncio.run(handler.handle("transcribe_audio", {"audio_path": str(audio_file)}))
    assert result["status"] == "success"
    assert result["metadata"]["text"] == "hello world"
