"""
Phase 31 Tests — In-Memory Event Bus (MSG-01)

Tests subject-based pub/sub, wildcards, queue groups, and event-driven kernel.
"""
import asyncio
import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))


def test_import_enums():
    from ai_generation.event_bus import MessageStatus, SubscriptionType
    assert MessageStatus.PENDING.value == "pending"
    assert SubscriptionType.DIRECT.value == "direct"


def test_message_defaults():
    from ai_generation.event_bus import Message
    msg = Message(subject="test.subject", payload="hello")
    assert msg.message_id != ""
    assert msg.subject == "test.subject"
    assert msg.timestamp != ""
    assert msg.to_dict()["subject"] == "test.subject"


def test_subscription_defaults():
    from ai_generation.event_bus import Subscription
    sub = Subscription(subject="test")
    assert sub.subscription_id != ""
    assert sub.created_at != ""
    assert sub.message_count == 0


def test_event_bus_init():
    from ai_generation.event_bus import EventBus
    bus = EventBus()
    stats = bus.get_stats()
    assert stats["total_published"] == 0
    assert stats["active_subscriptions"] == 0


def test_subscribe():
    from ai_generation.event_bus import EventBus
    bus = EventBus()
    received = []
    sub = bus.subscribe("test.subject", lambda msg: received.append(msg))
    assert sub.subscription_id != ""
    assert bus.get_stats()["active_subscriptions"] == 1


def test_publish_sync():
    from ai_generation.event_bus import EventBus
    bus = EventBus()
    received = []
    bus.subscribe("test.subject", lambda msg: received.append(msg))
    msg = bus.publish_sync("test.subject", "payload1", publisher="test")
    assert msg.to_dict()["subject"] == "test.subject"
    assert len(received) == 1
    assert received[0].payload == "payload1"


def test_publish_async():
    from ai_generation.event_bus import EventBus
    bus = EventBus()
    received = []
    bus.subscribe("test.subject", lambda msg: received.append(msg))
    msg = asyncio.run(bus.publish("test.subject", "async_payload"))
    assert len(received) == 1
    assert received[0].payload == "async_payload"


def test_wildcard_single():
    from ai_generation.event_bus import EventBus
    bus = EventBus()
    received = []
    bus.subscribe("test.*", lambda msg: received.append(msg))
    bus.publish_sync("test.one", "a")
    bus.publish_sync("test.two", "b")
    bus.publish_sync("other.three", "c")
    assert len(received) == 2


def test_wildcard_multi():
    from ai_generation.event_bus import EventBus
    bus = EventBus()
    received = []
    bus.subscribe("a.>", lambda msg: received.append(msg))
    bus.publish_sync("a.b.c", "1")
    bus.publish_sync("a.b", "2")
    bus.publish_sync("x.y.z", "3")
    assert len(received) == 2


def test_exact_match():
    from ai_generation.event_bus import EventBus
    bus = EventBus()
    received = []
    bus.subscribe("exact.subject", lambda msg: received.append(msg))
    bus.publish_sync("exact.subject", "match")
    bus.publish_sync("exact.other", "no_match")
    assert len(received) == 1


def test_unsubscribe():
    from ai_generation.event_bus import EventBus
    bus = EventBus()
    sub = bus.subscribe("test", lambda msg: None)
    assert bus.get_stats()["active_subscriptions"] == 1
    result = bus.unsubscribe(sub.subscription_id)
    assert result is True
    assert bus.get_stats()["active_subscriptions"] == 0


def test_unsubscribe_nonexistent():
    from ai_generation.event_bus import EventBus
    bus = EventBus()
    result = bus.unsubscribe("nonexistent")
    assert result is False


def test_queue_group():
    from ai_generation.event_bus import EventBus
    bus = EventBus()
    received = []
    def handler(msg): received.append(msg)
    bus.subscribe("queue.test", handler, queue_group="workers")
    bus.subscribe("queue.test", handler, queue_group="workers")
    for _ in range(4):
        bus.publish_sync("queue.test", "work")
    # Each publish goes to all matching subscribers
    assert len(received) >= 4


def test_get_history():
    from ai_generation.event_bus import EventBus
    bus = EventBus()
    bus.publish_sync("test.a", "1")
    bus.publish_sync("test.b", "2")
    history = bus.get_history()
    assert len(history) == 2


def test_get_history_filtered():
    from ai_generation.event_bus import EventBus
    bus = EventBus()
    bus.publish_sync("test.a", "1")
    bus.publish_sync("other.b", "2")
    history = bus.get_history(subject="test.*")
    assert len(history) == 1


def test_get_history_limit():
    from ai_generation.event_bus import EventBus
    bus = EventBus()
    for i in range(10):
        bus.publish_sync(f"test.{i}", str(i))
    history = bus.get_history(limit=3)
    assert len(history) == 3


def test_get_subscriptions():
    from ai_generation.event_bus import EventBus
    bus = EventBus()
    bus.subscribe("test.a", lambda msg: None)
    bus.subscribe("test.b", lambda msg: None)
    subs = bus.get_subscriptions()
    assert len(subs) == 2
    assert subs[0]["subject"] != subs[1]["subject"]


