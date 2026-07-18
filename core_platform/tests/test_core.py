"""Core platform tests."""
import asyncio, pytest, json, hashlib, os, tempfile

# ── Data Quality Tests ────────────────────────────────────────────
def test_deduplication():
    from core_platform.quality.data_quality import DuplicateDetector
    dd = DuplicateDetector()
    assert not dd.is_exact_duplicate("Hello World")
    assert dd.is_exact_duplicate("Hello World")  # second time = duplicate
    assert not dd.is_exact_duplicate("Different text")

def test_jaccard_similarity():
    from core_platform.quality.data_quality import DuplicateDetector
    dd = DuplicateDetector()
    assert dd.jaccard_similarity("hello world foo", "hello world bar") >= 0.5
    assert dd.jaccard_similarity("hello", "completely different") < 0.3

def test_schema_validation():
    from core_platform.quality.data_quality import SchemaValidator
    sv = SchemaValidator()
    result = sv.validate({"title": "Test", "url": "http://example.com"}, {"title": str, "url": str})
    assert result["valid"] is True
    result2 = sv.validate({"title": 123}, {"title": str})
    assert result2["valid"] is False

def test_text_repair():
    from core_platform.quality.data_quality import AutomaticRepair
    r = AutomaticRepair()
    assert r.repair_text("Hello  <b>World</b>  ") == "Hello World"
    assert r.repair_url("example.com") == "https://example.com"
    assert r.repair_date("2024-01-15") == "2024-01-15T00:00:00"

def test_source_reliability():
    from core_platform.quality.data_quality import SourceReliabilityScorer
    s = SourceReliabilityScorer()
    assert s.score("https://en.wikipedia.org/wiki/Raipur") >= 80
    assert s.score("https://gov.in/something") >= 85

def test_language_detection():
    from core_platform.quality.data_quality import LanguageDetector
    ld = LanguageDetector()
    result = ld.detect("Hello world this is English text")
    assert result["language"] == "en"
    result_hi = ld.detect("यह हिंदी में लिखा गया है रायपुर")
    assert result_hi["language"] == "hi"


# ── Knowledge Graph Tests ─────────────────────────────────────────
def test_kg_entity_extraction():
    from core_platform.knowledge_graph.graph_engine import KnowledgeGraphEngine
    kg = KnowledgeGraphEngine(storage_path=tempfile.mkdtemp())
    result = kg.extract_from_text("Hotel Taj Raipur is located in Raipur Chhattisgarh. It serves Indian food.", "test")
    assert result["new_entities"] > 0

def test_kg_analytics():
    from core_platform.knowledge_graph.graph_engine import KnowledgeGraphEngine
    from core_platform.knowledge_graph.graph_engine import Entity, Relationship
    kg = KnowledgeGraphEngine(storage_path=tempfile.mkdtemp())
    kg._entities["e1"] = Entity(id="e1", name="Taj Hotel", entity_type="hotel")
    kg._entities["e2"] = Entity(id="e2", name="Raipur", entity_type="city")
    kg._relationships["r1"] = Relationship(source_id="e1", target_id="e2", relation_type="located_in")
    analytics = kg.get_analytics()
    assert analytics["total_entities"] == 2
    assert analytics["total_relationships"] == 1

def test_kg_cypher():
    from core_platform.knowledge_graph.graph_engine import KnowledgeGraphEngine, Entity, Relationship
    kg = KnowledgeGraphEngine(storage_path=tempfile.mkdtemp())
    kg._entities["e1"] = Entity(id="e1", name="Test", entity_type="restaurant")
    queries = kg.to_cypher()
    assert len(queries) > 0
    assert "CREATE" in queries[0]


# ── Vector Store Tests ────────────────────────────────────────────
@pytest.mark.asyncio
@pytest.mark.skipif(True, reason="chromadb not installed")
async def test_chroma_store():
    from core_platform.vector_store.multi_vector_store import ChromaStore, VectorRecord
    import tempfile
    store = ChromaStore(path=tempfile.mkdtemp())
    records = [VectorRecord(id="test1", text="Raipur is in Chhattisgarh", embedding=[0.1]*384, metadata={"source": "test"})]
    count = await store.index(records)
    assert count == 1
    results = await store.search([0.1]*384, k=1)
    assert len(results) > 0

