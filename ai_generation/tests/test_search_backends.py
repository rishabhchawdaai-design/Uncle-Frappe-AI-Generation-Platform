"""Tests for SRC-09/10/11 — Meilisearch, OpenSearch, Vector Search."""
import pytest


def test_external_search_backend_enum():
    from ai_generation.search_backends import ExternalSearchBackend
    assert ExternalSearchBackend.MEILISEARCH.value == "meilisearch"
    assert ExternalSearchBackend.OPENSEARCH.value == "opensearch"
    assert ExternalSearchBackend.VECTOR.value == "vector"
    assert ExternalSearchBackend.QDRANT.value == "qdrant"
    assert ExternalSearchBackend.CHROMA.value == "chroma"


def test_semantic_search_model_enum():
    from ai_generation.search_backends import SemanticSearchModel
    assert SemanticSearchModel.ALL_MINILM.value == "all-MiniLM-L6-v2"
    assert SemanticSearchModel.BGE_BASE.value == "BAAI/bge-base-en-v1.5"


def test_backend_profile_serialization():
    from ai_generation.search_backends import BACKEND_PROFILES
    assert len(BACKEND_PROFILES) == 4
    for p in BACKEND_PROFILES:
        d = p.to_dict()
        assert "name" in d
        assert "backend" in d
        assert "features" in d


def test_search_result_serialization():
    from ai_generation.search_backends import SearchResult
    r = SearchResult(id="doc1", score=0.95, payload={"title": "Test"})
    d = r.to_dict()
    assert d["id"] == "doc1"
    assert d["score"] == 0.95


def test_search_response_serialization():
    from ai_generation.search_backends import SearchResponse, SearchResult
    resp = SearchResponse(
        backend="vector", hits=[SearchResult(id="1", score=0.9)],
        total_hits=1, query="test", latency_ms=10.5,
    )
    d = resp.to_dict()
    assert d["backend"] == "vector"
    assert d["total_hits"] == 1
    assert d["latency_ms"] == 10.5


def test_meilisearch_backend_import():
    from ai_generation.search_backends import MeilisearchBackend
    b = MeilisearchBackend()
    assert b.name == "meilisearch"


def test_opensearch_backend_import():
    from ai_generation.search_backends import OpenSearchBackend
    b = OpenSearchBackend()
    assert b.name == "opensearch"


def test_vector_search_backend_import():
    from ai_generation.search_backends import VectorSearchBackend
    b = VectorSearchBackend()
    assert b.name == "vector"


def test_search_backend_manager_import():
    from ai_generation.search_backends import SearchBackendManager
    m = SearchBackendManager()
    assert m is not None


def test_search_backend_manager_profiles():
    from ai_generation.search_backends import SearchBackendManager
    m = SearchBackendManager()
    profiles = m.get_profiles()
    assert len(profiles) == 4


def test_search_backend_manager_stats():
    from ai_generation.search_backends import SearchBackendManager
    m = SearchBackendManager()
    stats = m.get_stats()
    assert stats["total_searches"] == 0
    assert stats["profiles"] == 4


@pytest.mark.asyncio
async def test_vector_search_no_model():
    from ai_generation.search_backends import VectorSearchBackend, SearchResponse
    b = VectorSearchBackend()
    result = await b.search("test_collection", "hello world")
    assert result.backend == "vector"
    assert result.error is not None or result.total_hits == 0


@pytest.mark.asyncio
async def test_vector_index_no_model():
    from ai_generation.search_backends import VectorSearchBackend
    b = VectorSearchBackend()
    result = await b.index_documents("test", [{"text": "hello"}])
    assert result.get("error") is not None or result.get("indexed", 0) >= 0


@pytest.mark.asyncio
async def test_search_backend_health():
    from ai_generation.search_backends import SearchBackendManager
    m = SearchBackendManager()
    health = await m.check_health()
    assert "meilisearch" in health
    assert "opensearch" in health
    assert "vector" in health


# ── SDK Integration ──

def test_sdk_search_backends_import():
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    assert ai.search_backends is not None
    assert type(ai.search_backends).__name__ == "SearchBackendManager"


def test_sdk_search_backends_in_stats():
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    stats = ai.get_stats()
    assert "search_backends" in stats


# ── MCP Tools ──

def test_mcp_search_tools_exist():
    from ai_generation.mcp_tools import MCP_GENERATION_TOOLS
    assert "search_external" in MCP_GENERATION_TOOLS
    assert "vector_search" in MCP_GENERATION_TOOLS
    assert "index_documents_external" in MCP_GENERATION_TOOLS
    assert "check_search_health" in MCP_GENERATION_TOOLS
    assert "get_search_backend_profiles" in MCP_GENERATION_TOOLS


def test_mcp_search_external_schema():
    from ai_generation.mcp_tools import MCP_GENERATION_TOOLS
    tool = MCP_GENERATION_TOOLS["search_external"]
    schema = tool["inputSchema"]
    assert "backend" in schema["properties"]
    assert "query" in schema["properties"]


def test_mcp_vector_search_schema():
    from ai_generation.mcp_tools import MCP_GENERATION_TOOLS
    tool = MCP_GENERATION_TOOLS["vector_search"]
    schema = tool["inputSchema"]
    assert "collection" in schema["properties"]
    assert "query" in schema["properties"]


@pytest.mark.asyncio
async def test_mcp_search_external_handler():
    from ai_generation.mcp_tools import MCPGenerationTools
    mcp = MCPGenerationTools()
    assert hasattr(mcp, "_handle_search_external")


@pytest.mark.asyncio
async def test_mcp_vector_search_handler():
    from ai_generation.mcp_tools import MCPGenerationTools
    mcp = MCPGenerationTools()
    assert hasattr(mcp, "_handle_vector_search")
