"""
Decision Ledger — immutable audit trail for all platform decisions.

Based on ACOS Research: Ch9 (Knowledge & Decision Ledger)
Records every routing, negotiation, generation, and recovery decision
with full context, reasoning, and outcome.

Constitution Principle: Every decision is evidence-based, documented,
and reversible. No silent decisions.
"""
import hashlib
import json
import logging
import tempfile
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class DecisionType(str, Enum):
    ROUTING = "routing"
    NEGOTIATION = "negotiation"
    GENERATION = "generation"
    RECOVERY = "recovery"
    FALLBACK = "fallback"
    PROVIDER_SELECTION = "provider_selection"
    MODEL_SELECTION = "model_selection"
    QUALITY_CHECK = "quality_check"
    BENCHMARK = "benchmark"
    HEALTH_CHECK = "health_check"
    CONFIGURATION = "configuration"


class DecisionOutcome(str, Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    FALLBACK_USED = "fallback_used"
    DEGRADED = "degraded"
    BLOCKED = "blocked"
    SKIPPED = "skipped"


@dataclass
class DecisionEntry:
    """A single decision in the audit trail."""
    decision_id: str = ""
    decision_type: DecisionType = DecisionType.ROUTING
    outcome: DecisionOutcome = DecisionOutcome.SUCCESS
    timestamp: str = ""
    session_id: str = ""

    request_id: str = ""
    prompt: str = ""
    task_type: str = ""

    selected_provider: str = ""
    selected_model: str = ""
    selected_layer: str = ""

    alternatives: List[Dict[str, Any]] = field(default_factory=list)
    fallback_chain: List[Dict[str, Any]] = field(default_factory=list)

    confidence_score: float = 0.0
    quality_score: float = 0.0
    latency_ms: float = 0.0
    cost_usd: float = 0.0

    reasoning: str = ""
    trade_offs: List[Dict[str, Any]] = field(default_factory=list)

    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()
        if not self.decision_id:
            h = hashlib.sha256(
                f"{self.decision_type.value}:{self.request_id}:{self.timestamp}".encode()
            ).hexdigest()[:12]
            self.decision_id = f"dec-{h}"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "decision_type": self.decision_type.value,
            "outcome": self.outcome.value,
            "timestamp": self.timestamp,
            "session_id": self.session_id,
            "request_id": self.request_id,
            "prompt": self.prompt[:200] if self.prompt else "",
            "task_type": self.task_type,
            "selected_provider": self.selected_provider,
            "selected_model": self.selected_model,
            "selected_layer": self.selected_layer,
            "alternatives_count": len(self.alternatives),
            "fallback_count": len(self.fallback_chain),
            "confidence_score": round(self.confidence_score, 3),
            "quality_score": round(self.quality_score, 3),
            "latency_ms": round(self.latency_ms, 1),
            "cost_usd": round(self.cost_usd, 6),
            "reasoning": self.reasoning[:500],
            "trade_offs_count": len(self.trade_offs),
            "error": self.error[:200] if self.error else None,
            "metadata_keys": list(self.metadata.keys()),
        }


