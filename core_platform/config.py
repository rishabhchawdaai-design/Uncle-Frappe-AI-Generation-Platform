"""Production configuration with environment-based secrets."""
import os
from dataclasses import dataclass, field
from typing import Optional

@dataclass(frozen=True)
class PlatformConfig:
    # Search
    exa_api_key: str = field(default_factory=lambda: os.environ.get("EXA_API_KEY", ""))
    tavily_api_key: str = field(default_factory=lambda: os.environ.get("TAVILY_API_KEY", ""))
    brave_api_key: str = field(default_factory=lambda: os.environ.get("BRAVE_API_KEY", ""))
    google_api_key: str = field(default_factory=lambda: os.environ.get("GOOGLE_API_KEY", ""))
    google_cx: str = field(default_factory=lambda: os.environ.get("GOOGLE_CX", ""))
    serper_api_key: str = field(default_factory=lambda: os.environ.get("SERPER_API_KEY", ""))
    serpapi_key: str = field(default_factory=lambda: os.environ.get("SERPAPI_KEY", ""))

    # Vector DB
    qdrant_url: str = field(default_factory=lambda: os.environ.get("QDRANT_URL", "http://localhost:6333"))
    weaviate_url: str = field(default_factory=lambda: os.environ.get("WEAVIATE_URL", "http://localhost:8080"))
    chroma_path: str = field(default_factory=lambda: os.environ.get("CHROMA_PATH", "./data/chroma"))
    milvus_uri: str = field(default_factory=lambda: os.environ.get("MILVUS_URI", "./data/milvus.db"))
    pgvector_dsn: str = field(default_factory=lambda: os.environ.get("PGVECTOR_DSN", "postgresql://localhost:5432/vectordb"))
    lancedb_path: str = field(default_factory=lambda: os.environ.get("LANCEDB_PATH", "./data/lancedb"))
    faiss_path: str = field(default_factory=lambda: os.environ.get("FAISS_PATH", "./data/faiss"))

    # Graph DB
    neo4j_uri: str = field(default_factory=lambda: os.environ.get("NEO4J_URI", "bolt://localhost:7687"))
    neo4j_user: str = field(default_factory=lambda: os.environ.get("NEO4J_USER", "neo4j"))
    neo4j_password: str = field(default_factory=lambda: os.environ.get("NEO4J_PASSWORD", ""))

    # Search engines
    searxng_url: str = field(default_factory=lambda: os.environ.get("SEARXNG_URL", "http://localhost:8080"))
    elasticsearch_url: str = field(default_factory=lambda: os.environ.get("ELASTICSEARCH_URL", "http://localhost:9200"))

    # Crawler
    max_concurrent_requests: int = int(os.environ.get("MAX_CONCURRENT", "10"))
    request_delay_ms: int = int(os.environ.get("REQUEST_DELAY_MS", "1000"))
    max_retries: int = int(os.environ.get("MAX_RETRIES", "3"))
    crawl_timeout: int = int(os.environ.get("CRAWL_TIMEOUT", "30"))
    respect_robots: bool = os.environ.get("RESPECT_ROBOTS", "true").lower() == "true"

    # Embeddings
    embedding_model: str = field(default_factory=lambda: os.environ.get("EMBEDDING_MODEL", "all-MiniLM-L6-v2"))
    embedding_dim: int = int(os.environ.get("EMBEDDING_DIM", "384"))

    # LLM
    openai_api_key: str = field(default_factory=lambda: os.environ.get("OPENAI_API_KEY", ""))
    llm_model: str = field(default_factory=lambda: os.environ.get("LLM_MODEL", "gpt-4o-mini"))

    # Raipur
    raipur_lat: float = 21.2514
    raipur_lng: float = 81.6296

    # Data
    data_dir: str = field(default_factory=lambda: os.environ.get("DATA_DIR", "./data"))
    output_dir: str = field(default_factory=lambda: os.environ.get("OUTPUT_DIR", "./output"))
    log_level: str = field(default_factory=lambda: os.environ.get("LOG_LEVEL", "INFO"))

    # Observability
    prometheus_port: int = int(os.environ.get("PROMETHEUS_PORT", "9090"))
    grafana_port: int = int(os.environ.get("GRAFANA_PORT", "3000"))
    jaeger_url: str = field(default_factory=lambda: os.environ.get("JAEGER_URL", "http://localhost:14268"))

config = PlatformConfig()
