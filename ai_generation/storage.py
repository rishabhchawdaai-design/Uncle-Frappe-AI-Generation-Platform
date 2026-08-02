"""
Storage & Databases — unified storage backend registry.

Based on ACOS Research: Storage & Databases Research.
Provides a single storage abstraction over local (SQLite, JSON files) and
external (PostgreSQL, Qdrant, LanceDB, MinIO, Neo4j, Prometheus, Redis)
backends. Local backends work offline with zero dependencies; external
backends are registered as profiles and report a clean, truthful
"not_configured" status until their connection details are provided.

Research mapping (ACOS Storage Architecture):
- SQLite/JSON -> Metadata, Decision Ledger, Audit Logs
- Qdrant      -> Embeddings, Semantic Search
- MinIO       -> Model Weights, Checkpoints, Outputs
- Neo4j       -> Capability Graph, Knowledge Graph
- Prometheus  -> Metrics, Time-Series Data
- Redis       -> Caching, Session State, Queues
"""
import json
import logging
import os
import sqlite3
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class StorageBackendType(str, Enum):
    SQLITE = "sqlite"
    JSON = "json"
    POSTGRESQL = "postgresql"
    QDRANT = "qdrant"
    LANCEDB = "lancedb"
    MINIO = "minio"
    NEO4J = "neo4j"
    PROMETHEUS = "prometheus"
    REDIS = "redis"


class StorageTask(str, Enum):
    METADATA = "metadata"
    LEDGER = "ledger"
    AUDIT = "audit"
    EMBEDDINGS = "embeddings"
    ARTIFACTS = "artifacts"
    GRAPH = "graph"
    METRICS = "metrics"
    CACHE = "cache"


@dataclass
class StorageRecord:
    """A single stored record."""
    collection: str = ""
    key: str = ""
    value: Any = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = ""
    updated_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "collection": self.collection,
            "key": self.key,
            "value": self.value,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class StorageBackendProfile:
    """Profile for a storage backend."""
    backend: StorageBackendType = StorageBackendType.JSON
    name: str = ""
    description: str = ""
    tasks: List[str] = field(default_factory=list)
    local: bool = True
    requires_connection: bool = False
    default_url: str = ""
    available: bool = True
    status: str = "available"  # available, not_configured, unreachable, error

    def to_dict(self) -> Dict[str, Any]:
        return {
            "backend": self.backend.value,
            "name": self.name,
            "description": self.description,
            "tasks": self.tasks,
            "local": self.local,
            "requires_connection": self.requires_connection,
            "default_url": self.default_url,
            "available": self.available,
            "status": self.status,
        }


class StorageBackend:
    """Base class for storage backends."""

    backend: StorageBackendType = StorageBackendType.JSON
    name: str = "base"
    description: str = ""
    local: bool = True
    requires_connection: bool = False
    tasks: List[str] = []

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._status = "available"
        self._error: Optional[str] = None
        self._last_checked: Optional[str] = None

    @property
    def is_available(self) -> bool:
        return self._status in ("available", "not_configured")

    def health_check(self) -> Dict[str, Any]:
        return {
            "backend": self.name,
            "status": self._status,
            "available": self.is_available,
            "error": self._error,
            "checked_at": self._last_checked,
        }

    def _mark(self, status: str, error: str = ""):
        self._status = status
        self._error = error or None
        self._last_checked = datetime.now().isoformat()

    def write(self, collection: str, key: str, value: Any, **kwargs) -> StorageRecord:
        raise NotImplementedError

    def read(self, collection: str, key: str) -> Optional[StorageRecord]:
        raise NotImplementedError

    def query(self, collection: str, limit: int = 100, **kwargs) -> List[StorageRecord]:
        raise NotImplementedError

    def delete(self, collection: str, key: str) -> bool:
        raise NotImplementedError

    def stats(self) -> Dict[str, Any]:
        return {"backend": self.name, "collections": 0, "records": 0}

    def to_profile(self) -> StorageBackendProfile:
        return StorageBackendProfile(
            backend=self.backend, name=self.name, description=self.description,
            tasks=list(self.tasks), local=self.local,
            requires_connection=self.requires_connection,
            available=self.is_available, status=self._status,
        )


