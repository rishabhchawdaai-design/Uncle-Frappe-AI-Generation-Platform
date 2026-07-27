"""
Phase 17 Tests — Decision Ledger

Tests immutable audit trail for platform decisions.
"""
import pytest
import sys
import os
import tempfile
import shutil
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))


# ── DecisionEntry Tests ────────────────────────────────────────

def test_decision_entry_import():
    from ai_generation.decision_ledger import (
        DecisionEntry, DecisionType, DecisionOutcome,
    )
    assert DecisionType.ROUTING.value == "routing"
    assert DecisionOutcome.SUCCESS.value == "success"


def test_decision_entry_defaults():
    from ai_generation.decision_ledger import DecisionEntry, DecisionType
    entry = DecisionEntry(decision_type=DecisionType.ROUTING)
    assert entry.decision_id.startswith("dec-")
    assert entry.timestamp != ""
    assert entry.decision_type == DecisionType.ROUTING
    assert entry.outcome.value == "success"


def test_decision_entry_serialization():
    from ai_generation.decision_ledger import DecisionEntry, DecisionType
    entry = DecisionEntry(
        decision_type=DecisionType.GENERATION,
        selected_provider="pollinations",
        selected_model="flux",
        confidence_score=0.85,
    )
    d = entry.to_dict()
    assert d["decision_type"] == "generation"
    assert d["selected_provider"] == "pollinations"
    assert d["confidence_score"] == 0.85


# ── DecisionLedger Tests ──────────────────────────────────────

def test_ledger_init():
    from ai_generation.decision_ledger import DecisionLedger
    ledger = DecisionLedger()
    stats = ledger.get_stats()
    assert stats["total_decisions"] == 0
    assert stats["session_id"] != ""


def test_ledger_record():
    from ai_generation.decision_ledger import DecisionLedger, DecisionType
    ledger = DecisionLedger()
    entry = ledger.record(DecisionType.ROUTING, selected_provider="test")
    assert entry.decision_id.startswith("dec-")
    assert stats_after(ledger) == 1


def stats_after(ledger):
    return ledger.get_stats()["total_decisions"]


def test_ledger_record_routing():
    from ai_generation.decision_ledger import DecisionLedger
    ledger = DecisionLedger()
    entry = ledger.record_routing(
        request_id="req-1", prompt="generate image", task_type="text_to_image",
        selected_provider="pollinations", selected_model="flux",
        confidence=0.9, reasoning="Best free provider",
    )
    assert entry.selected_provider == "pollinations"
    assert entry.confidence_score == 0.9


def test_ledger_record_negotiation():
    from ai_generation.decision_ledger import DecisionLedger
    ledger = DecisionLedger()
    entry = ledger.record_negotiation(
        request_id="req-2", prompt="edit image", task_type="image_editing",
        selected_provider="stability", selected_model="sd3",
        confidence=0.85, trade_offs=[{"dimension": "cost", "impact": "$0.01"}],
    )
    assert entry.selected_provider == "stability"
    assert len(entry.trade_offs) == 1


def test_ledger_record_generation():
    from ai_generation.decision_ledger import DecisionLedger, DecisionOutcome
    ledger = DecisionLedger()
    entry = ledger.record_generation(
        request_id="req-3", prompt="test", task_type="image_generation",
        provider="pollinations", model="flux",
        outcome=DecisionOutcome.SUCCESS,
        latency_ms=8000, quality_score=0.75,
    )
    assert entry.outcome == DecisionOutcome.SUCCESS
    assert entry.latency_ms == 8000


def test_ledger_record_generation_failure():
    from ai_generation.decision_ledger import DecisionLedger, DecisionOutcome
    ledger = DecisionLedger()
    entry = ledger.record_generation(
        request_id="req-4", prompt="test", task_type="image_generation",
        provider="stability", model="sd3",
        outcome=DecisionOutcome.FAILURE,
        error="API key invalid",
    )
    assert entry.outcome == DecisionOutcome.FAILURE
    assert entry.error == "API key invalid"


def test_ledger_record_recovery():
    from ai_generation.decision_ledger import DecisionLedger
    ledger = DecisionLedger()
    entry = ledger.record_recovery(
        request_id="req-5", failed_provider="stability",
        error="API error", recovery_provider="pollinations",
        reasoning="Stability down, using free fallback",
    )
    assert entry.selected_provider == "pollinations"
    assert entry.metadata["failed_provider"] == "stability"


def test_ledger_record_health_check():
    from ai_generation.decision_ledger import DecisionLedger
    ledger = DecisionLedger()
    entry = ledger.record_health_check(
        provider="pollinations", healthy=True, latency_ms=150,
    )
    assert entry.outcome.value == "success"
    entry2 = ledger.record_health_check(
        provider="stability", healthy=False, error="timeout",
    )
    assert entry2.outcome.value == "failure"


def test_ledger_query_by_type():
    from ai_generation.decision_ledger import DecisionLedger, DecisionType
    ledger = DecisionLedger()
    ledger.record(DecisionType.ROUTING, selected_provider="a")
    ledger.record(DecisionType.GENERATION, selected_provider="b")
    ledger.record(DecisionType.ROUTING, selected_provider="c")
    routing = ledger.query(decision_type=DecisionType.ROUTING)
    assert len(routing) == 2


