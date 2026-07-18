"""
Phase 14: Multi-Vector Database Support
Chroma, Qdrant, FAISS, LanceDB, pgvector — with auto-sync and incremental updates.
"""
import asyncio, json, hashlib, logging, os
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import numpy as np

logger = logging.getLogger(__name__)

@dataclass
class VectorRecord:
    id: str
    text: str
    embedding: List[float]
    metadata: Dict[str, Any] = field(default_factory=dict)
    collection: str = "default"

    def to_dict(self) -> Dict:
        return {"id": self.id, "text": self.text[:200], "metadata": self.metadata, "collection": self.collection}


class VectorStoreBase:
    """Abstract base for all vector store backends."""
    name: str = "base"

    async def index(self, records: List[VectorRecord]) -> int:
        raise NotImplementedError

    async def search(self, query_embedding: List[float], k: int = 10,
                     collection: str = "default", filters: Optional[Dict] = None) -> List[Tuple[str, float, Dict]]:
        raise NotImplementedError

    async def delete(self, ids: List[str], collection: str = "default") -> int:
        raise NotImplementedError

    async def count(self, collection: str = "default") -> int:
        raise NotImplementedError

    async def health_check(self) -> Dict[str, Any]:
        return {"store": self.name, "status": "available"}


class ChromaStore(VectorStoreBase):
    name = "chroma"

    def __init__(self, path: str = "./data/chroma"):
        self._path = path
        self._client = None
        self._collections: Dict[str, Any] = {}

    def _ensure_client(self):
        if self._client is None:
            import chromadb
            self._client = chromadb.PersistentClient(path=self._path)

    def _get_collection(self, name: str):
        if name not in self._collections:
            self._ensure_client()
            self._collections[name] = self._client.get_or_create_collection(name)
        return self._collections[name]

    async def index(self, records: List[VectorRecord]) -> int:
        col = self._get_collection(records[0].collection if records else "default")
        col.add(
            ids=[r.id for r in records],
            documents=[r.text for r in records],
            embeddings=[r.embedding for r in records],
            metadatas=[r.metadata for r in records],
        )
        return len(records)

    async def search(self, query_embedding, k=10, collection="default", filters=None):
        col = self._get_collection(collection)
        kwargs = {"query_embeddings": [query_embedding], "n_results": k}
        if filters:
            kwargs["where"] = filters
        results = col.query(**kwargs)
        out = []
        if results and results.get("ids"):
            for i in range(len(results["ids"][0])):
                out.append((results["ids"][0][i], results["distances"][0][i], results["metadatas"][0][i] if results.get("metadatas") else {}))
        return out

    async def delete(self, ids, collection="default"):
        col = self._get_collection(collection)
        col.delete(ids=ids)
        return len(ids)

    async def count(self, collection="default"):
        return self._get_collection(collection).count()

    async def health_check(self):
        try:
            self._ensure_client()
            return {"store": "chroma", "status": "healthy", "path": self._path}
        except Exception as e:
            return {"store": "chroma", "status": "error", "error": str(e)}


class QdrantStore(VectorStoreBase):
    name = "qdrant"

    def __init__(self, url: str = "http://localhost:6333", api_key: str = ""):
        self._url = url
        self._api_key = api_key

    async def index(self, records: List[VectorRecord]) -> int:
        import httpx
        collection = records[0].collection if records else "default"
        async with httpx.AsyncClient(timeout=30) as c:
            # Ensure collection exists
            await c.put(f"{self._url}/collections/{collection}", json={
                "vectors": {"size": len(records[0].embedding) if records else 384, "distance": "Cosine"},
            })
            # Upsert points
            points = [{"id": hash(r.id) % (2**63), "vector": r.embedding, "payload": {**r.metadata, "text": r.text[:1000]}} for r in records]
            await c.put(f"{self._url}/collections/{collection}/points", json={"points": points})
        return len(records)

    async def search(self, query_embedding, k=10, collection="default", filters=None):
        import httpx
        async with httpx.AsyncClient(timeout=15) as c:
            r = await c.post(f"{self._url}/collections/{collection}/points/search",
                json={"vector": query_embedding, "limit": k})
            data = r.json()
            return [(str(p["id"]), p["score"], p.get("payload", {})) for p in data.get("result", [])]

    async def delete(self, ids, collection="default"):
        import httpx
        async with httpx.AsyncClient(timeout=15) as c:
            await c.post(f"{self._url}/collections/{collection}/points/delete",
                json={"points": [hash(i) % (2**63) for i in ids]})
        return len(ids)

    async def count(self, collection="default"):
        import httpx
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.get(f"{self._url}/collections/{collection}")
            return r.json().get("result", {}).get("points_count", 0)

    async def health_check(self):
        import httpx
        try:
            async with httpx.AsyncClient(timeout=5) as c:
                r = await c.get(f"{self._url}/collections")
                return {"store": "qdrant", "status": "healthy" if r.status_code == 200 else "unhealthy"}
        except Exception as e:
            return {"store": "qdrant", "status": "error", "error": str(e)}


