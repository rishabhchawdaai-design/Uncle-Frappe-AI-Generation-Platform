# Research MCP Stack — Sections 3-10: Complete Research Infrastructure

**161 tools** across 8 sections, fully integrated with unified orchestration, Docker services, MCP adapters, health checks, and Raipur-focused collection profiles.

---

## Section Overview

| Section | Name | Tools | Focus |
|---------|------|:-----:|-------|
| **3** | Search MCPs | 20 | Web search, academic search, metasearch, AI search |
| **4** | Local Raipur Data | 20 | Maps, directories, government, business portals |
| **5** | Social Data | 20 | All major social platforms + feeds |
| **6** | AI Research Agents | 20 | Multi-agent frameworks, RAG, automation |
| **7** | OCR & Documents | 20 | PDF, OCR, table extraction, document parsing |
| **8** | Knowledge Graph | 20 | Graph DBs, vector stores, search engines |
| **9** | Data Validation | 20 | Dedup, fact-check, provenance, quality |
| **10** | Raipur Targets | 21 | 20 business categories + composite BI |

## Quick Start

```bash
# Health check all 161 tools
PYTHONPATH=. python sections/health_check.py

# Search across tools
PYTHONPATH=. python sections/cli.py search "Raipur restaurants" search

# Raipur target research
PYTHONPATH=. python sections/cli.py raipur restaurants

# View statistics
PYTHONPATH=. python sections/cli.py stats

# List Raipur targets
PYTHONPATH=. python sections/cli.py targets
```

## Section 3 — Search MCPs (20)

| Tool | API Key | MCP Server | Capabilities |
|------|:-------:|:----------:|-------------|
| Exa | ✅ | ✅ | Neural search, similarity, contents |
| Tavily | ✅ | ✅ | Search, extract, QA |
| Brave Search | ✅ | ✅ | Web, news, images, videos |
| DuckDuckGo | — | — | Web, instant answers |
| Google PSE | ✅ | — | Custom search, CSE |
| Bing Search | ✅ | — | Web, news, images |
| SearXNG | — | — | Metasearch, privacy, self-hosted |
| Perplexity | ✅ | — | AI search, citations, real-time |
| Jina | ✅ | — | Search, reader, deep research |
| SerpAPI | ✅ | — | Multi-engine, local, scholar |
| Serper | ✅ | — | Google, images, places |
| Kagi | ✅ | — | Ad-free, privacy, summarizer |
| Metaphor | ✅ | — | Neural, similar, contents |
| YaCy | — | — | P2P, self-hosted, distributed |
| Common Crawl | — | — | Web archive, bulk data |
| OpenAlex | — | — | Academic, works, authors |
| Crossref | — | — | Academic, DOI, citations |
| Semantic Scholar | ✅ | — | Academic, TLDR, author |
| Europe PMC | — | — | Biomedical, open access |
| Wikidata | — | — | Entities, SPARQL, structured |

## Section 4 — Local Raipur Data (20)

| Tool | API Key | Capabilities |
|------|:-------:|-------------|
| Google Maps | ✅ | Places, geocoding, reviews, photos |
| OpenStreetMap | — | Nominatim, Overpass, POI |
| Mapbox | ✅ | Geocoding, static maps, directions |
| Foursquare | ✅ | Venues, tips, categories |
| Yelp | ✅ | Business search, reviews |
| TripAdvisor | — | Locations, reviews, attractions |
| Zomato | ✅ | Restaurants, reviews, menus |
| Swiggy | — | Restaurants, delivery, offers |
| Magicpin | — | Local deals, restaurants |
| JustDial | — | Business directory, contact |
| IndiaMART | — | Suppliers, products |
| Sulekha | — | Local services, businesses |
| Yellow Pages India | — | Business directory |
| CG Government | — | Schemes, notices, departments |
| Raipur Smart City | — | Projects, citizen services |
| Raipur Municipal Corp | — | Tax, permits, services |
| MSME Portal | — | Registration, subsidies |
| Startup India | — | Startups, funding |
| GeM | — | Government procurement |
| Data.gov.in | — | Open datasets, APIs |

## Section 5 — Social Data (20)

