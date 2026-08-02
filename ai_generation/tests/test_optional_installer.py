"""
Tests for the optional local-backend dependency installer
(optional_requirements.txt + scripts/install-optional.sh).
"""
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")


def _req_path():
    return os.path.join(ROOT, "optional_requirements.txt")


def test_requirements_cover_all_local_backends():
    text = open(_req_path()).read()
    for pkg in ("sentence-transformers", "piper-tts", "faster-whisper",
                "transformers", "spandrel", "rembg", "pytesseract",
                "marker-pdf", "camelot-py", "meilisearch", "opensearch-py"):
        assert pkg in text, pkg


def test_group_headers_match_cli_names():
    text = open(_req_path()).read()
    headers = re.findall(r"^# Group: (\S+)", text, re.M)
    for g in ("embeddings", "speech", "translation", "upscaling",
              "background_removal", "ocr", "documents", "search"):
        assert g in headers, g


def test_installer_syntax_and_groups():
    script = os.path.join(ROOT, "scripts", "install-optional.sh")
    subprocess.run(["bash", "-n", script], check=True)
    for group in ("embeddings", "ocr", "background_removal", "translation"):
        out = subprocess.run(
            ["bash", script, "--group", group, "--dry-run"],
            capture_output=True, text=True, check=True).stdout
        assert "would install" in out
    out = subprocess.run(
        ["bash", script, "--dry-run"], capture_output=True, text=True,
        check=True).stdout
    for pkg in ("sentence-transformers", "faster-whisper", "spandrel"):
        assert pkg in out
