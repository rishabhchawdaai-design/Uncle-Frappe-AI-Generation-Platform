# Research MCP Stack — Phases 11-20: Production Platform

**200+ tools** across 10 production-ready phases, with a unified orchestrator, real health checks, distributed crawling, hybrid RAG, multi-vector storage, knowledge graph, data quality pipeline, Raipur BI, 20 autonomous agents, observability, and production deployment.

---

## Phase Overview

| Phase | Name | Key Deliverables |
|-------|------|-----------------|
| **11** | Real Tool Validation | 26 live health checks with real operations, latency measurement, health scores |
| **12** | Distributed Crawler | Priority queues, rate limiting, robots.txt, sitemaps, fingerprinting, change detection |
| **13** | Hybrid RAG | Semantic/fixed/hierarchical chunking, embeddings, hybrid retrieval, reranking, citations |
| **14** | Vector Database | Chroma, Qdrant, FAISS, LanceDB — unified interface with sync |
| **15** | Knowledge Graph | Entity extraction, relationship mapping, graph analytics, Cypher export |
| **16** | Data Quality | Dedup, fact-check, source scoring, freshness, schema validation, link checking, auto-repair |
| **17** | Raipur BI | 16 business categories, automated collection, competitor pricing, menus, reports |
| **18** | Autonomous Agents | 20 specialized agents with message bus communication |
| **19** | Observability | Prometheus metrics, structured logging, distributed tracing |
| **20** | Production Deployment | Docker Compose, Dockerfiles, Nginx, HTTPS, CI/CD, GitHub Actions |

## Test Results

```
======================== 21 passed, 2 skipped =========================
- Deduplication:        ✅
- Jaccard similarity:   ✅
- Schema validation:    ✅
- Text repair:          ✅
- Source reliability:    ✅
- Language detection:    ✅
- KG entity extraction: ✅
- KG analytics:         ✅
- KG Cypher export:     ✅
- Semantic chunking:    ✅
- Fixed chunking:       ✅
- Hierarchical chunking:✅
- Rate limiter:         ✅
- Content fingerprint:  ✅
- Change detection:     ✅
- Agent orchestrator:   ✅
- Metrics collector:    ✅
- Structured logging:   ✅
- Distributed tracing:  ✅
- BI categories:        ✅
- BI reporting:         ✅
```

## Quick Start

```bash
# Run tests
PYTHONPATH=. pytest core_platform/tests/ -v

# Run health checks
PYTHONPATH=. python -c "
import asyncio
from core_platform.validation.health_checker import HealthChecker
checker = HealthChecker()
report = asyncio.run(checker.check_all())
print(f'Score: {report.overall_score}% ({report.healthy_count}/{report.total_count})')
"

# Start API server
uvicorn core_platform.api:app --host 0.0.0.0 --port 8000

# Docker deployment
cd core_platform/deployment && docker compose up -d
```

## API Endpoints

```
GET  /health                        Platform health
GET  /health/tools                  Real tool validation (26 tools)
GET  /health/tools/{tool_name}      Individual tool check

POST /api/search                    Hybrid search across all sources
POST /api/kg/extract                Extract entities into knowledge graph
GET  /api/kg/analytics              Graph analytics
GET  /api/kg/entity/{name}          Query entity and relationships

POST /api/quality/validate          Data quality validation batch
POST /api/raipur/collect/{category} Trigger Raipur data collection
GET  /api/raipur/report             Raipur BI report

GET  /api/agents/status             All 20 agent statuses
POST /api/agents/dispatch/{id}      Dispatch task to agent
GET  /api/agents/messages           Inter-agent message log

GET  /metrics                       Prometheus metrics endpoint
GET  /api/metrics/dashboard         Dashboard data

POST /api/crawl                     Start distributed crawl
POST /api/ocr/tesseract             OCR processing
```

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                        API Gateway (FastAPI)                      │
├──────────────────────────────────────────────────────────────────┤
│  Phase 11    │  Phase 12   │  Phase 13   │  Phase 14           │
│  Health      │  Distributed│  Hybrid RAG │  Multi-Vector DB    │
│  Checker     │  Crawler    │  Pipeline   │  Chroma/Qdrant/etc  │
├──────────────┼─────────────┼─────────────┼─────────────────────┤
│  Phase 15    │  Phase 16   │  Phase 17   │  Phase 18           │
│  Knowledge   │  Data       │  Raipur BI  │  20 Autonomous      │
│  Graph       │  Quality    │  Collector  │  Agents             │
├──────────────┴─────────────┴─────────────┴─────────────────────┤
│  Phase 19: Observability (Prometheus, Structured Logs, Tracing) │
├─────────────────────────────────────────────────────────────────┤
│  Phase 20: Docker Compose, CI/CD, Nginx, HTTPS, Backups         │
├─────────────────────────────────────────────────────────────────┤
│  Sections 1-10: Data Collection, Browser Agents, Search, OCR,   │
│  Knowledge Graph, Validation, Raipur Targets (200+ tools)        │
└─────────────────────────────────────────────────────────────────┘
```

## Docker Services (Phase 20)

```bash
cd core_platform/deployment
docker compose up -d

# Services:
#   platform-api     — FastAPI application      (port 8000)
#   searxng          — Metasearch engine         (port 8080)
#   neo4j            — Graph database            (port 7474/7687)
#   qdrant           — Vector database           (port 6333)
#   elasticsearch    — Search engine             (port 9200)
#   redis            — Cache                     (port 6379)
#   prometheus       — Metrics collection        (port 9090)
#   grafana          — Monitoring dashboards     (port 3000)
#   nginx            — Reverse proxy / gateway   (port 80/443)
```

## Project Structure

```
core_platform/
├── __init__.py
├── api.py                            # FastAPI application
├── config.py                         # Environment-based configuration
├── requirements.txt
├── README.md
├── validation/
│   └── health_checker.py             # Phase 11: 26 real health checks
├── crawler/
│   └── distributed_crawler.py        # Phase 12: Full distributed crawler
├── rag/
│   └── hybrid_rag.py                 # Phase 13: Complete RAG pipeline
├── vector_store/
│   └── multi_vector_store.py         # Phase 14: 4 vector backends
├── knowledge_graph/
│   └── graph_engine.py               # Phase 15: KG with extraction
├── quality/
│   └── data_quality.py               # Phase 16: Full quality pipeline
├── bi/
│   └── raipur_bi.py                  # Phase 17: 16 BI categories
├── agents/
│   └── agent_system.py               # Phase 18: 20 autonomous agents
├── observability/
│   └── metrics.py                    # Phase 19: Metrics, logs, traces
├── deployment/
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── prometheus.yml
│   ├── grafana/provisioning/
│   └── nginx.conf
├── tests/
│   └── test_core.py                  # 23 unit tests
└── ...
```
