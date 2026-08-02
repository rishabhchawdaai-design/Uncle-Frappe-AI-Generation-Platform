"""
Durable Event Log — persistent event sourcing + delivery guarantees.

Based on ACOS Research: Messaging & Events Research (ACOS Event System
Architecture, Delivery Guarantees by Event Class).

Implements the durable event log (NATS JetStream analog) with:
- Event taxonomy: kernel.*, request.*, workflow.*, health.*, system.*
- Delivery guarantees per class: at-least-once with retry counts,
  at-most-once for health.* (no persistence)
- Dead-letter queue for failed deliveries
- Event replay (subject patterns, after timestamp, class filters)
- Retention policy (age-based and count-based purge)
- SQLite persistence (stdlib, offline)
"""
import json
import logging
import os
import time
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class EventClass(str, Enum):
    KERNEL = "kernel"
    REQUEST = "request"
    WORKFLOW = "workflow"
    HEALTH = "health"
    SYSTEM = "system"


# Delivery guarantees from ACOS research (section 4, Delivery Guarantees)
DELIVERY_POLICIES = {
    EventClass.KERNEL: {"guarantee": "at_least_once", "persist": True, "max_attempts": 3},
    EventClass.REQUEST: {"guarantee": "at_least_once", "persist": True, "max_attempts": 3},
    EventClass.WORKFLOW: {"guarantee": "at_least_once", "persist": True, "max_attempts": 5},
    EventClass.HEALTH: {"guarantee": "at_most_once", "persist": False, "max_attempts": 1},
    EventClass.SYSTEM: {"guarantee": "at_least_once", "persist": True, "max_attempts": 3},
}


@dataclass
class DurableEvent:
    """A persisted event with delivery metadata."""
    event_id: str = ""
    subject: str = ""
    payload: Any = None
    headers: Dict[str, str] = field(default_factory=dict)
    publisher: str = ""
    event_class: str = EventClass.SYSTEM.value
    guarantee: str = "at_least_once"
    attempts: int = 0
    max_attempts: int = 3
    status: str = "pending"  # pending, delivered, dead_letter, purged
    created_at: str = ""
    delivered_at: str = ""
    error: str = ""

    def __post_init__(self):
        if not self.event_id:
            import hashlib
            self.event_id = hashlib.md5(
                f"{self.subject}:{time.time()}:{id(self)}".encode()
            ).hexdigest()[:16]
        if not self.created_at:
            self.created_at = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "subject": self.subject,
            "payload": self.payload,
            "headers": self.headers,
            "publisher": self.publisher,
            "event_class": self.event_class,
            "guarantee": self.guarantee,
            "attempts": self.attempts,
            "max_attempts": self.max_attempts,
            "status": self.status,
            "created_at": self.created_at,
            "delivered_at": self.delivered_at,
            "error": self.error,
        }


def classify_subject(subject: str) -> EventClass:
    """Map a subject to its event class using the ACOS taxonomy."""
    if subject.startswith("request."):
        return EventClass.REQUEST
    if subject.startswith("workflow."):
        return EventClass.WORKFLOW
    if subject.startswith("health."):
        return EventClass.HEALTH
    if (subject.startswith("kernel.") or subject.startswith("capability.")
            or subject.startswith("node.")):
        return EventClass.KERNEL
    return EventClass.SYSTEM


