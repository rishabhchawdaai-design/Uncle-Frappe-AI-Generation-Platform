"""
Tests for the E2E verification harness (scripts/verify_generation.py):
artifact helpers must produce/validate real media, and the harness must
cover every platform modality.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
SCRIPTS = os.path.join(os.path.dirname(__file__), "..", "..", "scripts")
sys.path.insert(0, SCRIPTS)


def test_tiny_png_helper():
    from verify_generation import tiny_png_bytes, png_ok, image_dims
    data = tiny_png_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    assert png_ok(data)
    assert image_dims(data) == {"width": 1, "height": 1}


def test_wav_helper_detects_ri():
    from verify_generation import wav_ok
    header = b"RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00"
    assert wav_ok(header)
    assert not wav_ok(b"\x89PNG\r\n\x1a\n")


def test_harness_covers_all_modalities():
    path = os.path.join(SCRIPTS, "verify_generation.py")
    text = open(path).read()
    for name in ("image", "video", "music", "sfx", "speech", "3d", "text",
                 "embedding", "speech_local", "translation", "ocr",
                 "stt_local", "upscale", "bg_removal", "storage",
                 "event_log", "capability_graph", "compatibility_matrix",
                 "registries"):
        assert '"' + name + '"' in text, name