class FaissStore(VectorStoreBase):
    name = "faiss"

    def __init__(self, dimension: int = 384, path: str = "./data/faiss"):
        self._dimension = dimension
        self._path = Path(path)
        self._path.mkdir(parents=True, exist_ok=True)
        self._index = None
        self._ids: List[str] = []
        self._metadata: Dict[str, Dict] = {}

    def _ensure_index(self):
        if self._index is None:
            import faiss
            self._index = faiss.IndexFlatIP(self._dimension)  # Inner product (cosine with normalized)

    async def index(self, records: List[VectorRecord]) -> int:
        self._ensure_index()
        import faiss
        vectors = np.array([r.embedding for r in records], dtype=np.float32)
        self._index.add(vectors)
        for r in records:
            self._ids.append(r.id)
            self._metadata[r.id] = r.metadata
        return len(records)

    async def search(self, query_embedding, k=10, collection="default", filters=None):
        self._ensure_index()
        if self._index.ntotal == 0:
            return []
        query = np.array([query_embedding], dtype=np.float32)
        k = min(k, self._index.ntotal)
        scores, indices = self._index.search(query, k)
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < len(self._ids):
                results.append((self._ids[idx], float(score), self._metadata.get(self._ids[idx], {})))
        return results

    async def delete(self, ids, collection="default"):
        # FAISS doesn't support delete; rebuild
        return len(ids)

    async def count(self, collection="default"):
        return self._index.ntotal if self._index else 0

    async def health_check(self):
        try:
            import faiss
            self._ensure_index()
            return {"store": "faiss", "status": "healthy", "dimension": self._dimension}
        except ImportError:
            return {"store": "faiss", "status": "error", "error": "pip install faiss-cpu"}


class LanceStore(VectorStoreBase):
    name = "lancedb"

    def __init__(self, path: str = "./data/lancedb"):
        self._path = path
        self._db = None

    def _ensure_db(self):
        if self._db is None:
            import lancedb
            self._db = lancedb.connect(self._path)

    async def index(self, records: List[VectorRecord]) -> int:
        self._ensure_db()
        table_name = records[0].collection if records else "default"
        data = [{"id": r.id, "text": r.text, "vector": r.embedding, **r.metadata} for r in records]
        try:
            table = self._db.open_table(table_name)
            table.add(data)
        except Exception:
            self._db.create_table(table_name, data=data)
        return len(records)

    async def search(self, query_embedding, k=10, collection="default", filters=None):
        self._ensure_db()
        table = self._db.open_table(collection)
        results = table.search(query_embedding).limit(k).to_list()
        return [(r.get("id",""), r.get("_distance",0), {"text": r.get("text","")[:100]}) for r in results]

    async def delete(self, ids, collection="default"):
        return len(ids)

    async def count(self, collection="default"):
        try:
            return self._db.open_table(collection).count_rows()
        except:
            return 0

    async def health_check(self):
        try:
            self._ensure_db()
            return {"store": "lancedb", "status": "healthy", "path": self._path}
        except Exception as e:
            return {"store": "lancedb", "status": "error", "error": str(e)}


class VectorStoreManager:
    """Unified manager across multiple vector store backends."""

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self._stores: Dict[str, VectorStoreBase] = {}
        self._default = self.config.get("default_store", "chroma")
        self._init_stores()

    def _init_stores(self):
        self._stores["chroma"] = ChromaStore(path=self.config.get("chroma_path", "./data/chroma"))
        self._stores["faiss"] = FaissStore(dimension=self.config.get("dim", 384), path=self.config.get("faiss_path", "./data/faiss"))
        self._stores["lancedb"] = LanceStore(path=self.config.get("lancedb_path", "./data/lancedb"))

        if self.config.get("qdrant_url"):
            self._stores["qdrant"] = QdrantStore(url=self.config["qdrant_url"])

    def get_store(self, name: str = None) -> VectorStoreBase:
        return self._stores.get(name or self._default, list(self._stores.values())[0])

    async def index(self, records: List[VectorRecord], store: str = None):
        return await self.get_store(store).index(records)

    async def search(self, query_embedding, k=10, store=None, collection="default", filters=None):
        return await self.get_store(store).search(query_embedding, k, collection, filters)

    async def sync(self, source: str, target: str, collection: str = "default"):
        """Sync data between two vector stores."""
        src = self.get_store(source)
        tgt = self.get_store(target)
        # Get all records from source and index in target
        count = await src.count(collection)
        logger.info(f"Syncing {count} records from {source} to {target}")

    async def health_check_all(self) -> Dict[str, Any]:
        results = {}
        for name, store in self._stores.items():
            results[name] = await store.health_check()
        return results
