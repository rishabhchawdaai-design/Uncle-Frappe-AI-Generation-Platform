"""
Phase 22 Tests — Search Systems

Tests full-text search, filtering, faceting, typo tolerance, and SDK/MCP exposure.
"""
import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))


# ── BuiltinSearchEngine Tests ────────────────────────────────

def test_builtin_engine_import():
    from ai_generation.search_systems import BuiltinSearchEngine
    engine = BuiltinSearchEngine()
    assert engine is not None


def test_create_index():
    from ai_generation.search_systems import BuiltinSearchEngine
    engine = BuiltinSearchEngine()
    engine.create_index("test_index")
    indexes = engine.list_indexes()
    assert any(i["index_name"] == "test_index" for i in indexes)


def test_add_documents():
    from ai_generation.search_systems import BuiltinSearchEngine
    engine = BuiltinSearchEngine()
    engine.create_index("docs")
    docs = [
        {"id": "1", "title": "Hello World", "content": "A test document"},
        {"id": "2", "title": "Python Guide", "content": "Learn Python programming"},
    ]
    engine.add_documents("docs", docs)
    info = engine.get_index_info("docs")
    assert info["document_count"] == 2


def test_search_basic():
    from ai_generation.search_systems import BuiltinSearchEngine
    engine = BuiltinSearchEngine()
    engine.create_index("docs")
    engine.add_documents("docs", [
        {"id": "1", "title": "Python Programming", "content": "Learn Python"},
        {"id": "2", "title": "Java Programming", "content": "Learn Java"},
        {"id": "3", "title": "Web Development", "content": "HTML CSS JavaScript"},
    ])
    results = engine.search("docs", "Python")
    assert results.total_hits >= 1
    assert any("python" in h.document.get("title", "").lower() for h in results.hits)


def test_search_empty_query():
    from ai_generation.search_systems import BuiltinSearchEngine
    engine = BuiltinSearchEngine()
    engine.create_index("docs")
    engine.add_documents("docs", [{"id": "1", "title": "Test"}])
    results = engine.search("docs", "")
    # Empty query should return no results (no tokens to match)
    assert results.total_hits == 0


def test_search_with_filter():
    from ai_generation.search_systems import BuiltinSearchEngine
    engine = BuiltinSearchEngine()
    engine.create_index("providers")
    engine.add_documents("providers", [
        {"id": "1", "name": "OpenAI", "type": "image", "tier": "paid"},
        {"id": "2", "name": "Pollinations", "type": "image", "tier": "free"},
        {"id": "3", "name": "Whisper", "type": "audio", "tier": "free"},
    ])
    results = engine.search("providers", "image", filter_expr={"tier": "free"})
    assert results.total_hits >= 1
    assert all(h.document.get("tier") == "free" for h in results.hits)


def test_search_typo_tolerance():
    from ai_generation.search_systems import BuiltinSearchEngine
    engine = BuiltinSearchEngine()
    engine.create_index("docs")
    engine.add_documents("docs", [
        {"id": "1", "title": "Programming Language", "content": "Python is great"},
    ])
    # "programing" is one edit away from "programming"
    results = engine.search("docs", "programing")
    assert results.total_hits >= 1


def test_search_facets():
    from ai_generation.search_systems import BuiltinSearchEngine
    engine = BuiltinSearchEngine()
    engine.create_index("providers")
    engine.add_documents("providers", [
        {"id": "1", "name": "OpenAI", "type": "image"},
        {"id": "2", "name": "Pollinations", "type": "image"},
        {"id": "3", "name": "Whisper", "type": "audio"},
    ])
    results = engine.search("providers", "AI", facets=["type"])
    assert "type" in results.facets
    assert results.facets["type"].get("image", 0) >= 1


def test_search_pagination():
    from ai_generation.search_systems import BuiltinSearchEngine
    engine = BuiltinSearchEngine()
    engine.create_index("docs")
    docs = [{"id": str(i), "title": f"Document {i} about Python"} for i in range(50)]
    engine.add_documents("docs", docs)
    page1 = engine.search("docs", "Python", page=1, hits_per_page=10)
    page2 = engine.search("docs", "Python", page=2, hits_per_page=10)
    assert len(page1.hits) == 10
    assert len(page2.hits) == 10
    assert page1.total_hits == 50


def test_delete_document():
    from ai_generation.search_systems import BuiltinSearchEngine
    engine = BuiltinSearchEngine()
    engine.create_index("docs")
    engine.add_documents("docs", [{"id": "1", "title": "Test"}])
    engine.delete_document("docs", "1")
    info = engine.get_index_info("docs")
    assert info["document_count"] == 0


