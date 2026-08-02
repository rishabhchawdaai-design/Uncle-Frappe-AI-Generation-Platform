"""
Tests for the Durable Event Log (ACOS Messaging & Events Research).

Covers event taxonomy classification, per-class delivery guarantees,
SQLite persistence, replay, failure->retry->dead-letter flow, retention,
and SDK/CLI/MCP integration. All offline (stdlib sqlite3).
"""
import asyncio
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))


@pytest.fixture
def isolated_log(tmp_path):
    from ai_generation.event_log import DurableEventLog

    return DurableEventLog({"db_path": str(tmp_path / "events.db")})


@pytest.fixture
def isolated_sdk(tmp_path):
    from ai_generation import UncleFrappeAI

    return UncleFrappeAI(config={
        "event_log": {"db_path": str(tmp_path / "sdk_events.db")},
    })


# ── Taxonomy & delivery guarantees ──────────────────────────────────────

def test_classify_subject():
    from ai_generation.event_log import classify_subject

    assert classify_subject("request.completed").value == "request"
    assert classify_subject("request.failed").value == "request"
    assert classify_subject("workflow.started").value == "workflow"
    assert classify_subject("health.critical").value == "health"
    assert classify_subject("health.warning").value == "health"
    assert classify_subject("kernel.request").value == "kernel"
    assert classify_subject("node.joined").value == "kernel"
    assert classify_subject("capability.changed").value == "kernel"
    assert classify_subject("plugin.registered").value == "system"
    assert classify_subject("benchmark.completed").value == "system"


def test_delivery_policies():
    from ai_generation.event_log import DELIVERY_POLICIES, EventClass

    assert DELIVERY_POLICIES[EventClass.REQUEST]["guarantee"] == "at_least_once"
    assert DELIVERY_POLICIES[EventClass.REQUEST]["max_attempts"] == 3
    assert DELIVERY_POLICIES[EventClass.WORKFLOW]["max_attempts"] == 5
    assert DELIVERY_POLICIES[EventClass.HEALTH]["guarantee"] == "at_most_once"
    assert DELIVERY_POLICIES[EventClass.HEALTH]["persist"] is False
    assert DELIVERY_POLICIES[EventClass.KERNEL]["max_attempts"] == 3
    assert DELIVERY_POLICIES[EventClass.SYSTEM]["max_attempts"] == 3


# ── Persistence & replay ────────────────────────────────────────────────

def test_append_and_replay(isolated_log):
    e = isolated_log.append("request.completed", {"task_id": "t1"}, publisher="engine")
    assert e.event_class == "request"
    assert e.guarantee == "at_least_once"
    assert e.max_attempts == 3

    rows = isolated_log.replay(subject="request.*")
    assert len(rows) == 1
    assert rows[0].payload == {"task_id": "t1"}
    assert rows[0].publisher == "engine"


def test_replay_filters(isolated_log):
    isolated_log.append("workflow.started", {"workflow_id": "w1"})
    isolated_log.append("health.critical", {"node": "n1"})
    isolated_log.append("request.completed", {"task_id": "t1"})

    assert len(isolated_log.replay(event_class="health")) == 1
    assert len(isolated_log.replay(event_class="workflow")) == 1
    assert len(isolated_log.replay(subject="*")) == 3
    # health.* is at-most-once: delivered immediately, so only 2 pending
    assert len(isolated_log.replay(status="pending")) == 2


def test_health_events_not_persisted(isolated_log):
    e = isolated_log.append("health.critical", {"node": "n1"})
    assert e.status == "delivered"
    assert e.guarantee == "at_most_once"
    assert len(isolated_log.replay(event_class="health", status="pending")) == 0
    assert len(isolated_log.replay(event_class="health")) == 1


# ── Failure → retry → dead-letter ───────────────────────────────────────

def test_failure_flow_to_dead_letter(isolated_log):
    e = isolated_log.append("request.completed", {"task_id": "t1"})
    assert isolated_log.record_failure(e.event_id, "err1") == "retry"
    assert isolated_log.replay(subject="request.completed")[0].attempts == 1
    assert isolated_log.record_failure(e.event_id, "err2") == "retry"
    assert isolated_log.record_failure(e.event_id, "err3") == "dead_letter"
    dlq = isolated_log.dead_letter_queue()
    assert len(dlq) == 1
    assert dlq[0].status == "dead_letter"
    assert dlq[0].attempts == 3


def test_mark_delivered(isolated_log):
    e = isolated_log.append("request.completed", {"task_id": "t1"})
    assert isolated_log.mark_delivered(e.event_id) is True
    assert isolated_log.replay(subject="request.completed")[0].status == "delivered"


# ── Retention ───────────────────────────────────────────────────────────

def test_purge(isolated_log):
    isolated_log.append("request.completed", {"task_id": "t1"})
    e2 = isolated_log.append("workflow.started", {"workflow_id": "w1"})
    for _ in range(5):  # workflow.* max_attempts = 5
        isolated_log.record_failure(e2.event_id, "x")
    assert len(isolated_log.dead_letter_queue()) == 1
    purged = isolated_log.purge(status="dead_letter")
    assert purged == 1
    assert len(isolated_log.dead_letter_queue()) == 0
    assert len(isolated_log.replay(subject="request.completed")) == 1


