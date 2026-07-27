"""
Search Backends — Meilisearch, OpenSearch, Vector/Semantic Search.
Extends SearchManager with external search backends and semantic search.
All backends gracefully degrade when services are unavailable.
"""
import hashlib
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False


class ExternalSearchBackend(str, Enum):
    MEILISEARCH = "meilisearch"
    OPENSEARCH = "opensearch"
    VECTOR = "vector"
    QDRANT = "qdrant"
    CHROMA = "chroma"


class SemanticSearchModel(str, Enum):
    ALL_MINILM = "all-MiniLM-L6-v2"
    ALL_MPNET = "all-mpnet-base-v2"
    PARAPHRASE = "paraphrase-MiniLM-L6-v2"
    BGE_SMALL = "BAAI/bge-small-en-v1.5"
    BGE_BASE = "BAAI/bge-base-en-v1.5"
    E5_SMALL = "intfloat/e5-small-v2"


class VectorDBStatus(str, Enum):
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    CONNECTING = "connecting"


@dataclass
class BackendProfile:
    name: str
    backend: ExternalSearchBackend
    description: str
    license: str
    default_url: str
    requires_server: bool
    features: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name, "backend": self.backend.value,
            "description": self.description, "license": self.license,
            "default_url": self.default_url, "requires_server": self.requires_server,
            "features": self.features,
        }


BACKEND_PROFILES: List[BackendProfile] = [
    BackendProfile(
        name="Meilisearch", backend=ExternalSearchBackend.MEILISEARCH,
        description="Fast, typo-tolerant full-text search engine",
        license="MIT", default_url="http://localhost:7700", requires_server=True,
        features=["full-text", "typo-tolerant", "filtering", "faceting", "sorting"],
    ),
    BackendProfile(
        name="OpenSearch", backend=ExternalSearchBackend.OPENSEARCH,
        description="Elasticsearch fork with full-text, vector, and analytics",
        license="Apache-2.0", default_url="http://localhost:9200", requires_server=True,
        features=["full-text", "vector", "analytics", "dashboards", "alerting"],
    ),
    BackendProfile(
        name="Qdrant", backend=ExternalSearchBackend.QDRANT,
        description="High-performance vector similarity search engine",
        license="Apache-2.0", default_url="http://localhost:6333", requires_server=True,
        features=["vector-similarity", "filtering", "clustering", "payload"],
    ),
    BackendProfile(
        name="Chroma", backend=ExternalSearchBackend.CHROMA,
        description="Embedding-native database for AI applications",
        license="Apache-2.0", default_url="http://localhost:8000", requires_server=True,
        features=["vector-similarity", "embedding", "metadata-filtering"],
    ),
]


@dataclass
class SearchResult:
    id: str = ""
    score: float = 0.0
    payload: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {"id": self.id, "score": self.score, "payload": self.payload}


@dataclass
class SearchResponse:
    backend: str = ""
    hits: List[SearchResult] = field(default_factory=list)
    total_hits: int = 0
    query: str = ""
    latency_ms: float = 0.0
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "backend": self.backend, "hits": [h.to_dict() for h in self.hits[:20]],
            "total_hits": self.total_hits, "query": self.query,
            "latency_ms": self.latency_ms, "error": self.error,
            "metadata": self.metadata,
        }


# ── Meilisearch Backend ──────────────────────────────────────────