@pytest.mark.asyncio
@pytest.mark.skipif(True, reason="faiss not installed")
async def test_faiss_store():
    from core_platform.vector_store.multi_vector_store import FaissStore, VectorRecord
    import tempfile, numpy as np
    store = FaissStore(dimension=64, path=tempfile.mkdtemp())
    emb = np.random.rand(64).tolist()
    records = [VectorRecord(id="test1", text="Test document", embedding=emb)]
    count = await store.index(records)
    assert count == 1
    results = await store.search(emb, k=1)
    assert len(results) > 0


# ── Chunker Tests ─────────────────────────────────────────────────
def test_semantic_chunking():
    from core_platform.rag.hybrid_rag import Chunker
    chunker = Chunker(chunk_size=50, chunk_overlap=10)
    text = "Paragraph one about Raipur.\n\nParagraph two about Chhattisgarh.\n\nParagraph three about India."
    chunks = chunker.chunk_text(text, "doc1", "Test", "semantic")
    assert len(chunks) > 0
    assert all(c.document_id == "doc1" for c in chunks)

def test_fixed_chunking():
    from core_platform.rag.hybrid_rag import Chunker
    chunker = Chunker(chunk_size=20, chunk_overlap=5)
    text = " ".join(["word"] * 100)
    chunks = chunker.chunk_text(text, "doc1", "Test", "fixed")
    assert len(chunks) > 1

def test_hierarchical_chunking():
    from core_platform.rag.hybrid_rag import Chunker
    chunker = Chunker(chunk_size=30, chunk_overlap=5)
    text = " ".join(["paragraph about Raipur"] * 20)
    chunks = chunker.chunk_text(text, "doc1", "Test", "hierarchical")
    hier_chunks = [c for c in chunks if c.metadata.get("hierarchical_level")]
    assert len(hier_chunks) > 0


# ── Crawler Tests ─────────────────────────────────────────────────
def test_rate_limiter():
    from core_platform.crawler.distributed_crawler import RateLimiter
    rl = RateLimiter(requests_per_second=10, burst=5)
    assert rl._rps == 10

def test_content_fingerprinter():
    from core_platform.crawler.distributed_crawler import ContentFingerprinter
    import tempfile
    fp = ContentFingerprinter(storage_path=tempfile.mkdtemp())
    h1 = fp.compute("Hello World")
    h2 = fp.compute("Hello World")
    h3 = fp.compute("Different Text")
    assert h1 == h2
    assert h1 != h3

def test_change_detection():
    from core_platform.crawler.distributed_crawler import ChangeDetector
    import tempfile
    cd = ChangeDetector(storage_path=tempfile.mkdtemp())
    cd.record("http://test.com", "hash1", True)
    cd.record("http://test.com", "hash1", False)
    assert cd.get_change_count("http://test.com") == 1


# ── Agent Tests ───────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_agent_orchestrator():
    from core_platform.agents.agent_system import AgentOrchestrator
    orch = AgentOrchestrator()
    assert len(orch._agents) == 20
    await orch.start_all()
    status = await orch.get_all_status()
    assert "coordinator" in status
    assert status["coordinator"]["running"] is True
    await orch.stop_all()


# ── Observability Tests ───────────────────────────────────────────
def test_metrics_collector():
    from core_platform.observability.metrics import MetricsCollector
    m = MetricsCollector()
    m.counter("test_counter", 5)
    m.gauge("test_gauge", 42)
    m.histogram("test_histogram", 0.5)
    prom = m.to_prometheus()
    assert "test_counter" in prom
    assert "test_gauge" in prom

def test_structured_logger():
    from core_platform.observability.metrics import StructuredLogger
    import tempfile
    log = StructuredLogger("test", log_dir=tempfile.mkdtemp())
    entry = log.info("Test message", context="test")
    assert entry["level"] == "INFO"

def test_tracing():
    from core_platform.observability.metrics import TracingMiddleware
    trace = TracingMiddleware()
    tid = trace.start_trace("test_operation")
    assert len(trace.get_traces()) > 0
    trace.end_trace(tid)
    traces = trace.get_traces()
    assert traces[-1]["status"] == "ok"


# ── BI Tests ──────────────────────────────────────────────────────
def test_bi_categories():
    from core_platform.bi.raipur_bi import BICATEGORIES
    assert "restaurants" in BICATEGORIES
    assert "hotels" in BICATEGORIES
    assert "demographics" in BICATEGORIES
    assert len(BICATEGORIES) >= 15

def test_bi_report():
    from core_platform.bi.raipur_bi import RaipurBICollector
    import tempfile
    bi = RaipurBICollector({"output_dir": tempfile.mkdtemp()})
    report = bi.generate_report()
    assert "generated_at" in report