| Tool | API Key | MCP | Capabilities |
|------|:-------:|:---:|-------------|
| Reddit | — | ✅ | Posts, comments, subreddits |
| X/Twitter | ✅ | ✅ | Posts, search, trends |
| Facebook | ✅ | — | Pages, reviews |
| Instagram | ✅ | — | Posts, hashtags, location |
| Threads | — | — | Posts, search |
| LinkedIn | ✅ | — | Company, people, jobs |
| YouTube | ✅ | — | Videos, channels, playlists |
| Telegram | — | — | Channels, messages |
| Discord | — | — | Servers, messages |
| Pinterest | ✅ | — | Pins, boards |
| Quora | — | — | Questions, answers |
| Medium | — | — | Articles, publications |
| Substack | — | — | Newsletters, articles |
| Tumblr | — | — | Posts, blogs, tags |
| Flickr | ✅ | — | Photos, geotags |
| Vimeo | — | — | Videos, channels |
| Mastodon | — | — | Toots, federated |
| Bluesky | — | — | Posts, feeds |
| Hacker News | — | — | Stories, comments |
| Product Hunt | ✅ | — | Products, hunters |

## Section 6 — AI Research Agents (20)

| Tool | Capabilities |
|------|-------------|
| OpenHands | Coding, browser, terminal |
| OpenManus | Browser agent, file ops |
| CrewAI | Multi-agent, tasks, tools |
| AutoGen | Multi-agent, chat, code |
| LangGraph | State graph, persistence |
| LangChain | Chains, agents, retrieval |
| SmolAgents | Code agent, lightweight |
| Haystack | Pipelines, retrieval, generation |
| DSPy | Modules, optimizers, signatures |
| LlamaIndex | Indexing, RAG, workflows |
| CamelAI | Role-playing, multi-agent |
| MetaGPT | Multi-agent, software dev |
| SuperAGI | Autonomous, tool use |
| AgentVerse | Simulation, debate |
| OpenDevin | Coding, sandbox |
| GPT Researcher | Deep research, reports |
| AgentReach | Web scraping, extraction |
| Browser Use | AI browsing, multi-step |
| AutoScraper | Pattern learning |
| Deep Research | Multi-hop, iterative |

## Section 7 — OCR & Documents (20)

| Tool | Capabilities |
|------|-------------|
| Docling | Document parsing, table extraction |
| Marker | PDF to Markdown, layout |
| OCRmyPDF | Searchable PDF, lossless |
| Tesseract | OCR, multi-language |
| PaddleOCR | Layout, table, Chinese/Hindi |
| EasyOCR | 80+ languages |
| Surya OCR | Layout, line detection |
| Nougat | Scientific PDF, equations |
| PyMuPDF | PDF read, search, images |
| pdfplumber | Table extraction |
| Camelot | PDF tables, lattice/stream |
| Tabula | Java-based table extraction |
| Unstructured | Partition, chunking, multi-format |
| Apache Tika | Content extraction, metadata |
| GROBID | Scholarly PDF, TEI XML |
| pymupdf4llm | PDF to LLM-ready Markdown |
| LayoutParser | Document layout detection |
| Marker PDF | Batch PDF conversion |
| MinerU | PDF parsing, OCR |
| Poppler | PDF utilities, CLI |

## Section 8 — Knowledge Graph (20)

| Tool | Type | MCP | Capabilities |
|------|------|:---:|-------------|
| Neo4j | Graph DB | ✅ | Cypher, ACID, OLAP |
| Memgraph | Graph DB | — | In-memory, streaming |
| FalkorDB | Graph DB | — | Redis-compatible, fast |
| TypeDB | Graph DB | — | Logic programming, reasoning |
| ArangoDB | Multi-model | — | Graph + document + KV |
| RDFLib | RDF | — | SPARQL, OWL, triples |
| Blazegraph | Triplestore | — | SPARQL, OLAP |
| Graphiti | Temporal | — | Episodic, entity resolution |
| NetworkX | Analysis | — | Centrality, community |
| Apache Jena | Triplestore | — | SPARQL, Fuseki |
| Weaviate | Vector DB | ✅ | Semantic, hybrid, GraphQL |
| Qdrant | Vector DB | ✅ | Similarity, filtering |
| Milvus | Vector DB | — | Scalable, GPU, hybrid |
| ChromaDB | Vector DB | ✅ | Lightweight, local |
| LanceDB | Vector DB | — | Serverless, multi-modal |
| FAISS | Vector | — | Efficient, GPU |
| pgvector | Vector DB | — | PostgreSQL, SQL |
| Vespa | Search | — | Hybrid, real-time |
| OpenSearch | Search | — | Analytics, KNN |
| Elasticsearch | Search | ✅ | Full-text, ML |

