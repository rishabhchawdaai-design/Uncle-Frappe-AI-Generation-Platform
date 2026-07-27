"""
Phase 23 Tests — OCR & Document Intelligence

Tests OCR provider profiles, backend selection, routing, and SDK/MCP exposure.
"""
import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))


def test_ocr_backend_enum():
    from ai_generation.ocr_engine import OCRBackend
    assert OCRBackend.TESSERACT.value == "tesseract"
    assert OCRBackend.PADDLEOCR.value == "paddleocr"
    assert OCRBackend.EASYOCR.value == "easyocr"
    assert OCRBackend.SURYA.value == "surya"


def test_document_type_enum():
    from ai_generation.ocr_engine import DocumentType
    assert DocumentType.IMAGE.value == "image"
    assert DocumentType.PDF.value == "pdf"
    assert DocumentType.SCANNED.value == "scanned"


def test_ocr_result_serialization():
    from ai_generation.ocr_engine import OCRResult
    r = OCRResult(text="Hello", confidence=0.95, backend="tesseract")
    d = r.to_dict()
    assert d["text"] == "Hello"
    assert d["confidence"] == 0.95
    assert d["backend"] == "tesseract"


def test_ocr_engine_import():
    from ai_generation.ocr_engine import OCREngine
    engine = OCREngine()
    assert engine is not None


def test_ocr_engine_has_profiles():
    from ai_generation.ocr_engine import OCREngine
    engine = OCREngine()
    providers = engine.list_providers()
    assert len(providers) >= 4
    backends = [p["backend"] for p in providers]
    assert "tesseract" in backends
    assert "paddleocr" in backends
    assert "easyocr" in backends
    assert "surya" in backends


def test_ocr_engine_get_provider():
    from ai_generation.ocr_engine import OCREngine
    engine = OCREngine()
    p = engine.get_provider("tesseract")
    assert p is not None
    assert p["backend"] == "tesseract"
    assert p["license"] == "Apache-2.0"
    assert engine.get_provider("nonexistent") is None


def test_ocr_select_backend_default():
    from ai_generation.ocr_engine import OCREngine
    engine = OCREngine()
    backend = engine.select_backend()
    # Should select paddleocr (highest quality + speed)
    assert backend in ["paddleocr", "surya", "easyocr", "tesseract"]


def test_ocr_select_backend_cjk():
    from ai_generation.ocr_engine import OCREngine, DocumentType
    engine = OCREngine()
    backend = engine.select_backend(DocumentType.IMAGE, "zh")
    # PaddleOCR has CJK strength
    assert backend in ["paddleocr", "surya"]


def test_ocr_select_backend_gpu():
    from ai_generation.ocr_engine import OCREngine, DocumentType
    engine = OCREngine()
    backend = engine.select_backend(DocumentType.IMAGE, "en", needs_gpu=True)
    # Should select a GPU-capable backend
    assert backend in ["paddleocr", "easyocr", "surya"]


def test_ocr_process_routing():
    from ai_generation.ocr_engine import OCREngine, OCRRequest
    engine = OCREngine()
    req = OCRRequest(document_type="image", language="en")
    result = engine.process(req)
    assert result.backend != ""
    assert result.to_dict()["backend"] != ""


def test_ocr_stats():
    from ai_generation.ocr_engine import OCREngine
    engine = OCREngine()
    stats = engine.get_stats()
    assert "provider_count" in stats
    assert stats["provider_count"] >= 4


def test_ocr_negotiation_candidates():
    from ai_generation.ocr_engine import OCREngine
    engine = OCREngine()
    candidates = engine.to_negotiation_candidates()
    assert len(candidates) >= 4
    assert all(c["layer"] == "ocr" for c in candidates)


# ── SDK Integration Tests ─────────────────────────────────────

def test_sdk_ocr_import():
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    assert hasattr(ai, 'ocr_engine')
    assert hasattr(ai, 'list_ocr_providers')
    assert hasattr(ai, 'select_ocr_backend')
    assert hasattr(ai, 'process_ocr')
    assert hasattr(ai, 'get_ocr_stats')


def test_sdk_list_ocr_providers():
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    providers = ai.list_ocr_providers()
    assert len(providers) >= 4


def test_sdk_select_ocr_backend():
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    backend = ai.select_ocr_backend()
    assert backend != ""


def test_sdk_ocr_stats():
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    stats = ai.get_ocr_stats()
    assert "provider_count" in stats


# ── MCP Tools Tests ──────────────────────────────────────────

def test_mcp_ocr_tools_exist():
    from ai_generation.mcp_tools import MCP_GENERATION_TOOLS
    assert "list_ocr_providers" in MCP_GENERATION_TOOLS
    assert "select_ocr_backend" in MCP_GENERATION_TOOLS
    assert "process_ocr" in MCP_GENERATION_TOOLS
    assert "get_ocr_stats" in MCP_GENERATION_TOOLS


def test_mcp_ocr_handler_import():
    from ai_generation.mcp_tools import MCPGenerationTools
    handler = MCPGenerationTools()
    assert hasattr(handler, '_handle_list_ocr_providers')
    assert hasattr(handler, '_handle_select_ocr_backend')
    assert hasattr(handler, '_handle_process_ocr')
    assert hasattr(handler, '_handle_get_ocr_stats')
