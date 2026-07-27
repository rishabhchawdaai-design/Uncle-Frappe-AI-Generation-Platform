"""Tests for OCR-06/07/08 — Document Parsing, Table Extraction, Layout Analysis."""
import pytest


def test_doc_parsing_backend_enum():
    from ai_generation.document_intelligence import DocParsingBackend
    assert DocParsingBackend.MARKER.value == "marker"
    assert DocParsingBackend.NOUGAT.value == "nougat"
    assert DocParsingBackend.DOCLING.value == "docling"
    assert DocParsingBackend.BUILTIN.value == "builtin"


def test_table_extraction_backend_enum():
    from ai_generation.document_intelligence import TableExtractionBackend
    assert TableExtractionBackend.CAMELOT.value == "camelot"
    assert TableExtractionBackend.TABULA.value == "tabula"


def test_layout_backend_enum():
    from ai_generation.document_intelligence import LayoutBackend
    assert LayoutBackend.LAYOUTLMV3.value == "layoutlmv3"
    assert LayoutBackend.DETR.value == "detr"
    assert LayoutBackend.SURYA.value == "surya"


def test_document_format_enum():
    from ai_generation.document_intelligence import DocumentFormat
    assert DocumentFormat.PDF.value == "pdf"
    assert DocumentFormat.DOCX.value == "docx"
    assert DocumentFormat.HTML.value == "html"
    assert DocumentFormat.MARKDOWN.value == "markdown"


def test_doc_intelligence_status_enum():
    from ai_generation.document_intelligence import DocIntelligenceStatus
    assert DocIntelligenceStatus.COMPLETED.value == "completed"
    assert DocIntelligenceStatus.FAILED.value == "failed"
    assert DocIntelligenceStatus.DEPENDENCY_MISSING.value == "dependency_missing"


def test_backend_profile_serialization():
    from ai_generation.document_intelligence import BackendProfile
    p = BackendProfile(
        name="Marker", backend_type="document_parsing",
        description="Fast PDF to Markdown", license="GPL-3.0",
        requires_gpu=False, install_command="pip install marker-pdf",
        strengths=["speed", "tables"], supported_formats=["pdf"],
        maturity="production",
    )
    d = p.to_dict()
    assert d["name"] == "Marker"
    assert d["license"] == "GPL-3.0"
    assert "speed" in d["strengths"]


def test_document_parse_result_serialization():
    from ai_generation.document_intelligence import DocumentParseResult, DocIntelligenceStatus
    r = DocumentParseResult(backend="marker", status=DocIntelligenceStatus.COMPLETED, request_id="test-123")
    d = r.to_dict()
    assert d["backend"] == "marker"
    assert d["status"] == "completed"


def test_table_extraction_result_serialization():
    from ai_generation.document_intelligence import TableExtractionResult, DocIntelligenceStatus
    r = TableExtractionResult(
        backend="camelot", status=DocIntelligenceStatus.COMPLETED,
        tables=[{"page": 1, "rows": 3, "cols": 2}], table_count=1,
    )
    d = r.to_dict()
    assert d["backend"] == "camelot"
    assert d["table_count"] == 1


def test_layout_analysis_result_serialization():
    from ai_generation.document_intelligence import LayoutAnalysisResult, DocIntelligenceStatus
    r = LayoutAnalysisResult(
        backend="layoutlmv3", status=DocIntelligenceStatus.DEPENDENCY_MISSING,
        regions=[], region_count=0,
    )
    d = r.to_dict()
    assert d["backend"] == "layoutlmv3"
    assert d["status"] == "dependency_missing"


def test_doc_intelligence_engine_import():
    from ai_generation.document_intelligence import DocumentIntelligenceEngine
    e = DocumentIntelligenceEngine()
    assert e is not None


def test_doc_intelligence_parsing_profiles():
    from ai_generation.document_intelligence import DocumentIntelligenceEngine
    e = DocumentIntelligenceEngine()
    profiles = e.get_parsing_profiles()
    assert len(profiles) == 3
    names = [p["name"] for p in profiles]
    assert "Marker" in names


