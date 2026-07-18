"""
Research MCP Stack — Production API Server
FastAPI application exposing all platform capabilities.
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import PlainTextResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import asyncio

app = FastAPI(title="Research MCP Stack API", version="1.0.0", description="Production Research Platform")

# ── Lazy-loaded singletons ────────────────────────────────────────
_health_checker = None
_quality_pipeline = None
_kg_engine = None
_vector_manager = None
_crawler = None
_bi_collector = None
_agent_orchestrator = None
_metrics = None
_structured_log = None

def _get_health_checker():
    global _health_checker
    if _health_checker is None:
        from core_platform.validation.health_checker import HealthChecker
        _health_checker = HealthChecker()
    return _health_checker

def _get_quality():
    global _quality_pipeline
    if _quality_pipeline is None:
        from core_platform.quality.data_quality import DataQualityPipeline
        _quality_pipeline = DataQualityPipeline()
    return _quality_pipeline

def _get_kg():
    global _kg_engine
    if _kg_engine is None:
        from core_platform.knowledge_graph.graph_engine import KnowledgeGraphEngine
        _kg_engine = KnowledgeGraphEngine()
    return _kg_engine

def _get_agents():
    global _agent_orchestrator
    if _agent_orchestrator is None:
        from core_platform.agents.agent_system import AgentOrchestrator
        _agent_orchestrator = AgentOrchestrator()
    return _agent_orchestrator

def _get_bi():
    global _bi_collector
    if _bi_collector is None:
        from core_platform.bi.raipur_bi import RaipurBICollector
        _bi_collector = RaipurBICollector()
    return _bi_collector

def _get_metrics():
    global _metrics
    if _metrics is None:
        from core_platform.observability.metrics import MetricsCollector
        _metrics = MetricsCollector()
    return _metrics


# ── Health ────────────────────────────────────────────────────────
@app.get("/health")
async def health():
    return {"status": "ok", "service": "research-mcp-stack", "version": "1.0.0"}

@app.get("/health/tools")
async def health_tools():
    checker = _get_health_checker()
    report = await checker.check_all()
    return {"overall_score": report.overall_score, "healthy": report.healthy_count, "total": report.total_count}

@app.get("/health/tools/{tool_name}")
async def health_tool(tool_name: str):
    checker = _get_health_checker()
    if tool_name in checker._checks:
        result = await checker._run_check(tool_name, checker._checks[tool_name])
        return result.to_dict() if result else {"error": "Check failed"}
    raise HTTPException(404, f"Unknown tool: {tool_name}")


# ── Search ────────────────────────────────────────────────────────
class SearchRequest(BaseModel):
    query: str
    category: str = "search"
    max_results: int = 10

@app.post("/api/search")
async def search(req: SearchRequest):
    from sections.unified_orchestrator import UnifiedOrchestrator
    orch = UnifiedOrchestrator()
    result = await orch.search(req.query, category=req.category)
    return result.to_dict() if hasattr(result, 'to_dict') else {"source": result.source, "status": result.status, "tool": result.tool}


# ── Knowledge Graph ───────────────────────────────────────────────
class KGExtractRequest(BaseModel):
    text: str
    source_id: str = "api"

@app.post("/api/kg/extract")
async def kg_extract(req: KGExtractRequest):
    kg = _get_kg()
    result = kg.extract_from_text(req.text, req.source_id)
    kg.save()
    return result

@app.get("/api/kg/analytics")
async def kg_analytics():
    return _get_kg().get_analytics()

@app.get("/api/kg/entity/{name}")
async def kg_entity(name: str):
    entity = _get_kg().query_entity(name)
    if entity:
        rels = _get_kg().query_relationships(entity.id)
        return {"entity": entity.to_dict(), "relationships": [{"type": r.relation_type, "source": r.source_id, "target": r.target_id} for r in rels]}
    raise HTTPException(404, f"Entity not found: {name}")


# ── Data Quality ──────────────────────────────────────────────────
class QualityRequest(BaseModel):
    records: List[Dict[str, Any]]
    urls: Optional[List[str]] = None

@app.post("/api/quality/validate")
async def quality_validate(req: QualityRequest):
    pipeline = _get_quality()
    return await pipeline.validate_batch(req.records, req.urls)


# ── Raipur BI ─────────────────────────────────────────────────────
@app.post("/api/raipur/collect/{category}")
async def raipur_collect(category: str, background_tasks: BackgroundTasks):
    bi = _get_bi()
    background_tasks.add_task(bi.collect_category, category)
    return {"status": "started", "category": category}

@app.get("/api/raipur/report")
async def raipur_report():
    return _get_bi().generate_report()


# ── Agents ────────────────────────────────────────────────────────
@app.get("/api/agents/status")
async def agents_status():
    return await _get_agents().get_all_status()

@app.post("/api/agents/dispatch/{agent_id}")
async def agents_dispatch(agent_id: str, action: str, payload: Dict[str, Any] = {}):
    return await _get_agents().dispatch(agent_id, action, payload)

@app.get("/api/agents/messages")
async def agents_messages(limit: int = 50):
    return _get_agents().get_message_log(limit)


# ── Metrics (Prometheus) ──────────────────────────────────────────
@app.get("/metrics")
async def metrics():
    m = _get_metrics()
    m.counter("api_requests_total", 1, endpoint="/metrics")
    return PlainTextResponse(m.to_prometheus())

@app.get("/api/metrics/dashboard")
async def metrics_dashboard():
    return _get_metrics().get_dashboard_data()


# ── Crawler ───────────────────────────────────────────────────────
class CrawlRequest(BaseModel):
    urls: List[str]
    max_pages: int = 20
    max_depth: int = 3

@app.post("/api/crawl")
async def crawl(req: CrawlRequest, background_tasks: BackgroundTasks):
    from core_platform.crawler.distributed_crawler import DistributedCrawler
    crawler = DistributedCrawler({"max_concurrent": 5, "max_depth": req.max_depth})
    background_tasks.add_task(crawler.crawl, req.urls, req.max_pages)
    return {"status": "started", "urls": len(req.urls), "max_pages": req.max_pages}

@app.get("/api/crawl/stats")
async def crawl_stats():
    return {"status": "crawler_stats_not_persistent"}


# ── OCR ───────────────────────────────────────────────────────────
@app.post("/api/ocr/tesseract")
async def ocr_tesseract(file_path: str = ""):
    import subprocess
    result = subprocess.run(["tesseract", file_path, "stdout"], capture_output=True, text=True, timeout=30)
    return {"text": result.stdout, "error": result.stderr if result.returncode != 0 else None}