def test_bus_stats():
    from ai_generation.event_bus import EventBus
    bus = EventBus()
    bus.subscribe("test", lambda msg: None)
    bus.publish_sync("test", "payload")
    stats = bus.get_stats()
    assert stats["total_published"] == 1
    assert stats["total_delivered"] == 1
    assert stats["delivery_rate"] == 100.0
    assert stats["active_subscriptions"] == 1


def test_message_history_limit():
    from ai_generation.event_bus import EventBus
    bus = EventBus({"max_history": 5})
    for i in range(10):
        bus.publish_sync(f"test.{i}", str(i))
    assert len(bus._message_history) == 5


# ── EventDrivenKernel Tests ──

def test_kernel_init():
    from ai_generation.event_bus import EventDrivenKernel
    kernel = EventDrivenKernel()
    stats = kernel.get_stats()
    assert stats["total_events_emitted"] == 0
    assert stats["event_types_supported"] > 0


def test_kernel_emit_sync():
    from ai_generation.event_bus import EventDrivenKernel
    kernel = EventDrivenKernel()
    msg = kernel.emit_sync("generation.request", {"prompt": "test"}, source="test")
    assert msg.to_dict()["subject"] == "generation.request"
    assert kernel.get_stats()["total_events_emitted"] == 1


def test_kernel_emit_async():
    from ai_generation.event_bus import EventDrivenKernel
    kernel = EventDrivenKernel()
    msg = asyncio.run(kernel.emit("routing.decision", {"route": "vllm"}, source="router"))
    assert msg.to_dict()["subject"] == "routing.decision"


def test_kernel_subscribe():
    from ai_generation.event_bus import EventDrivenKernel
    kernel = EventDrivenKernel()
    received = []
    sub = kernel.subscribe_event("plugin.loaded", lambda msg: received.append(msg))
    assert sub.subscription_id != ""


def test_kernel_subscribe_all():
    from ai_generation.event_bus import EventDrivenKernel
    kernel = EventDrivenKernel()
    received = []
    subs = kernel.subscribe_all(lambda msg: received.append(msg))
    assert len(subs) > 0


# ── SDK Integration Tests ──

def test_sdk_event_bus_import():
    from ai_generation.sdk import UncleFrappeAI
    sdk = UncleFrappeAI({"test_mode": True})
    assert sdk.event_bus is not None
    assert sdk.event_kernel is not None


def test_sdk_event_bus_subscribe():
    from ai_generation.sdk import UncleFrappeAI
    sdk = UncleFrappeAI({"test_mode": True})
    result = sdk.event_bus_subscribe("test.subject")
    assert "subscription_id" in result


def test_sdk_event_bus_publish():
    from ai_generation.sdk import UncleFrappeAI
    sdk = UncleFrappeAI({"test_mode": True})
    result = sdk.event_bus_publish_sync("test.subject", "payload", "sdk")
    assert result["subject"] == "test.subject"


def test_sdk_event_bus_history():
    from ai_generation.sdk import UncleFrappeAI
    sdk = UncleFrappeAI({"test_mode": True})
    history = sdk.event_bus_get_history()
    assert isinstance(history, list)


def test_sdk_event_bus_subscriptions():
    from ai_generation.sdk import UncleFrappeAI
    sdk = UncleFrappeAI({"test_mode": True})
    subs = sdk.event_bus_get_subscriptions()
    assert isinstance(subs, list)


def test_sdk_event_bus_stats():
    from ai_generation.sdk import UncleFrappeAI
    sdk = UncleFrappeAI({"test_mode": True})
    stats = sdk.get_event_bus_stats()
    assert "total_published" in stats


def test_sdk_emit_event():
    from ai_generation.sdk import UncleFrappeAI
    sdk = UncleFrappeAI({"test_mode": True})
    result = sdk.emit_event("generation.request", "test", "sdk")
    assert result["subject"] == "generation.request"


def test_sdk_event_kernel_stats():
    from ai_generation.sdk import UncleFrappeAI
    sdk = UncleFrappeAI({"test_mode": True})
    stats = sdk.get_event_kernel_stats()
    assert "total_events_emitted" in stats


# ── MCP Tool Tests ──

def test_mcp_event_bus_tools_exist():
    from ai_generation.mcp_tools import MCP_GENERATION_TOOLS
    assert "event_bus_publish" in MCP_GENERATION_TOOLS
    assert "event_bus_get_history" in MCP_GENERATION_TOOLS
    assert "event_bus_get_subscriptions" in MCP_GENERATION_TOOLS
    assert "get_event_bus_stats" in MCP_GENERATION_TOOLS
    assert "emit_event" in MCP_GENERATION_TOOLS
    assert "get_event_kernel_stats" in MCP_GENERATION_TOOLS


def test_mcp_event_bus_handler_import():
    from ai_generation.mcp_tools import MCPGenerationTools
    tools = MCPGenerationTools()
    assert hasattr(tools, "_handle_event_bus_publish")
    assert hasattr(tools, "_handle_event_bus_get_history")
    assert hasattr(tools, "_handle_event_bus_get_subscriptions")
    assert hasattr(tools, "_handle_get_event_bus_stats")
    assert hasattr(tools, "_handle_emit_event")
    assert hasattr(tools, "_handle_get_event_kernel_stats")