def test_doc_intelligence_table_profiles():
    from ai_generation.document_intelligence import DocumentIntelligenceEngine
    e = DocumentIntelligenceEngine()
    profiles = e.get_table_profiles()
    assert len(profiles) == 2
    names = [p["name"] for p in profiles]
    assert "Camelot" in names


def test_doc_intelligence_layout_profiles():
    from ai_generation.document_intelligence import DocumentIntelligenceEngine
    e = DocumentIntelligenceEngine()
    profiles = e.get_layout_profiles()
    assert len(profiles) == 3


def test_doc_intelligence_stats():
    from ai_generation.document_intelligence import DocumentIntelligenceEngine
    e = DocumentIntelligenceEngine()
    stats = e.get_stats()
    assert stats["total_operations"] == 0
    assert stats["parsing_profiles"] == 3
    assert stats["table_profiles"] == 2
    assert stats["layout_profiles"] == 3


@pytest.mark.asyncio
async def test_parse_document_no_backend():
    from ai_generation.document_intelligence import DocumentIntelligenceEngine, DocIntelligenceStatus
    e = DocumentIntelligenceEngine()
    result = await e.parse_document("test.pdf")
    assert result.status == DocIntelligenceStatus.DEPENDENCY_MISSING


@pytest.mark.asyncio
async def test_extract_tables_no_backend():
    from ai_generation.document_intelligence import DocumentIntelligenceEngine, DocIntelligenceStatus
    e = DocumentIntelligenceEngine()
    result = await e.extract_tables("test.pdf")
    assert result.status == DocIntelligenceStatus.DEPENDENCY_MISSING


@pytest.mark.asyncio
async def test_analyze_layout_no_backend():
    from ai_generation.document_intelligence import DocumentIntelligenceEngine, DocIntelligenceStatus
    e = DocumentIntelligenceEngine()
    result = await e.analyze_layout("test.pdf")
    assert result.status == DocIntelligenceStatus.DEPENDENCY_MISSING


# ── SDK Integration ──

def test_sdk_doc_intelligence_import():
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    assert ai.document_intelligence is not None
    assert type(ai.document_intelligence).__name__ == "DocumentIntelligenceEngine"


def test_sdk_doc_intelligence_in_stats():
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    stats = ai.get_stats()
    assert "document_intelligence" in stats


# ── MCP Tools ──

def test_mcp_doc_intelligence_tools_exist():
    from ai_generation.mcp_tools import MCP_GENERATION_TOOLS
    assert "parse_document" in MCP_GENERATION_TOOLS
    assert "extract_tables" in MCP_GENERATION_TOOLS
    assert "analyze_layout" in MCP_GENERATION_TOOLS
    assert "get_doc_intelligence_profiles" in MCP_GENERATION_TOOLS


def test_mcp_parse_document_schema():
    from ai_generation.mcp_tools import MCP_GENERATION_TOOLS
    tool = MCP_GENERATION_TOOLS["parse_document"]
    schema = tool["inputSchema"]
    assert "input_path" in schema["properties"]
    assert "backend" in schema["properties"]


def test_mcp_extract_tables_schema():
    from ai_generation.mcp_tools import MCP_GENERATION_TOOLS
    tool = MCP_GENERATION_TOOLS["extract_tables"]
    schema = tool["inputSchema"]
    assert "input_path" in schema["properties"]
    assert "pages" in schema["properties"]


@pytest.mark.asyncio
async def test_mcp_parse_document_handler():
    from ai_generation.mcp_tools import MCPGenerationTools
    mcp = MCPGenerationTools()
    assert hasattr(mcp, "_handle_parse_document")


@pytest.mark.asyncio
async def test_mcp_doc_intelligence_profiles():
    from ai_generation.mcp_tools import MCPGenerationTools
    mcp = MCPGenerationTools()
    result = await mcp.handle("get_doc_intelligence_profiles", {})
    assert "parsing" in result
    assert "table_extraction" in result
    assert "layout" in result
    assert len(result["parsing"]) == 3