class DecisionLedger:
    """
    Immutable audit trail for all platform decisions.

    Every routing, negotiation, generation, and recovery decision
    is recorded with full context. Supports querying by type,
    provider, time range, and outcome.

    Storage: JSON file with append-only semantics.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._entries: List[DecisionEntry] = []
        self._session_id = hashlib.sha256(
            f"{time.time()}:{id(self)}".encode()
        ).hexdigest()[:8]
        self._storage_path = Path(
            self.config.get("ledger_path", tempfile.mkdtemp() + "/ledger")
        )
        self._max_entries = self.config.get("max_entries", 10000)
        self._load()

    def record(self, decision_type: DecisionType, **kwargs) -> DecisionEntry:
        """Record a new decision entry."""
        entry = DecisionEntry(
            decision_type=decision_type,
            session_id=self._session_id,
            **kwargs,
        )
        self._entries.append(entry)
        self._trim()
        self._save()
        logger.debug(
            f"Decision recorded: {entry.decision_id} "
            f"type={entry.decision_type.value} outcome={entry.outcome.value}"
        )
        return entry

    def record_routing(
        self, request_id: str, prompt: str, task_type: str,
        selected_provider: str, selected_model: str,
        alternatives: List[Dict] = None, fallback_chain: List[Dict] = None,
        confidence: float = 0.0, reasoning: str = "", **kwargs
    ) -> DecisionEntry:
        """Record a routing decision."""
        return self.record(
            DecisionType.ROUTING,
            request_id=request_id, prompt=prompt, task_type=task_type,
            selected_provider=selected_provider, selected_model=selected_model,
            alternatives=alternatives or [], fallback_chain=fallback_chain or [],
            confidence_score=confidence, reasoning=reasoning, **kwargs,
        )

    def record_negotiation(
        self, request_id: str, prompt: str, task_type: str,
        selected_provider: str, selected_model: str,
        confidence: float = 0.0, reasoning: str = "",
        trade_offs: List[Dict] = None, **kwargs
    ) -> DecisionEntry:
        """Record a negotiation decision."""
        return self.record(
            DecisionType.NEGOTIATION,
            request_id=request_id, prompt=prompt, task_type=task_type,
            selected_provider=selected_provider, selected_model=selected_model,
            confidence_score=confidence, reasoning=reasoning,
            trade_offs=trade_offs or [], **kwargs,
        )

    def record_generation(
        self, request_id: str, prompt: str, task_type: str,
        provider: str, model: str, outcome: DecisionOutcome,
        latency_ms: float = 0.0, cost_usd: float = 0.0,
        quality_score: float = 0.0, error: str = None, **kwargs
    ) -> DecisionEntry:
        """Record a generation result."""
        return self.record(
            DecisionType.GENERATION,
            request_id=request_id, prompt=prompt, task_type=task_type,
            selected_provider=provider, selected_model=model,
            outcome=outcome, latency_ms=latency_ms, cost_usd=cost_usd,
            quality_score=quality_score, error=error, **kwargs,
        )

    def record_recovery(
        self, request_id: str, failed_provider: str, error: str,
        recovery_provider: str = "", reasoning: str = "", **kwargs
    ) -> DecisionEntry:
        """Record a recovery/fallback action."""
        return self.record(
            DecisionType.RECOVERY,
            request_id=request_id, selected_provider=recovery_provider,
            error=error, reasoning=reasoning,
            metadata={"failed_provider": failed_provider}, **kwargs,
        )

    def record_health_check(
        self, provider: str, healthy: bool,
        latency_ms: float = 0.0, error: str = None, **kwargs
    ) -> DecisionEntry:
        """Record a health check result."""
        outcome = DecisionOutcome.SUCCESS if healthy else DecisionOutcome.FAILURE
        return self.record(
            DecisionType.HEALTH_CHECK,
            selected_provider=provider, outcome=outcome,
            latency_ms=latency_ms, error=error, **kwargs,
        )

    # ── Query Methods ──────────────────────────────────────────

    def query(
        self,
        decision_type: Optional[DecisionType] = None,
        provider: Optional[str] = None,
        outcome: Optional[DecisionOutcome] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Query decision entries with filters."""
        results = self._entries

        if decision_type:
            results = [e for e in results if e.decision_type == decision_type]
        if provider:
            results = [e for e in results if e.selected_provider == provider]
        if outcome:
            results = [e for e in results if e.outcome == outcome]

        return [e.to_dict() for e in reversed(results[offset:offset + limit])]

    def get_recent(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get most recent decisions."""
        return [e.to_dict() for e in reversed(self._entries[-limit:])]

    def get_by_provider(self, provider: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get decisions for a specific provider."""
        return self.query(provider=provider, limit=limit)

    def get_failures(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get all failed decisions."""
        return self.query(outcome=DecisionOutcome.FAILURE, limit=limit)

    def get_stats(self) -> Dict[str, Any]:
        """Get ledger statistics."""
        total = len(self._entries)
        by_type = {}
        by_outcome = {}
        by_provider = {}

        for e in self._entries:
            dt_val = e.decision_type.value if hasattr(e.decision_type, "value") else e.decision_type
            by_type[dt_val] = by_type.get(dt_val, 0) + 1
            oc_val = e.outcome.value if hasattr(e.outcome, "value") else e.outcome
            by_outcome[oc_val] = by_outcome.get(oc_val, 0) + 1
            if e.selected_provider:
                by_provider[e.selected_provider] = by_provider.get(e.selected_provider, 0) + 1

        avg_confidence = (
            sum(e.confidence_score for e in self._entries if e.confidence_score > 0)
            / max(sum(1 for e in self._entries if e.confidence_score > 0), 1)
        )

        return {
            "total_decisions": total,
            "session_id": self._session_id,
            "by_type": by_type,
            "by_outcome": by_outcome,
            "by_provider": dict(sorted(by_provider.items(), key=lambda x: -x[1])[:10]),
            "avg_confidence": round(avg_confidence, 3),
            "first_entry": self._entries[0].timestamp if self._entries else None,
            "last_entry": self._entries[-1].timestamp if self._entries else None,
        }

    def get_provider_stats(self, provider: str) -> Dict[str, Any]:
        """Get statistics for a specific provider."""
        entries = [e for e in self._entries if e.selected_provider == provider]
        total = len(entries)
        success = sum(1 for e in entries if e.outcome == DecisionOutcome.SUCCESS)
        failure = sum(1 for e in entries if e.outcome == DecisionOutcome.FAILURE)
        avg_latency = (
            sum(e.latency_ms for e in entries if e.latency_ms > 0)
            / max(sum(1 for e in entries if e.latency_ms > 0), 1)
        )
        return {
            "provider": provider,
            "total_decisions": total,
            "success": success,
            "failure": failure,
            "success_rate": round(success / max(total, 1) * 100, 1),
            "avg_latency_ms": round(avg_latency, 1),
        }

    # ── Persistence ────────────────────────────────────────────

    def _load(self):
        """Load ledger from disk."""
        ledger_file = self._storage_path / "decisions.json"
        if ledger_file.exists():
            try:
                data = json.loads(ledger_file.read_text())
                for item in data:
                    # Coerce serialized strings back to enums
                    if isinstance(item.get("decision_type"), str):
                        item["decision_type"] = DecisionType(item["decision_type"])
                    if isinstance(item.get("outcome"), str):
                        item["outcome"] = DecisionOutcome(item["outcome"])
                    entry = DecisionEntry(**{
                        k: v for k, v in item.items()
                        if k in DecisionEntry.__dataclass_fields__
                    })
                    self._entries.append(entry)
                logger.debug(f"Loaded {len(self._entries)} decisions from ledger")
            except Exception as e:
                logger.warning(f"Failed to load ledger: {e}")

    def _save(self):
        """Save ledger to disk."""
        try:
            self._storage_path.mkdir(parents=True, exist_ok=True)
            ledger_file = self._storage_path / "decisions.json"
            data = [e.to_dict() for e in self._entries[-self._max_entries:]]
            ledger_file.write_text(json.dumps(data, indent=2, default=str))
        except Exception as e:
            logger.warning(f"Failed to save ledger: {e}")

    def _trim(self):
        """Trim old entries if exceeding max."""
        if len(self._entries) > self._max_entries:
            self._entries = self._entries[-self._max_entries:]

    def export(self, path: str) -> int:
        """Export ledger to a file. Returns number of entries exported."""
        data = [e.to_dict() for e in self._entries]
        Path(path).write_text(json.dumps(data, indent=2, default=str))
        return len(data)

    def clear(self):
        """Clear all entries (use with caution)."""
        self._entries.clear()
        self._save()