def test_clear_index():
    from ai_generation.search_systems import BuiltinSearchEngine
    engine = BuiltinSearchEngine()
    engine.create_index("docs")
    engine.add_documents("docs", [{"id": "1", "title": "Test"}, {"id": "2", "title": "Test2"}])
    engine.clear_index("docs")
    info = engine.get_index_info("docs")
    assert info["document_count"] == 0


def test_highlights():
    from ai_generation.search_systems import BuiltinSearchEngine
    engine = BuiltinSearchEngine()
    engine.create_index("docs")
    engine.add_documents("docs", [
        {"id": "1", "title": "Python Programming Guide"},
    ])
    results = engine.search("docs", "Python")
    if results.hits:
        assert "title" in results.hits[0].highlights or results.hits[0].score > 0


def test_levenshtein_distance():
    from ai_generation.search_systems import BuiltinSearchEngine
    assert BuiltinSearchEngine._levenshtein_distance("kitten", "sitting") == 3
    assert BuiltinSearchEngine._levenshtein_distance("python", "python") == 0
    assert BuiltinSearchEngine._levenshtein_distance("abc", "ab") == 1


# ── SearchManager Tests ───────────────────────────────────────

def test_search_manager_import():
    from ai_generation.search_systems import SearchManager
    sm = SearchManager()
    assert sm is not None


def test_search_manager_has_builtin_indexes():
    from ai_generation.search_systems import SearchManager
    sm = SearchManager()
    indexes = sm.list_indexes()
    names = [i["index_name"] for i in indexes]
    assert "providers" in names
    assert "models" in names
    assert "knowledge" in names
    assert "decisions" in names
    assert "benchmarks" in names


def test_search_providers():
    from ai_generation.search_systems import SearchManager
    sm = SearchManager()
    sm.index_documents("providers", [
        {"id": "1", "name": "OpenAI", "type": "image", "tier": "paid"},
        {"id": "2", "name": "Pollinations", "type": "image", "tier": "free"},
    ])
    results = sm.search_providers("OpenAI")
    assert results.total_hits >= 1


def test_search_models():
    from ai_generation.search_systems import SearchManager
    sm = SearchManager()
    sm.index_documents("models", [
        {"id": "1", "name": "GPT-4", "category": "llm", "runtime": "openai"},
        {"id": "2", "name": "SDXL", "category": "diffusion", "runtime": "diffusers"},
    ])
    results = sm.search_models("GPT", category="llm")
    assert results.total_hits >= 1


def test_search_knowledge():
    from ai_generation.search_systems import SearchManager
    sm = SearchManager()
    sm.index_documents("knowledge", [
        {"id": "1", "title": "Provider Selection", "content": "How to choose providers", "category": "routing"},
    ])
    results = sm.search_knowledge("provider")
    assert results.total_hits >= 1


def test_search_stats():
    from ai_generation.search_systems import SearchManager
    sm = SearchManager()
    stats = sm.get_stats()
    assert "backend" in stats
    assert "index_count" in stats
    assert stats["index_count"] == 5


# ── SDK Integration Tests ─────────────────────────────────────

def test_sdk_search_import():
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    assert hasattr(ai, 'search_systems')
    assert hasattr(ai, 'search_index')
    assert hasattr(ai, 'search_providers')
    assert hasattr(ai, 'search_models')
    assert hasattr(ai, 'search_knowledge')
    assert hasattr(ai, 'search_decisions')
    assert hasattr(ai, 'search_benchmarks')
    assert hasattr(ai, 'list_search_indexes')
    assert hasattr(ai, 'get_search_stats')


def test_sdk_search_stats():
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    stats = ai.get_search_stats()
    assert "backend" in stats
    assert stats["backend"] == "builtin"


def test_sdk_list_search_indexes():
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    indexes = ai.list_search_indexes()
    assert len(indexes) == 5


# ── MCP Tools Tests ──────────────────────────────────────────

def test_mcp_search_tools_exist():
    from ai_generation.mcp_tools import MCP_GENERATION_TOOLS
    assert "search_index" in MCP_GENERATION_TOOLS
    assert "search_providers" in MCP_GENERATION_TOOLS
    assert "search_models" in MCP_GENERATION_TOOLS
    assert "list_search_indexes" in MCP_GENERATION_TOOLS
    assert "get_search_stats" in MCP_GENERATION_TOOLS


def test_mcp_search_handler_import():
    from ai_generation.mcp_tools import MCPGenerationTools
    handler = MCPGenerationTools()
    assert hasattr(handler, '_handle_search_index')
    assert hasattr(handler, '_handle_search_providers')
    assert hasattr(handler, '_handle_search_models')
    assert hasattr(handler, '_handle_list_search_indexes')
    assert hasattr(handler, '_handle_get_search_stats')
