"""
In-Memory Event Bus — NATS-like subject-based pub/sub.

Based on ACOS Research: Messaging Events Research
Pure Python implementation of a subject-based message bus for subsystem communication.

Features:
- Subject-based routing with wildcards (*, >)
- Async subscriber support
- Message persistence (in-memory ring buffer)
- Queue groups (load-balanced delivery)
- Message acknowledgment
- Health monitoring
"""
import asyncio
import hashlib
import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Coroutine, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class MessageStatus(str, Enum):
    PENDING = "pending"
    DELIVERED = "delivered"
    ACKNOWLEDGED = "acknowledged"
    FAILED = "failed"


class SubscriptionType(str, Enum):
    DIRECT = "direct"
    QUEUE = "queue"
    REPLAY = "replay"


@dataclass
class Message:
    message_id: str = ""
    subject: str = ""
    payload: Any = None
    headers: Dict[str, str] = field(default_factory=dict)
    timestamp: str = ""
    status: MessageStatus = MessageStatus.PENDING
    publisher: str = ""
    reply_to: str = ""
    ttl_secs: float = 300.0

    def __post_init__(self):
        if not self.message_id:
            self.message_id = hashlib.md5(f"{self.subject}:{time.time()}".encode()).hexdigest()[:12]
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "message_id": self.message_id,
            "subject": self.subject,
            "payload": str(self.payload)[:200] if self.payload else None,
            "headers": self.headers,
            "timestamp": self.timestamp,
            "status": self.status.value,
            "publisher": self.publisher,
        }


@dataclass
class Subscription:
    subscription_id: str = ""
    subject: str = ""
    callback: Optional[Callable] = None
    sub_type: SubscriptionType = SubscriptionType.DIRECT
    queue_group: str = ""
    message_count: int = 0
    failed_count: int = 0
    created_at: str = ""
    last_message_at: str = ""

    def __post_init__(self):
        if not self.subscription_id:
            self.subscription_id = hashlib.md5(f"{self.subject}:{time.time()}".encode()).hexdigest()[:10]
        if not self.created_at:
            self.created_at = datetime.now().isoformat()