class MeilisearchBackend:
    """Meilisearch HTTP API client."""

    name = "meilisearch"

    def __init__(self, url: str = "http://localhost:7700", api_key: str = ""):
        self.url = url.rstrip("/")
        self.api_key = api_key
        self._available: Optional[bool] = None

    async def _request(self, method: str, path: str, **kwargs) -> Dict[str, Any]:
        if not HAS_HTTPX:
            return {"error": "httpx not installed"}
        headers = kwargs.pop("headers", {})
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.request(method, f"{self.url}{path}", headers=headers, **kwargs)
                return {"status": resp.status_code, "data": resp.json() if resp.status_code < 400 else None, "error": resp.text if resp.status_code >= 400 else None}
        except Exception as e:
            return {"error": str(e)[:200]}

    async def health(self) -> bool:
        res = await self._request("GET", "/health")
        self._available = res.get("data", {}).get("status") == "available" if not res.get("error") else False
        return self._available

    async def search(self, index_name: str, query: str, limit: int = 20, filter: str = "") -> SearchResponse:
        start = time.time()
        body: Dict[str, Any] = {"q": query, "limit": limit}
        if filter:
            body["filter"] = filter
        res = await self._request("POST", f"/indexes/{index_name}/search", json=body)
        latency_ms = round((time.time() - start) * 1000, 1)
        if res.get("error"):
            return SearchResponse(backend="meilisearch", query=query, latency_ms=latency_ms, error=res["error"])
        hits_data = res.get("data", {}).get("hits", [])
        hits = [SearchResult(id=str(h.get("id", "")), score=h.get("_rankingScore", 0), payload=h) for h in hits_data]
        return SearchResponse(backend="meilisearch", hits=hits, total_hits=len(hits), query=query, latency_ms=latency_ms)

    async def add_documents(self, index_name: str, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        return await self._request("POST", f"/indexes/{index_name}/documents", json=documents)

    async def create_index(self, index_name: str, primary_key: str = "id") -> Dict[str, Any]:
        return await self._request("POST", "/indexes", json={"uid": index_name, "primaryKey": primary_key})

    async def list_indexes(self) -> List[str]:
        res = await self._request("GET", "/indexes")
        if res.get("error"):
            return []
        return [idx.get("uid", "") for idx in res.get("data", {}).get("results", [])]


# ── OpenSearch Backend ───────────────────────────────────────────

class OpenSearchBackend:
    """OpenSearch HTTP API client."""

    name = "opensearch"

    def __init__(self, url: str = "http://localhost:9200", username: str = "", password: str = ""):
        self.url = url.rstrip("/")
        self.username = username
        self.password = password
        self._available: Optional[bool] = None

    async def _request(self, method: str, path: str, **kwargs) -> Dict[str, Any]:
        if not HAS_HTTPX:
            return {"error": "httpx not installed"}
        headers = kwargs.pop("headers", {})
        auth = (self.username, self.password) if self.username else None
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.request(method, f"{self.url}{path}", headers=headers, auth=auth, **kwargs)
                return {"status": resp.status_code, "data": resp.json() if resp.status_code < 400 else None, "error": resp.text if resp.status_code >= 400 else None}
        except Exception as e:
            return {"error": str(e)[:200]}

    async def health(self) -> bool:
        res = await self._request("GET", "/_cluster/health")
        self._available = not res.get("error")
        return self._available

    async def search(self, index_name: str, query: str, size: int = 20) -> SearchResponse:
        start = time.time()
        body = {"query": {"match": {"_all": query}}, "size": size}
        res = await self._request("POST", f"/{index_name}/_search", json=body)
        latency_ms = round((time.time() - start) * 1000, 1)
        if res.get("error"):
            return SearchResponse(backend="opensearch", query=query, latency_ms=latency_ms, error=res["error"])
        hits_data = res.get("data", {}).get("hits", {}).get("hits", [])
        total = res.get("data", {}).get("hits", {}).get("total", {}).get("value", 0)
        hits = [SearchResult(id=h.get("_id", ""), score=h.get("_score", 0), payload=h.get("_source", {})) for h in hits_data]
        return SearchResponse(backend="opensearch", hits=hits, total_hits=total, query=query, latency_ms=latency_ms)

    async def index_document(self, index_name: str, doc_id: str, document: Dict[str, Any]) -> Dict[str, Any]:
        return await self._request("PUT", f"/{index_name}/_doc/{doc_id}", json=document)

    async def create_index(self, index_name: str, mappings: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        body = {"mappings": mappings or {"properties": {"_all": {"type": "text"}}}}
        return await self._request("PUT", f"/{index_name}", json=body)

    async def list_indexes(self) -> List[str]:
        res = await self._request("GET", "/_cat/indices?format=json")
        if res.get("error"):
            return []
        return [idx.get("index", "") for idx in res.get("data", []) if not idx.get("index", "").startswith(".")]


# ── Vector Search Backend ────────────────────────────────────────

class VectorSearchBackend:
    """Vector similarity search using sentence-transformers (optional)."""

    name = "vector"

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self._model = None
        self._store: Dict[str, List[Tuple[str, List[float], Dict[str, Any]]]] = {}

    def _get_model(self):
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(self.model_name)
            except ImportError:
                return None
        return self._model

    def _embed(self, texts: List[str]) -> List[List[float]]:
        model = self._get_model()
        if model is None:
            return []
        return model.encode(texts).tolist()

    async def index_documents(self, collection: str, documents: List[Dict[str, Any]], text_field: str = "text") -> Dict[str, Any]:
        texts = [doc.get(text_field, "") for doc in documents]
        embeddings = self._embed(texts)
        if not embeddings:
            return {"error": "sentence-transformers not installed", "indexed": 0}
        if collection not in self._store:
            self._store[collection] = []
        for i, doc in enumerate(documents):
            doc_id = doc.get("id", hashlib.md5(texts[i].encode()).hexdigest()[:12])
            self._store[collection].append((doc_id, embeddings[i], doc))
        return {"indexed": len(documents), "collection": collection}

    async def search(self, collection: str, query: str, limit: int = 10) -> SearchResponse:
        start = time.time()
        query_embedding = self._embed([query])
        if not query_embedding:
            latency_ms = round((time.time() - start) * 1000, 1)
            return SearchResponse(backend="vector", query=query, latency_ms=latency_ms, error="sentence-transformers not installed")
        q_emb = query_embedding[0]
        docs = self._store.get(collection, [])
        scored = []
        for doc_id, emb, payload in docs:
            score = sum(a * b for a, b in zip(q_emb, emb)) / (
                (sum(a * a for a in q_emb) ** 0.5) * (sum(b * b for b in emb) ** 0.5) + 1e-10
            )
            scored.append((doc_id, score, payload))
        scored.sort(key=lambda x: -x[1])
        hits = [SearchResult(id=did, score=round(sc, 4), payload=pl) for did, sc, pl in scored[:limit]]
        latency_ms = round((time.time() - start) * 1000, 1)
        return SearchResponse(backend="vector", hits=hits, total_hits=len(hits), query=query, latency_ms=latency_ms)


# ── Search Backend Manager ───────────────────────────────────────

class SearchBackendManager:
    """Manages external search backends (Meilisearch, OpenSearch, Vector)."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._meilisearch = MeilisearchBackend(
            url=self.config.get("meilisearch_url", "http://localhost:7700"),
            api_key=self.config.get("meilisearch_api_key", ""),
        )
        self._opensearch = OpenSearchBackend(
            url=self.config.get("opensearch_url", "http://localhost:9200"),
            username=self.config.get("opensearch_username", ""),
            password=self.config.get("opensearch_password", ""),
        )
        self._vector = VectorSearchBackend(
            model_name=self.config.get("vector_model", SemanticSearchModel.ALL_MINILM.value),
        )
        self._history: List[SearchResponse] = []

    def get_profiles(self) -> List[Dict[str, Any]]:
        return [p.to_dict() for p in BACKEND_PROFILES]

    async def check_health(self) -> Dict[str, bool]:
        meili = await self._meilisearch.health()
        os_health = await self._opensearch.health()
        return {"meilisearch": meili, "opensearch": os_health, "vector": True}

    async def search(self, backend: ExternalSearchBackend, index_name: str, query: str, **kwargs) -> SearchResponse:
        if backend == ExternalSearchBackend.MEILISEARCH:
            result = await self._meilisearch.search(index_name, query, **kwargs)
        elif backend == ExternalSearchBackend.OPENSEARCH:
            result = await self._opensearch.search(index_name, query, **kwargs)
        elif backend == ExternalSearchBackend.VECTOR:
            result = await self._vector.search(index_name, query, **kwargs)
        else:
            result = SearchResponse(backend=backend.value, query=query, error=f"Unknown backend: {backend.value}")
        self._history.append(result)
        return result

    async def index_documents(self, backend: ExternalSearchBackend, collection: str, documents: List[Dict[str, Any]], **kwargs) -> Dict[str, Any]:
        if backend == ExternalSearchBackend.MEILISEARCH:
            return await self._meilisearch.add_documents(collection, documents)
        elif backend == ExternalSearchBackend.OPENSEARCH:
            results = []
            for doc in documents:
                doc_id = doc.get("id", hashlib.md5(str(doc).encode()).hexdigest()[:12])
                res = await self._opensearch.index_document(collection, doc_id, doc)
                results.append(res)
            return {"indexed": len(documents), "results": results}
        elif backend == ExternalSearchBackend.VECTOR:
            return await self._vector.index_documents(collection, documents, **kwargs)
        return {"error": f"Unknown backend: {backend.value}"}

    async def vector_search(self, collection: str, query: str, limit: int = 10, model: str = "") -> SearchResponse:
        if model and model != self._vector.model_name:
            self._vector = VectorSearchBackend(model_name=model)
        result = await self._vector.search(collection, query, limit)
        self._history.append(result)
        return result

    def get_stats(self) -> Dict[str, Any]:
        return {
            "total_searches": len(self._history),
            "backends_used": list(set(r.backend for r in self._history)),
            "profiles": len(BACKEND_PROFILES),
        }