def test_stats(isolated_log):
    isolated_log.append("request.completed", {"task_id": "t1"})
    isolated_log.append("workflow.started", {"workflow_id": "w1"})
    stats = isolated_log.stats()
    assert stats["total_events"] == 2
    assert stats["by_class"] == {"request": 1, "workflow": 1}
    assert stats["delivery_policies"]["health"]["guarantee"] == "at_most_once"


# ── SDK integration ─────────────────────────────────────────────────────

def test_sdk_emit_and_replay(isolated_sdk):
    event = isolated_sdk.emit_durable_event("request.completed", {"task_id": "x1"})
    assert event["event_class"] == "request"
    assert event["status"] == "pending"

    rows = isolated_sdk.replay_events(subject="request.*")
    assert len(rows) == 1
    assert rows[0]["payload"] == {"task_id": "x1"}


def test_sdk_event_classes(isolated_sdk):
    classes = isolated_sdk.list_event_classes()
    assert set(classes.keys()) == {"kernel", "request", "workflow", "health", "system"}
    assert classes["workflow"]["max_attempts"] == 5
    assert classes["health"]["persist"] is False


def test_sdk_stats_and_purge(isolated_sdk):
    isolated_sdk.emit_durable_event("request.completed", {"task_id": "x1"})
    e2 = isolated_sdk.emit_durable_event("workflow.started", {"workflow_id": "w1"})
    # force to DLQ (workflow.* max_attempts = 5)
    for _ in range(5):
        isolated_sdk.event_log.record_failure(e2["event_id"], "boom")
    stats = isolated_sdk.get_event_log_stats()
    assert stats["total_events"] == 2
    assert stats["by_status"].get("dead_letter", 0) == 1
    purged = isolated_sdk.purge_events()
    assert purged == 1
    assert isolated_sdk.get_event_log_stats()["by_status"].get("dead_letter", 0) == 0


def test_sdk_dead_letter_queue(isolated_sdk):
    e = isolated_sdk.emit_durable_event("system.plugin_failed", {"plugin": "p1"})
    for _ in range(3):
        isolated_sdk.event_log.record_failure(e["event_id"], "boom")
    dlq = isolated_sdk.dead_letter_queue()
    assert len(dlq) == 1
    assert dlq[0]["subject"] == "system.plugin_failed"


# ── CLI integration ─────────────────────────────────────────────────────

def test_cli_event_classes(capsys):
    import ai_generation.cli as cli

    result = asyncio.run(cli.cmd_event_classes())
    out = capsys.readouterr().out
    assert len(result) == 5
    assert "workflow" in out
    assert "at_most_once" in out


def test_cli_event_emit_replay(tmp_path, capsys):
    import ai_generation.cli as cli

    os.environ["ACOS_EVENT_LOG_PATH"] = str(tmp_path / "cli_events.db")
    try:
        event = asyncio.run(cli.cmd_event_emit("request.completed", '{"task_id": "cli-1"}'))
        capsys.readouterr().out
        assert event["event_class"] == "request"
        rows = asyncio.run(cli.cmd_event_replay("request.*"))
        out = capsys.readouterr().out
        assert len(rows) == 1
        assert "request.completed" in out
    finally:
        os.environ.pop("ACOS_EVENT_LOG_PATH", None)


def test_cli_event_stats(tmp_path, capsys):
    import ai_generation.cli as cli

    os.environ["ACOS_EVENT_LOG_PATH"] = str(tmp_path / "cli_stats.db")
    try:
        asyncio.run(cli.cmd_event_emit("workflow.started", '{"workflow_id": "w"}'))
        capsys.readouterr().out
        result = asyncio.run(cli.cmd_event_stats())
        out = capsys.readouterr().out
        assert result["total_events"] == 1
        assert "Total events" in out
    finally:
        os.environ.pop("ACOS_EVENT_LOG_PATH", None)


# ── MCP integration ─────────────────────────────────────────────────────

def test_mcp_event_tools_registered():
    from ai_generation.mcp_tools import MCP_GENERATION_TOOLS, MCPGenerationTools

    for tool in ("emit_durable_event", "replay_events", "get_event_log_stats",
                 "purge_events", "list_event_classes"):
        assert tool in MCP_GENERATION_TOOLS, f"missing {tool}"
        assert "inputSchema" in MCP_GENERATION_TOOLS[tool]
    handler = MCPGenerationTools()
    for tool in ("emit_durable_event", "replay_events", "get_event_log_stats",
                 "purge_events", "list_event_classes"):
        assert hasattr(handler, f"_handle_{tool}"), f"missing handler {tool}"


def test_mcp_emit_and_replay(tmp_path):
    from ai_generation.mcp_tools import MCPGenerationTools

    os.environ["ACOS_EVENT_LOG_PATH"] = str(tmp_path / "mcp_events.db")
    try:
        handler = MCPGenerationTools()
        event = asyncio.run(handler.handle("emit_durable_event", {
            "subject": "workflow.stage_completed", "payload": {"stage": "gen"} }))
        assert event["event_class"] == "workflow"
        assert event["max_attempts"] == 5
        replay = asyncio.run(handler.handle("replay_events", {
            "subject": "workflow.*" }))
        assert len(replay["events"]) == 1
        stats = asyncio.run(handler.handle("get_event_log_stats", {}))
        assert stats["total_events"] == 1
        classes = asyncio.run(handler.handle("list_event_classes", {}))
        assert len(classes["event_classes"]) == 5
    finally:
        os.environ.pop("ACOS_EVENT_LOG_PATH", None)