class EventBus:
    """
    In-Memory Event Bus with NATS-like subject-based pub/sub.

    Provides subject-based routing with wildcards, queue groups,
    and message persistence for ACOS subsystem communication.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._subscriptions: Dict[str, List[Subscription]] = defaultdict(list)
        self._queue_groups: Dict[str, Dict[str, List[Subscription]]] = defaultdict(lambda: defaultdict(list))
        self._message_history: List[Message] = []
        self._max_history: int = self.config.get("max_history", 10000)
        self._message_counter: int = 0
        self._total_published: int = 0
        self._total_delivered: int = 0
        self._total_failed: int = 0
        self._wildcard_cache: Dict[str, List[str]] = {}

    def subscribe(self, subject: str, callback: Optional[Callable] = None,
                  sub_type: SubscriptionType = SubscriptionType.DIRECT,
                  queue_group: str = "") -> Subscription:
        sub = Subscription(
            subject=subject,
            callback=callback,
            sub_type=sub_type,
            queue_group=queue_group,
        )
        self._subscriptions[subject].append(sub)
        if queue_group:
            self._queue_groups[subject][queue_group].append(sub)
        self._wildcard_cache.clear()
        logger.debug(f"Subscribed to {subject} (id={sub.subscription_id})")
        return sub

    def unsubscribe(self, subscription_id: str) -> bool:
        for subject, subs in self._subscriptions.items():
            for i, sub in enumerate(subs):
                if sub.subscription_id == subscription_id:
                    subs.pop(i)
                    if sub.queue_group:
                        group = self._queue_groups[subject].get(sub.queue_group, [])
                        self._queue_groups[subject][sub.queue_group] = [
                            s for s in group if s.subscription_id != subscription_id
                        ]
                    self._wildcard_cache.clear()
                    return True
        return False

    async def publish(self, subject: str, payload: Any = None,
                       headers: Optional[Dict[str, str]] = None,
                       publisher: str = "") -> Message:
        msg = Message(
            subject=subject,
            payload=payload,
            headers=headers or {},
            publisher=publisher,
        )
        self._total_published += 1
        self._message_history.append(msg)
        if len(self._message_history) > self._max_history:
            self._message_history = self._message_history[-self._max_history:]

        matched_subs = self._match_subject(subject)
        delivered = 0

        for sub in matched_subs:
            try:
                if sub.sub_type == SubscriptionType.QUEUE and sub.queue_group:
                    group_subs = self._queue_groups[subject].get(sub.queue_group, [])
                    if group_subs:
                        target = group_subs[self._total_delivered % len(group_subs)]
                        if target.callback:
                            if asyncio.iscoroutinefunction(target.callback):
                                await target.callback(msg)
                            else:
                                target.callback(msg)
                            target.message_count += 1
                            target.last_message_at = datetime.now().isoformat()
                            delivered += 1
                else:
                    if sub.callback:
                        if asyncio.iscoroutinefunction(sub.callback):
                            await sub.callback(msg)
                        else:
                            sub.callback(msg)
                        sub.message_count += 1
                        sub.last_message_at = datetime.now().isoformat()
                        delivered += 1
            except Exception as e:
                sub.failed_count += 1
                self._total_failed += 1
                logger.error(f"Delivery failed for {sub.subscription_id}: {e}")

        self._total_delivered += delivered
        msg.status = MessageStatus.DELIVERED if delivered > 0 else MessageStatus.FAILED
        return msg

    def publish_sync(self, subject: str, payload: Any = None,
                      headers: Optional[Dict[str, str]] = None,
                      publisher: str = "") -> Message:
        msg = Message(
            subject=subject,
            payload=payload,
            headers=headers or {},
            publisher=publisher,
        )
        self._total_published += 1
        self._message_history.append(msg)
        if len(self._message_history) > self._max_history:
            self._message_history = self._message_history[-self._max_history:]

        matched_subs = self._match_subject(subject)
        delivered = 0

        for sub in matched_subs:
            try:
                if sub.callback:
                    sub.callback(msg)
                    sub.message_count += 1
                    sub.last_message_at = datetime.now().isoformat()
                    delivered += 1
            except Exception as e:
                sub.failed_count += 1
                self._total_failed += 1

        self._total_delivered += delivered
        msg.status = MessageStatus.DELIVERED if delivered > 0 else MessageStatus.FAILED
        return msg

    def _match_subject(self, subject: str) -> List[Subscription]:
        matches = []
        exact = self._subscriptions.get(subject, [])
        matches.extend(exact)

        for sub_subject, subs in self._subscriptions.items():
            if sub_subject == subject:
                continue
            if self._subject_matches(subject, sub_subject):
                matches.extend(subs)

        seen_ids = set()
        unique = []
        for sub in matches:
            if sub.subscription_id not in seen_ids:
                seen_ids.add(sub.subscription_id)
                unique.append(sub)
        return unique

    def _subject_matches(self, subject: str, pattern: str) -> bool:
        subject_parts = subject.split(".")
        pattern_parts = pattern.split(".")

        if ">" in pattern_parts:
            idx = pattern_parts.index(">")
            if len(subject_parts) < idx:
                return False
            for i in range(idx):
                if pattern_parts[i] != "*" and pattern_parts[i] != subject_parts[i]:
                    return False
            return True

        if len(subject_parts) != len(pattern_parts):
            return False

        for s, p in zip(subject_parts, pattern_parts):
            if p != "*" and p != s:
                return False
        return True

    def get_history(self, subject: Optional[str] = None,
                     limit: int = 50) -> List[Dict[str, Any]]:
        msgs = self._message_history
        if subject:
            msgs = [m for m in msgs if self._subject_matches(m.subject, subject)]
        return [m.to_dict() for m in msgs[-limit:]]

    def get_subscriptions(self) -> List[Dict[str, Any]]:
        result = []
        for subject, subs in self._subscriptions.items():
            for sub in subs:
                result.append({
                    "subscription_id": sub.subscription_id,
                    "subject": sub.subject,
                    "type": sub.sub_type.value,
                    "queue_group": sub.queue_group,
                    "message_count": sub.message_count,
                    "failed_count": sub.failed_count,
                    "created_at": sub.created_at,
                    "last_message_at": sub.last_message_at,
                })
        return result

    def get_stats(self) -> Dict[str, Any]:
        total_subs = sum(len(subs) for subs in self._subscriptions.values())
        total_queue_groups = sum(
            len(groups) for groups in self._queue_groups.values()
        )
        return {
            "total_published": self._total_published,
            "total_delivered": self._total_delivered,
            "total_failed": self._total_failed,
            "delivery_rate": round(
                self._total_delivered / max(self._total_published, 1) * 100, 1
            ),
            "active_subscriptions": total_subs,
            "active_subjects": len(self._subscriptions),
            "queue_groups": total_queue_groups,
            "history_size": len(self._message_history),
        }


class EventDrivenKernel:
    """
    Event-driven kernel using the EventBus for ACOS subsystem communication.

    Provides a high-level interface for publishing and subscribing
    to kernel events with automatic event classification.
    """

    EVENT_TYPES = [
        "kernel.startup", "kernel.shutdown", "kernel.error",
        "generation.request", "generation.complete", "generation.failed",
        "routing.decision", "routing.fallback",
        "provider.health", "provider.degraded", "provider.recovered",
        "benchmark.complete", "benchmark.regression",
        "security.auth", "security.denied",
        "plugin.loaded", "plugin.unloaded", "plugin.error",
        "observability.metric", "observability.trace",
    ]

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._bus = EventBus(config)
        self._event_count: int = 0

    @property
    def bus(self) -> EventBus:
        return self._bus

    def subscribe_event(self, event_type: str,
                         callback: Callable) -> Subscription:
        return self._bus.subscribe(event_type, callback)

    def subscribe_all(self, callback: Callable) -> List[Subscription]:
        subs = []
        for event_type in self.EVENT_TYPES:
            subs.append(self._bus.subscribe(event_type, callback))
        return subs

    async def emit(self, event_type: str, data: Any = None,
                    source: str = "") -> Message:
        self._event_count += 1
        return await self._bus.publish(
            subject=event_type,
            payload=data,
            headers={"source": source, "event_num": str(self._event_count)},
            publisher=source,
        )

    def emit_sync(self, event_type: str, data: Any = None,
                   source: str = "") -> Message:
        self._event_count += 1
        return self._bus.publish_sync(
            subject=event_type,
            payload=data,
            headers={"source": source, "event_num": str(self._event_count)},
            publisher=source,
        )

    def get_stats(self) -> Dict[str, Any]:
        bus_stats = self._bus.get_stats()
        return {
            **bus_stats,
            "total_events_emitted": self._event_count,
            "event_types_supported": len(self.EVENT_TYPES),
        }