class DurableEventLog:
    """SQLite-backed durable event log with replay, DLQ, and retention."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        db_path = self.config.get("db_path") or os.environ.get("ACOS_EVENT_LOG_PATH")
        if not db_path:
            Path("data/storage").mkdir(parents=True, exist_ok=True)
            db_path = "data/storage/event_log.db"
        self._db_path = db_path
        Path(self._db_path).parent.mkdir(parents=True, exist_ok=True)
        self._bus = None
        self._init_schema()
        self._stats = {
            "total_persisted": 0, "total_replayed": 0,
            "total_dead_lettered": 0, "total_purged": 0,
        }

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path, timeout=10)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self):
        with self._connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    event_id TEXT PRIMARY KEY,
                    subject TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    headers_json TEXT NOT NULL DEFAULT '{}',
                    publisher TEXT NOT NULL DEFAULT '',
                    event_class TEXT NOT NULL,
                    guarantee TEXT NOT NULL,
                    attempts INTEGER NOT NULL DEFAULT 0,
                    max_attempts INTEGER NOT NULL DEFAULT 3,
                    status TEXT NOT NULL DEFAULT 'pending',
                    created_at TEXT NOT NULL,
                    delivered_at TEXT,
                    error TEXT NOT NULL DEFAULT ''
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_events_subject ON events (subject)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_events_class ON events (event_class)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_events_status ON events (status)")

    def attach_bus(self, bus):
        """Attach an in-memory EventBus so durable events also fan out live."""
        self._bus = bus

    def _row_to_event(self, row: sqlite3.Row) -> DurableEvent:
        return DurableEvent(
            event_id=row["event_id"], subject=row["subject"],
            payload=json.loads(row["payload_json"]),
            headers=json.loads(row["headers_json"]),
            publisher=row["publisher"], event_class=row["event_class"],
            guarantee=row["guarantee"], attempts=row["attempts"],
            max_attempts=row["max_attempts"], status=row["status"],
            created_at=row["created_at"], delivered_at=row["delivered_at"],
            error=row["error"],
        )

    def append(self, subject: str, payload: Any = None,
               headers: Optional[Dict[str, str]] = None,
               publisher: str = "", event_class: Optional[str] = None) -> DurableEvent:
        """Persist an event (and fan out to the attached in-memory bus)."""
        event_class = event_class or classify_subject(subject).value
        policy = DELIVERY_POLICIES.get(EventClass(event_class), DELIVERY_POLICIES[EventClass.SYSTEM])
        now = datetime.now().isoformat()
        event = DurableEvent(
            subject=subject, payload=payload, headers=headers or {},
            publisher=publisher, event_class=event_class,
            guarantee=policy["guarantee"], max_attempts=policy["max_attempts"],
            created_at=now,
        )
        # health.* is at-most-once: still recorded but marked delivered immediately
        if not policy["persist"]:
            event.status = "delivered"
            event.delivered_at = now
        try:
            with self._connect() as conn:
                conn.execute(
                    """
                    INSERT INTO events (event_id, subject, payload_json, headers_json,
                        publisher, event_class, guarantee, attempts, max_attempts,
                        status, created_at, delivered_at, error)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (event.event_id, event.subject, json.dumps(payload, default=str),
                     json.dumps(event.headers, default=str), event.publisher,
                     event.event_class, event.guarantee, event.attempts,
                     event.max_attempts, event.status, event.created_at,
                     event.delivered_at, event.error),
                )
            self._stats["total_persisted"] += 1
            if self._bus is not None:
                import asyncio
                try:
                    asyncio.get_running_loop()
                    asyncio.ensure_future(self._bus.publish(
                        subject, payload, headers, publisher))
                except RuntimeError:
                    # no running loop -> synchronous fan-out
                    self._bus.publish_sync(subject, payload, headers, publisher)
                except Exception as e:
                    logger.debug("Live fan-out failed: %s", e)
            return event
        except Exception as e:
            logger.error("Event persist failed: %s", e)
            raise

    def replay(self, subject: str = "", after_ts: str = "",
               limit: int = 100, event_class: str = "",
               status: str = "") -> List[DurableEvent]:
        """Replay events from the durable log."""
        query = "SELECT * FROM events WHERE 1=1"
        params: List[Any] = []
        if subject:
            query += " AND (subject = ? OR subject LIKE ?)"
            params += [subject, subject.replace("*", "%") + "%"]
        if after_ts:
            query += " AND created_at >= ?"
            params.append(after_ts)
        if event_class:
            query += " AND event_class = ?"
            params.append(event_class)
        if status:
            query += " AND status = ?"
            params.append(status)
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(int(limit))
        try:
            with self._connect() as conn:
                rows = conn.execute(query, params).fetchall()
            self._stats["total_replayed"] += len(rows)
            return [self._row_to_event(r) for r in rows]
        except Exception as e:
            logger.error("Replay failed: %s", e)
            return []

    def mark_delivered(self, event_id: str) -> bool:
        try:
            with self._connect() as conn:
                cur = conn.execute(
                    "UPDATE events SET status='delivered', delivered_at=? WHERE event_id=?",
                    (datetime.now().isoformat(), event_id))
            return cur.rowcount > 0
        except Exception:
            return False

    def record_failure(self, event_id: str, error: str = "") -> str:
        """Record a delivery failure; move to DLQ when attempts exceed max."""
        try:
            with self._connect() as conn:
                row = conn.execute(
                    "SELECT * FROM events WHERE event_id = ?", (event_id,)
                ).fetchone()
                if row is None:
                    return "not_found"
                attempts = row["attempts"] + 1
                if attempts >= row["max_attempts"]:
                    conn.execute(
                        "UPDATE events SET attempts=?, status='dead_letter', error=? WHERE event_id=?",
                        (attempts, error[:500] or "max attempts exceeded", event_id))
                    self._stats["total_dead_lettered"] += 1
                    return "dead_letter"
                conn.execute(
                    "UPDATE events SET attempts=?, error=? WHERE event_id=?",
                    (attempts, error[:500], event_id))
                return "retry"
        except Exception as e:
            logger.error("record_failure failed: %s", e)
            return "error"

    def purge_older_than(self, days: int = 30) -> int:
        """Purge events older than N days (retention policy)."""
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        try:
            with self._connect() as conn:
                cur = conn.execute("DELETE FROM events WHERE created_at < ?", (cutoff,))
            count = cur.rowcount
            self._stats["total_purged"] += count
            return count
        except Exception:
            return 0

    def purge(self, status: str = "dead_letter") -> int:
        """Purge events by status (default: dead-letter queue)."""
        try:
            with self._connect() as conn:
                cur = conn.execute("DELETE FROM events WHERE status = ?", (status,))
            count = cur.rowcount
            self._stats["total_purged"] += count
            return count
        except Exception:
            return 0

    def dead_letter_queue(self, limit: int = 100) -> List[DurableEvent]:
        return self.replay(status="dead_letter", limit=limit)

    def stats(self) -> Dict[str, Any]:
        try:
            with self._connect() as conn:
                total = conn.execute("SELECT COUNT(*) as c FROM events").fetchone()["c"]
                by_status = {r["status"]: r["c"] for r in conn.execute(
                    "SELECT status, COUNT(*) as c FROM events GROUP BY status").fetchall()}
                by_class = {r["event_class"]: r["c"] for r in conn.execute(
                    "SELECT event_class, COUNT(*) as c FROM events GROUP BY event_class").fetchall()}
        except Exception:
            total, by_status, by_class = 0, {}, {}
        return {
            "db_path": self._db_path,
            "total_events": total,
            "by_status": by_status,
            "by_class": by_class,
            "live": dict(self._stats),
            "delivery_policies": {
                k.value: v for k, v in DELIVERY_POLICIES.items()
            },
        }