def test_ledger_query_by_provider():
    from ai_generation.decision_ledger import DecisionLedger, DecisionType
    ledger = DecisionLedger()
    ledger.record(DecisionType.ROUTING, selected_provider="pollinations")
    ledger.record(DecisionType.ROUTING, selected_provider="stability")
    ledger.record(DecisionType.GENERATION, selected_provider="pollinations")
    pol = ledger.query(provider="pollinations")
    assert len(pol) == 2


def test_ledger_query_by_outcome():
    from ai_generation.decision_ledger import DecisionLedger, DecisionType, DecisionOutcome
    ledger = DecisionLedger()
    ledger.record(DecisionType.GENERATION, outcome=DecisionOutcome.SUCCESS)
    ledger.record(DecisionType.GENERATION, outcome=DecisionOutcome.FAILURE)
    failures = ledger.query(outcome=DecisionOutcome.FAILURE)
    assert len(failures) == 1


def test_ledger_get_recent():
    from ai_generation.decision_ledger import DecisionLedger, DecisionType
    ledger = DecisionLedger()
    for i in range(10):
        ledger.record(DecisionType.ROUTING, selected_provider=f"p{i}")
    recent = ledger.get_recent(limit=5)
    assert len(recent) == 5


def test_ledger_get_failures():
    from ai_generation.decision_ledger import DecisionLedger, DecisionType, DecisionOutcome
    ledger = DecisionLedger()
    ledger.record(DecisionType.GENERATION, outcome=DecisionOutcome.SUCCESS)
    ledger.record(DecisionType.GENERATION, outcome=DecisionOutcome.FAILURE)
    ledger.record(DecisionType.GENERATION, outcome=DecisionOutcome.FALLBACK_USED)
    failures = ledger.get_failures()
    assert len(failures) == 1


def test_ledger_stats():
    from ai_generation.decision_ledger import DecisionLedger, DecisionType
    ledger = DecisionLedger()
    ledger.record(DecisionType.ROUTING, selected_provider="pollinations")
    ledger.record(DecisionType.GENERATION, selected_provider="stability")
    stats = ledger.get_stats()
    assert stats["total_decisions"] == 2
    assert "routing" in stats["by_type"]
    assert "pollinations" in stats["by_provider"]


def test_ledger_provider_stats():
    from ai_generation.decision_ledger import DecisionLedger, DecisionType, DecisionOutcome
    ledger = DecisionLedger()
    ledger.record(DecisionType.GENERATION, selected_provider="pollinations", outcome=DecisionOutcome.SUCCESS, latency_ms=8000)
    ledger.record(DecisionType.GENERATION, selected_provider="pollinations", outcome=DecisionOutcome.SUCCESS, latency_ms=6000)
    ledger.record(DecisionType.GENERATION, selected_provider="pollinations", outcome=DecisionOutcome.FAILURE)
    stats = ledger.get_provider_stats("pollinations")
    assert stats["total_decisions"] == 3
    assert stats["success"] == 2
    assert stats["failure"] == 1
    assert stats["success_rate"] == 66.7


def test_ledger_persistence():
    from ai_generation.decision_ledger import DecisionLedger, DecisionType
    tmpdir = tempfile.mkdtemp()
    try:
        ledger1 = DecisionLedger(config={"ledger_path": tmpdir})
        ledger1.record(DecisionType.ROUTING, selected_provider="test")
        assert ledger1.get_stats()["total_decisions"] == 1

        # Load from same path
        ledger2 = DecisionLedger(config={"ledger_path": tmpdir})
        assert ledger2.get_stats()["total_decisions"] == 1
    finally:
        shutil.rmtree(tmpdir)


def test_ledger_export():
    from ai_generation.decision_ledger import DecisionLedger, DecisionType
    ledger = DecisionLedger()
    ledger.record(DecisionType.ROUTING, selected_provider="test")
    tmpfile = tempfile.mktemp(suffix=".json")
    try:
        count = ledger.export(tmpfile)
        assert count == 1
        import json
        data = json.loads(open(tmpfile).read())
        assert len(data) == 1
    finally:
        os.unlink(tmpfile)


def test_ledger_clear():
    from ai_generation.decision_ledger import DecisionLedger, DecisionType
    ledger = DecisionLedger()
    ledger.record(DecisionType.ROUTING, selected_provider="test")
    assert ledger.get_stats()["total_decisions"] == 1
    ledger.clear()
    assert ledger.get_stats()["total_decisions"] == 0


def test_ledger_trim():
    from ai_generation.decision_ledger import DecisionLedger, DecisionType
    ledger = DecisionLedger(config={"max_entries": 5})
    for i in range(10):
        ledger.record(DecisionType.ROUTING, selected_provider=f"p{i}")
    assert ledger.get_stats()["total_decisions"] == 5


# ── SDK Integration Tests ──────────────────────────────────────

def test_sdk_decision_ledger_import():
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    assert hasattr(ai, 'decision_ledger')
    assert hasattr(ai, 'get_decision_stats')
    assert hasattr(ai, 'get_recent_decisions')
    assert hasattr(ai, 'get_provider_decisions')
    assert hasattr(ai, 'get_decision_failures')


def test_sdk_decision_stats():
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    stats = ai.get_decision_stats()
    assert "total_decisions" in stats
    assert stats["total_decisions"] == 0