class SQLiteStorageBackend(StorageBackend):
    """Local SQLite storage — metadata, ledger, audit, cache (stdlib)."""

    backend = StorageBackendType.SQLITE
    name = "sqlite_local"
    description = "Local SQLite database (stdlib sqlite3) for metadata, ledger, audit, cache"
    local = True
    requires_connection = False
    tasks = [StorageTask.METADATA.value, StorageTask.LEDGER.value,
             StorageTask.AUDIT.value, StorageTask.CACHE.value]

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        db_path = config.get("db_path") if config else None
        self._db_path = db_path or os.environ.get("ACOS_DB_PATH") or "data/storage/acos.db"
        Path(self._db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path, timeout=10)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self):
        try:
            with self._connect() as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS storage_items (
                        collection TEXT NOT NULL,
                        key TEXT NOT NULL,
                        value_json TEXT NOT NULL,
                        metadata_json TEXT NOT NULL DEFAULT '{}',
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        PRIMARY KEY (collection, key)
                    )
                """)
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_storage_collection "
                    "ON storage_items (collection)")
            self._mark("available")
        except Exception as e:
            self._mark("error", str(e)[:200])
            logger.warning("SQLite storage init failed: %s", e)

    def write(self, collection: str, key: str, value: Any, **kwargs) -> StorageRecord:
        now = datetime.now().isoformat()
        metadata = kwargs.get("metadata", {})
        try:
            with self._connect() as conn:
                conn.execute(
                    """
                    INSERT INTO storage_items
                        (collection, key, value_json, metadata_json, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(collection, key) DO UPDATE SET
                        value_json = excluded.value_json,
                        metadata_json = excluded.metadata_json,
                        updated_at = excluded.updated_at
                    """,
                    (collection, key, json.dumps(value, default=str),
                     json.dumps(metadata, default=str), now, now),
                )
            self._mark("available")
            return StorageRecord(collection=collection, key=key, value=value,
                                 metadata=metadata, created_at=now, updated_at=now)
        except Exception as e:
            self._mark("error", str(e)[:200])
            raise

    def read(self, collection: str, key: str) -> Optional[StorageRecord]:
        try:
            with self._connect() as conn:
                row = conn.execute(
                    "SELECT * FROM storage_items WHERE collection = ? AND key = ?",
                    (collection, key),
                ).fetchone()
            self._mark("available")
            if row is None:
                return None
            return StorageRecord(
                collection=row["collection"], key=row["key"],
                value=json.loads(row["value_json"]),
                metadata=json.loads(row["metadata_json"]),
                created_at=row["created_at"], updated_at=row["updated_at"],
            )
        except Exception as e:
            self._mark("error", str(e)[:200])
            return None

    def query(self, collection: str, limit: int = 100, **kwargs) -> List[StorageRecord]:
        try:
            with self._connect() as conn:
                rows = conn.execute(
                    "SELECT * FROM storage_items WHERE collection = ? ORDER BY updated_at DESC LIMIT ?",
                    (collection, int(limit)),
                ).fetchall()
            self._mark("available")
            return [
                StorageRecord(
                    collection=r["collection"], key=r["key"],
                    value=json.loads(r["value_json"]),
                    metadata=json.loads(r["metadata_json"]),
                    created_at=r["created_at"], updated_at=r["updated_at"],
                )
                for r in rows
            ]
        except Exception as e:
            self._mark("error", str(e)[:200])
            return []

    def delete(self, collection: str, key: str) -> bool:
        try:
            with self._connect() as conn:
                cur = conn.execute(
                    "DELETE FROM storage_items WHERE collection = ? AND key = ?",
                    (collection, key),
                )
            self._mark("available")
            return cur.rowcount > 0
        except Exception as e:
            self._mark("error", str(e)[:200])
            return False

    def stats(self) -> Dict[str, Any]:
        try:
            with self._connect() as conn:
                collections = conn.execute(
                    "SELECT collection, COUNT(*) as c FROM storage_items GROUP BY collection"
                ).fetchall()
                total = conn.execute("SELECT COUNT(*) as c FROM storage_items").fetchone()["c"]
            self._mark("available")
            return {
                "backend": self.name,
                "db_path": self._db_path,
                "collections": {r["collection"]: r["c"] for r in collections},
                "records": total,
            }
        except Exception as e:
            self._mark("error", str(e)[:200])
            return {"backend": self.name, "error": str(e)[:200]}

    def health_check(self) -> Dict[str, Any]:
        try:
            with self._connect() as conn:
                conn.execute("PRAGMA integrity_check").fetchone()
            self._mark("available")
        except Exception as e:
            self._mark("error", str(e)[:200])
        return super().health_check()


class JSONStorageBackend(StorageBackend):
    """Local JSON file storage — mirrors the existing data/ registry pattern."""

    backend = StorageBackendType.JSON
    name = "json_files"
    description = "Local JSON file storage (stdlib) for registries and small datasets"
    local = True
    requires_connection = False
    tasks = [StorageTask.METADATA.value, StorageTask.LEDGER.value,
             StorageTask.GRAPH.value]

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self._root = config.get("root") if config else None
        self._root = self._root or os.environ.get("ACOS_DATA_ROOT") or "data/storage/json"
        Path(self._root).mkdir(parents=True, exist_ok=True)
        self._mark("available")

    def _path(self, collection: str) -> Path:
        # safe collection name -> file path
        safe = "".join(c for c in collection if c.isalnum() or c in "-_.")
        return Path(self._root) / f"{safe}.json"

    def _load(self, collection: str) -> Dict[str, Dict[str, Any]]:
        path = self._path(collection)
        if not path.exists():
            return {}
        try:
            return json.loads(path.read_text())
        except Exception:
            return {}

    def _save(self, collection: str, data: Dict[str, Dict[str, Any]]):
        path = self._path(collection)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2, default=str))

    def write(self, collection: str, key: str, value: Any, **kwargs) -> StorageRecord:
        now = datetime.now().isoformat()
        metadata = kwargs.get("metadata", {})
        data = self._load(collection)
        record = {"value": value, "metadata": metadata,
                  "created_at": now, "updated_at": now}
        if key in data:
            record["created_at"] = data[key].get("created_at", now)
        data[key] = record
        self._save(collection, data)
        self._mark("available")
        return StorageRecord(collection=collection, key=key, value=value,
                             metadata=metadata, created_at=record["created_at"],
                             updated_at=now)

    def read(self, collection: str, key: str) -> Optional[StorageRecord]:
        data = self._load(collection)
        record = data.get(key)
        self._mark("available")
        if record is None:
            return None
        return StorageRecord(collection=collection, key=key,
                             value=record.get("value"),
                             metadata=record.get("metadata", {}),
                             created_at=record.get("created_at", ""),
                             updated_at=record.get("updated_at", ""))

    def query(self, collection: str, limit: int = 100, **kwargs) -> List[StorageRecord]:
        data = self._load(collection)
        self._mark("available")
        items = [
            StorageRecord(collection=collection, key=k,
                          value=v.get("value"), metadata=v.get("metadata", {}),
                          created_at=v.get("created_at", ""),
                          updated_at=v.get("updated_at", ""))
            for k, v in data.items()
        ]
        items.sort(key=lambda r: r.updated_at, reverse=True)
        return items[:int(limit)]

    def delete(self, collection: str, key: str) -> bool:
        data = self._load(collection)
        if key not in data:
            return False
        del data[key]
        self._save(collection, data)
        self._mark("available")
        return True

    def stats(self) -> Dict[str, Any]:
        root = Path(self._root)
        collections = {}
        total = 0
        for path in root.glob("*.json"):
            try:
                data = json.loads(path.read_text())
                collections[path.stem] = len(data)
                total += len(data)
            except Exception:
                continue
        return {"backend": self.name, "root": self._root,
                "collections": collections, "records": total}


EXTERNAL_BACKEND_PROFILES = [
    StorageBackendProfile(
        backend=StorageBackendType.POSTGRESQL, name="postgresql",
        description="PostgreSQL — metadata, decision ledger, audit logs",
        tasks=[StorageTask.METADATA.value, StorageTask.LEDGER.value,
               StorageTask.AUDIT.value],
        local=False, requires_connection=True, default_url="postgresql://localhost:5432",
        available=False, status="not_configured"),
    StorageBackendProfile(
        backend=StorageBackendType.QDRANT, name="qdrant",
        description="Qdrant — embeddings, semantic search",
        tasks=[StorageTask.EMBEDDINGS.value],
        local=False, requires_connection=True, default_url="http://localhost:6333",
        available=False, status="not_configured"),
    StorageBackendProfile(
        backend=StorageBackendType.LANCEDB, name="lancedb",
        description="LanceDB — embeddings, vector store (embeddable)",
        tasks=[StorageTask.EMBEDDINGS.value],
        local=True, requires_connection=False, default_url="",
        available=False, status="not_configured"),
    StorageBackendProfile(
        backend=StorageBackendType.MINIO, name="minio",
        description="MinIO — model weights, checkpoints, outputs (S3-compatible)",
        tasks=[StorageTask.ARTIFACTS.value],
        local=False, requires_connection=True, default_url="http://localhost:9000",
        available=False, status="not_configured"),
    StorageBackendProfile(
        backend=StorageBackendType.NEO4J, name="neo4j",
        description="Neo4j — capability graph, knowledge graph",
        tasks=[StorageTask.GRAPH.value],
        local=False, requires_connection=True, default_url="bolt://localhost:7687",
        available=False, status="not_configured"),
    StorageBackendProfile(
        backend=StorageBackendType.PROMETHEUS, name="prometheus",
        description="Prometheus — metrics, time-series data",
        tasks=[StorageTask.METRICS.value],
        local=False, requires_connection=True, default_url="http://localhost:9090",
        available=False, status="not_configured"),
    StorageBackendProfile(
        backend=StorageBackendType.REDIS, name="redis",
        description="Redis — caching, session state, queues",
        tasks=[StorageTask.CACHE.value],
        local=False, requires_connection=True, default_url="redis://localhost:6379",
        available=False, status="not_configured"),
]


class StorageRegistry:
    """Registry of storage backends and profiles with task-based selection."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self._backends: Dict[str, StorageBackend] = {}
        self._profiles: Dict[str, StorageBackendProfile] = {}
        self._auto_loaded = False
        self._auto_load(config or {})

    def _auto_load(self, config: Dict[str, Any]):
        nested = config.get("storage") or {}
        sqlite_cfg = config.get("sqlite") or nested.get("sqlite") or {}
        json_cfg = config.get("json") or nested.get("json") or {}
        self.register_backend(SQLiteStorageBackend(sqlite_cfg))
        self.register_backend(JSONStorageBackend(json_cfg))
        for profile in EXTERNAL_BACKEND_PROFILES:
            self._profiles[profile.name] = profile
        self._auto_loaded = True

    def register_backend(self, backend: StorageBackend):
        self._backends[backend.name] = backend
        self._profiles[backend.name] = backend.to_profile()

    def list_backends(self) -> List[Dict[str, Any]]:
        out = [p.to_dict() for p in self._profiles.values()]
        # merge live availability from instantiated backends
        live = {b.name: b.to_profile().to_dict() for b in self._backends.values()}
        for item in out:
            if item["name"] in live:
                item.update({k: v for k, v in live[item["name"]].items()
                             if k in ("available", "status")})
        return out

    def get_backend(self, name: str) -> Optional[StorageBackend]:
        return self._backends.get(name)

    def select_backend(self, task: str) -> Optional[StorageBackend]:
        """Select the best available backend for a storage task.

        Local backends are preferred; SQLite is the default for most tasks.
        """
        if task == StorageTask.EMBEDDINGS.value:
            # LanceDB is the researched embeddings backend but is not
            # installed by default; SQLite/JSON can hold vectors too.
            return self._backends.get("sqlite_local")
        if task == StorageTask.ARTIFACTS.value:
            return self._backends.get("sqlite_local")
        for backend in self._backends.values():
            if task in backend.tasks:
                return backend
        return self._backends.get("sqlite_local")

    def write(self, collection: str, key: str, value: Any,
              task: str = StorageTask.METADATA.value, **kwargs) -> StorageRecord:
        backend = self.select_backend(task)
        return backend.write(collection, key, value, **kwargs)

    def read(self, collection: str, key: str, task: str = StorageTask.METADATA.value):
        backend = self.select_backend(task)
        return backend.read(collection, key)

    def query(self, collection: str, limit: int = 100,
              task: str = StorageTask.METADATA.value) -> List[StorageRecord]:
        backend = self.select_backend(task)
        return backend.query(collection, limit=limit)

    def delete(self, collection: str, key: str,
               task: str = StorageTask.METADATA.value) -> bool:
        backend = self.select_backend(task)
        return backend.delete(collection, key)

    def get_stats(self) -> Dict[str, Any]:
        live = {name: b.stats() for name, b in self._backends.items()}
        return {
            "backends_total": len(self._profiles),
            "backends_local": sum(1 for p in self._profiles.values() if p.local),
            "backends_configured": sum(1 for b in self._backends.values() if b.is_available),
            "profiles": [p.to_dict() for p in self._profiles.values()],
            "live": live,
        }

    def to_negotiation_candidates(self) -> List[Dict[str, Any]]:
        """Generate negotiation engine candidates for storage backends."""
        candidates = []
        for backend in self._backends.values():
            candidates.append({
                "provider": f"storage_{backend.name}",
                "model": backend.name,
                "layer": "storage",
                "tier": 3,
                "cost_usd": 0.0,
                "latency_estimate_ms": 5,
                "quality_estimate": 0.9,
                "requires_network": not backend.local,
                "metadata": {
                    "tasks": backend.tasks,
                    "local": backend.local,
                },
            })
        return candidates