## Section 9 — Data Validation (20)

| Module | Capabilities |
|--------|-------------|
| Deduplication | Text dedup, fuzzy match, exact hash |
| Entity Resolution | Fuzzy match, disambiguation |
| Citation Verification | URL check, DOI check |
| Source Ranking | Authority, reliability |
| Confidence Scoring | Evidence weight, certainty |
| Provenance Tracking | Lineage, audit trail |
| Fact Verification | Claim check, verdict |
| Hallucination Detection | Grounding, factuality |
| Temporal Validation | Date check, recency |
| Geographical Validation | Geo check, bounding box |
| Duplicate Image Detection | Perceptual hash |
| URL Health Check | Status, SSL, response time |
| Dead Link Detection | Broken detection |
| Schema Validation | JSON schema, Pydantic |
| Language Detection | Language, script |
| Translation Verification | Back-translate, quality |
| Metadata Validation | Completeness, consistency |
| Evidence Ranking | Relevance, quality score |
| Cross-source Consensus | Agreement, confidence |
| Canonical Record Builder | Merge, golden record |

## Section 10 — Raipur Research Targets (21)

| Target | Keywords | Schedule | Primary Sources |
|--------|:--------:|----------|----------------|
| Restaurants | 5 | Daily | Zomato, Swiggy, Google Maps |
| Cafes | 4 | Daily | Zomato, Google Maps |
| Hotels | 5 | Daily | TripAdvisor, Google Maps |
| Cloud Kitchens | 4 | Weekly | Swiggy, Zomato |
| Bakeries | 4 | Weekly | Zomato, Google Maps |
| Food Trucks | 3 | Weekly | Google Maps, Instagram |
| Street Food | 5 | Weekly | TripAdvisor, YouTube |
| Shopping Malls | 3 | Monthly | Google Maps, JustDial |
| Markets | 5 | Monthly | Google Maps, OSM |
| Colleges | 4 | Monthly | Google Maps, OpenAlex |
| Schools | 4 | Monthly | Google Maps, Sulekha |
| Hospitals | 5 | Weekly | Google Maps, Practo |
| Tourist Places | 5 | Monthly | TripAdvisor, YouTube |
| Events | 5 | Daily | Google Maps, Instagram |
| Festivals | 5 | Monthly | YouTube, Instagram |
| Startups | 4 | Monthly | Startup India, LinkedIn |
| IT Companies | 4 | Monthly | LinkedIn, IndiaMART |
| Government Offices | 4 | Monthly | CG Gov, JustDial |
| Local News | 5 | Hourly | Google, Tavily, X |
| Business Intelligence | 11 | Daily | Data.gov.in, 99acres |
| **BI Composite** | — | Daily | **All targets combined** |

## Project Structure

```
sections/
├── base.py                         # Shared BaseTool, ToolResult, ToolCategory
├── unified_orchestrator.py         # Master orchestrator (161 tools)
├── health_check.py                 # Full health check
├── cli.py                          # CLI interface
├── mcp_registry.json               # MCP server configs
├── README.md
├── search_mcp/wrappers/search_tools.py         # Section 3 (20)
├── raipur_data/wrappers/raipur_tools.py        # Section 4 (20)
├── social_data/wrappers/social_tools.py        # Section 5 (20)
├── ai_research/wrappers/ai_tools.py            # Section 6 (20)
├── ocr_docs/wrappers/ocr_tools.py              # Section 7 (20)
├── knowledge_graph/wrappers/kg_tools.py        # Section 8 (20)
├── data_validation/wrappers/validation_tools.py # Section 9 (20)
├── raipur_targets/wrappers/raipur_targets.py   # Section 10 (21)
└── docker/
    ├── docker-compose.yml           # 15 service definitions
    └── nginx.conf                   # API gateway
```
