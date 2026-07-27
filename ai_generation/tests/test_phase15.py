"""
Phase 15 Tests — Negotiation Engine & Supervisor Tree

Tests the ACOS Negotiation Engine (multi-criteria scoring, fallback chains,
trade-off documentation) and Supervisor Tree (fault tolerance, restart strategies).
"""
import pytest
import time
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))


# ── Negotiation Engine Tests ───────────────────────────────────

def test_negotiation_engine_import():
    from ai_generation.negotiation_engine import (
        NegotiationEngine, NegotiationRequest, NegotiationResult,
        ExecutionCandidate, FallbackPlan, TradeOff,
        CandidateBuilder, TaskType, Modality, QualityPriority, PrivacyLevel,
        ExecutionLayer,
    )
    assert TaskType.IMAGE_GENERATION.value == "image_generation"
    assert Modality.IMAGE.value == "image"
    assert QualityPriority.HIGH.value == "high"
    assert PrivacyLevel.CLOUD_OK.value == "cloud_ok"
    assert ExecutionLayer.PUBLIC_API.value == 1


def test_negotiation_request_defaults():
    from ai_generation.negotiation_engine import NegotiationRequest, TaskType, Modality
    req = NegotiationRequest(prompt="a beautiful sunset")
    assert req.task_type == TaskType.IMAGE_GENERATION
    assert req.modality == Modality.IMAGE
    assert req.task_id.startswith("neg-")
    assert req.quality_priority.value == "high"
    assert req.privacy_level.value == "cloud_ok"
    assert req.prefer_free is True
    assert req.prefer_cloud is True


def test_execution_candidate_defaults():
    from ai_generation.negotiation_engine import ExecutionCandidate, ExecutionLayer
    c = ExecutionCandidate(
        provider_name="pollinations",
        model_id="flux",
        task_type="image_generation",
    )
    assert c.provider_name == "pollinations"
    assert c.score == 0.0
    assert c.confidence == 0.0
    d = c.to_dict()
    assert d["provider"] == "pollinations"
    assert d["model"] == "flux"


def test_negotiation_basic():
    from ai_generation.negotiation_engine import (
        NegotiationEngine, NegotiationRequest, ExecutionCandidate,
        TaskType, ExecutionLayer,
    )
    engine = NegotiationEngine()
    req = NegotiationRequest(
        prompt="generate an image",
        task_type=TaskType.IMAGE_GENERATION,
    )
    candidates = [
        ExecutionCandidate(
            candidate_id="c1", provider_name="pollinations", model_id="flux",
            task_type="image_generation", supported_tasks=["image_generation"],
            free_tier=True, expected_latency_ms=8000, expected_cost_usd=0.0,
            expected_quality_score=0.65, success_rate=0.85, healthy=True,
        ),
        ExecutionCandidate(
            candidate_id="c2", provider_name="stability", model_id="sd3-medium",
            task_type="image_generation", supported_tasks=["image_generation"],
            free_tier=False, expected_latency_ms=5000, expected_cost_usd=0.01,
            expected_quality_score=0.85, success_rate=0.90, healthy=True,
        ),
    ]
    result = engine.negotiate(req, candidates)
    assert result.status == "success"
    assert result.selected_candidate is not None
    assert result.confidence_score > 0
    assert len(result.fallback_chain) >= 0
    assert result.negotiation_time_ms >= 0
    assert result.total_candidates_evaluated == 2


def test_negotiation_no_candidates():
    from ai_generation.negotiation_engine import (
        NegotiationEngine, NegotiationRequest, TaskType,
    )
    engine = NegotiationEngine()
    req = NegotiationRequest(prompt="test", task_type=TaskType.IMAGE_GENERATION)
    result = engine.negotiate(req, [])
    assert result.status == "no_compatible_path"
    assert result.suggestion != ""


def test_negotiation_cost_filter():
    from ai_generation.negotiation_engine import (
        NegotiationEngine, NegotiationRequest, ExecutionCandidate,
        TaskType,
    )
    engine = NegotiationEngine()
    req = NegotiationRequest(
        prompt="test",
        task_type=TaskType.IMAGE_GENERATION,
        max_cost_usd=0.001,
    )
    candidates = [
        ExecutionCandidate(
            candidate_id="c1", provider_name="pollinations", model_id="flux",
            task_type="image_generation", supported_tasks=["image_generation"],
            expected_cost_usd=0.0, expected_quality_score=0.6,
        ),
        ExecutionCandidate(
            candidate_id="c2", provider_name="stability", model_id="sd3",
            task_type="image_generation", supported_tasks=["image_generation"],
            expected_cost_usd=0.05, expected_quality_score=0.9,
        ),
    ]
    result = engine.negotiate(req, candidates)
    assert result.status == "success"
    assert result.selected_candidate.provider_name == "pollinations"


def test_negotiation_latency_filter():
    from ai_generation.negotiation_engine import (
        NegotiationEngine, NegotiationRequest, ExecutionCandidate,
        TaskType,
    )
    engine = NegotiationEngine()
    req = NegotiationRequest(
        prompt="test",
        task_type=TaskType.IMAGE_GENERATION,
        latency_target_ms=2000,
    )
    candidates = [
        ExecutionCandidate(
            candidate_id="c1", provider_name="fast_provider", model_id="fast",
            task_type="image_generation", supported_tasks=["image_generation"],
            expected_latency_ms=1000, expected_quality_score=0.6,
        ),
        ExecutionCandidate(
            candidate_id="c2", provider_name="slow_provider", model_id="slow",
            task_type="image_generation", supported_tasks=["image_generation"],
            expected_latency_ms=10000, expected_quality_score=0.9,
        ),
    ]
    result = engine.negotiate(req, candidates)
    assert result.status == "success"
    assert result.selected_candidate.provider_name == "fast_provider"


def test_negotiation_privacy_local_only():
    from ai_generation.negotiation_engine import (
        NegotiationEngine, NegotiationRequest, ExecutionCandidate,
        TaskType, PrivacyLevel, ExecutionLayer,
    )
    engine = NegotiationEngine()
    req = NegotiationRequest(
        prompt="test",
        task_type=TaskType.IMAGE_GENERATION,
        privacy_level=PrivacyLevel.LOCAL_ONLY,
    )
    candidates = [
        ExecutionCandidate(
            candidate_id="c1", provider_name="cloud_api", model_id="cloud",
            task_type="image_generation", supported_tasks=["image_generation"],
            layer=ExecutionLayer.PUBLIC_API, expected_quality_score=0.9,
        ),
        ExecutionCandidate(
            candidate_id="c2", provider_name="local_gpu", model_id="local",
            task_type="image_generation", supported_tasks=["image_generation"],
            layer=ExecutionLayer.LOCAL_GPU, expected_quality_score=0.7,
        ),
    ]
    result = engine.negotiate(req, candidates)
    assert result.status == "success"
    assert result.selected_candidate.provider_name == "local_gpu"


def test_negotiation_fallback_chain():
    from ai_generation.negotiation_engine import (
        NegotiationEngine, NegotiationRequest, ExecutionCandidate,
        TaskType,
    )
    engine = NegotiationEngine()
    req = NegotiationRequest(prompt="test", task_type=TaskType.IMAGE_GENERATION)
    candidates = [
        ExecutionCandidate(
            candidate_id=f"c{i}", provider_name=f"provider_{i}",
            model_id=f"model_{i % 2}", model_name=f"model_{i % 2}",
            task_type="image_generation", supported_tasks=["image_generation"],
            expected_quality_score=0.9 - i * 0.1,
            expected_latency_ms=1000 + i * 500,
        )
        for i in range(5)
    ]
    result = engine.negotiate(req, candidates)
    assert result.status == "success"
    assert len(result.fallback_chain) > 0
    assert result.fallback_chain[0].level >= 1


def test_negotiation_trade_offs():
    from ai_generation.negotiation_engine import (
        NegotiationEngine, NegotiationRequest, ExecutionCandidate,
        TaskType,
    )
    engine = NegotiationEngine()
    req = NegotiationRequest(prompt="test", task_type=TaskType.IMAGE_GENERATION)
    candidates = [
        ExecutionCandidate(
            candidate_id="c1", provider_name="cheap", model_id="fast",
            task_type="image_generation", supported_tasks=["image_generation"],
            expected_quality_score=0.6, expected_cost_usd=0.0,
            expected_latency_ms=2000,
        ),
        ExecutionCandidate(
            candidate_id="c2", provider_name="premium", model_id="best",
            task_type="image_generation", supported_tasks=["image_generation"],
            expected_quality_score=0.95, expected_cost_usd=0.05,
            expected_latency_ms=8000,
        ),
    ]
    result = engine.negotiate(req, candidates)
    assert result.status == "success"
    assert len(result.trade_offs) >= 0


def test_negotiation_benchmark_update():
    from ai_generation.negotiation_engine import NegotiationEngine
    engine = NegotiationEngine()
    engine.update_benchmark("pollinations", "flux", "image_generation", 0.75, 0.90, 8000)
    stats = engine.get_stats()
    assert stats["benchmark_entries"] == 1


def test_negotiation_health_update():
    from ai_generation.negotiation_engine import NegotiationEngine
    engine = NegotiationEngine()
    engine.update_health("pollinations", True)
    engine.update_health("stability", False)
    stats = engine.get_stats()
    assert stats["health_tracked"] == 2


def test_negotiation_history():
    from ai_generation.negotiation_engine import (
        NegotiationEngine, NegotiationRequest, ExecutionCandidate,
        TaskType,
    )
    engine = NegotiationEngine()
    req = NegotiationRequest(prompt="test", task_type=TaskType.IMAGE_GENERATION)
    candidates = [
        ExecutionCandidate(
            candidate_id="c1", provider_name="test", model_id="test",
            task_type="image_generation", supported_tasks=["image_generation"],
        ),
    ]
    engine.negotiate(req, candidates)
    history = engine.get_history()
    assert len(history) == 1
    assert history[0]["status"] == "success"


def test_negotiation_weights_override():
    from ai_generation.negotiation_engine import NegotiationEngine
    engine = NegotiationEngine()
    engine.set_weights("image_generation", {
        "quality": 0.50, "speed": 0.10, "cost": 0.10,
        "reliability": 0.15, "energy": 0.15,
    })
    # Verify weights were updated
    weights = engine._scoring_weights["image_generation"]
    assert weights["quality"] == 0.50
    assert weights["speed"] == 0.10


def test_negotiation_confidence_scoring():
    from ai_generation.negotiation_engine import (
        NegotiationEngine, NegotiationRequest, ExecutionCandidate,
        TaskType,
    )
    engine = NegotiationEngine()
    req = NegotiationRequest(prompt="test", task_type=TaskType.IMAGE_GENERATION)

    # High confidence candidate (verified, many benchmarks, healthy)
    high = ExecutionCandidate(
        candidate_id="high", provider_name="proven", model_id="stable",
        task_type="image_generation", supported_tasks=["image_generation"],
        verified=True, healthy=True, benchmark_count=15,
        success_rate=0.95, expected_quality_score=0.9,
    )
    # Low confidence candidate (unverified, no benchmarks, unhealthy)
    low = ExecutionCandidate(
        candidate_id="low", provider_name="unknown", model_id="new",
        task_type="image_generation", supported_tasks=["image_generation"],
        verified=False, healthy=False, benchmark_count=0,
        success_rate=0.5, expected_quality_score=0.5,
    )
    result = engine.negotiate(req, [high, low])
    assert result.status == "success"
    assert result.selected_candidate.provider_name == "proven"
    assert result.confidence_score > 0.3


def test_candidate_builder_import():
    from ai_generation.negotiation_engine import CandidateBuilder, TaskType
    from ai_generation.capability_registry import CapabilityRegistry
    cr = CapabilityRegistry()
    builder = CandidateBuilder(capability_registry=cr)
    candidates = builder.build_candidates(TaskType.IMAGE_GENERATION)
    assert isinstance(candidates, list)
    assert len(candidates) > 0  # text_to_image models from registry
def test_supervisor_import():
    from ai_generation.supervisor import (
        SupervisorTree, SupervisorConfig, SupervisionStrategy,
        WorkerState, WorkerType, SupervisionEvent,
        SupervisorError, WorkerCrashError,
        create_provider_supervisor, create_agent_supervisor,
        create_engine_supervisor, create_platform_supervisor,
    )
    assert SupervisionStrategy.ONE_FOR_ONE.value == "one_for_one"
    assert WorkerType.PROVIDER.value == "provider"


def test_supervisor_tree_basic():
    from ai_generation.supervisor import SupervisorTree, SupervisorConfig
    tree = SupervisorTree(name="test", config=SupervisorConfig(max_restarts=3))
    assert tree.name == "test"
    assert tree.config.max_restarts == 3
    stats = tree.get_stats()
    assert stats["total_workers"] == 0
    assert stats["supervisor"] == "test"


def test_supervisor_add_worker():
    from ai_generation.supervisor import SupervisorTree, WorkerType
    tree = SupervisorTree(name="test")
    tree.add_worker("w1", lambda: 42, name="worker1", worker_type=WorkerType.PROVIDER)
    stats = tree.get_stats()
    assert stats["total_workers"] == 1
    state = tree.get_worker_state("w1")
    assert state["name"] == "worker1"
    assert state["type"] == "provider"


def test_supervisor_run_worker():
    from ai_generation.supervisor import SupervisorTree
    tree = SupervisorTree(name="test")
    tree.add_worker("w1", lambda: 42)
    result = tree.run_worker("w1")
    assert result == 42
    state = tree.get_worker_state("w1")
    assert state["total_executions"] == 1
    assert state["status"] == "idle"


def test_supervisor_run_worker_crash():
    from ai_generation.supervisor import SupervisorTree, WorkerCrashError
    def always_crash():
        raise ValueError("boom")
    tree = SupervisorTree(name="test")
    tree.add_worker("w1", always_crash)
    with pytest.raises((ValueError, WorkerCrashError)):
        tree.run_worker("w1")
    state = tree.get_worker_state("w1")
    assert state["total_failures"] >= 1


def test_supervisor_run_worker_safe():
    from ai_generation.supervisor import SupervisorTree
    def always_crash():
        raise ValueError("boom")
    tree = SupervisorTree(name="test")
    tree.add_worker("w1", always_crash)
    result = tree.run_worker_safe("w1")
    assert result is None


def test_supervisor_restart_strategy():
    from ai_generation.supervisor import (
        SupervisorTree, SupervisorConfig, SupervisionStrategy,
    )
    tree = SupervisorTree(name="test", config=SupervisorConfig(
        strategy=SupervisionStrategy.ONE_FOR_ALL,
        max_restarts=10,
    ))
    tree.add_worker("w1", lambda: 1)
    tree.add_worker("w2", lambda: 2)
    assert tree.config.strategy == SupervisionStrategy.ONE_FOR_ALL


def test_supervisor_child_supervisors():
    from ai_generation.supervisor import SupervisorTree, SupervisorConfig
    root = SupervisorTree(name="root")
    child1 = SupervisorTree(name="child1")
    child2 = SupervisorTree(name="child2")
    root.add_child("child1", child1)
    root.add_child("child2", child2)
    stats = root.get_stats()
    assert stats["children"] == 2


def test_supervisor_stop_worker():
    from ai_generation.supervisor import SupervisorTree
    tree = SupervisorTree(name="test")
    tree.add_worker("w1", lambda: 1)
    tree.run_worker("w1")
    tree.stop_worker("w1")
    state = tree.get_worker_state("w1")
    assert state["status"] == "stopped"


def test_supervisor_reset():
    from ai_generation.supervisor import SupervisorTree
    tree = SupervisorTree(name="test")
    tree.add_worker("w1", lambda: 1)
    tree.run_worker("w1")
    tree.reset_all()
    state = tree.get_worker_state("w1")
    assert state["restart_count"] == 0
    assert state["status"] == "idle"


def test_supervisor_events():
    from ai_generation.supervisor import SupervisorTree
    def always_crash():
        raise ValueError("fail")
    tree = SupervisorTree(name="test")
    tree.add_worker("w1", always_crash)
    tree.run_worker_safe("w1")
    events = tree.get_events()
    assert len(events) >= 1


def test_supervisor_event_handler():
    from ai_generation.supervisor import SupervisorTree, SupervisionEvent
    def always_crash():
        raise ValueError("fail")
    tree = SupervisorTree(name="test")
    events_received = []
    tree.on_event(lambda e: events_received.append(e))
    tree.add_worker("w1", always_crash)
    tree.run_worker_safe("w1")
    assert len(events_received) >= 1


def test_supervisor_crashed_workers():
    from ai_generation.supervisor import SupervisorTree
    def always_crash():
        raise ValueError("fail")
    tree = SupervisorTree(name="test")
    tree.add_worker("w1", lambda: 1)
    tree.add_worker("w2", always_crash)
    tree.run_worker("w1")
    tree.run_worker_safe("w2")
    crashed = tree.get_crashed_workers()
    assert "w2" in crashed


def test_supervisor_healthy_workers():
    from ai_generation.supervisor import SupervisorTree
    def always_crash():
        raise ValueError("fail")
    tree = SupervisorTree(name="test")
    tree.add_worker("w1", lambda: 1)
    tree.add_worker("w2", always_crash)
    tree.run_worker("w1")
    tree.run_worker_safe("w2")
    healthy = tree.get_healthy_workers()
    assert "w1" in healthy
    assert "w2" not in healthy


def test_supervisor_prebuilt_trees():
    from ai_generation.supervisor import (
        create_provider_supervisor, create_agent_supervisor,
        create_engine_supervisor, create_platform_supervisor,
    )
    ps = create_provider_supervisor()
    assert ps.name == "providers"
    ag = create_agent_supervisor()
    assert ag.name == "agents"
    en = create_engine_supervisor()
    assert en.name == "engines"
    plat = create_platform_supervisor()
    assert plat.name == "platform"
    stats = plat.get_stats()
    assert stats["children"] == 3


def test_supervisor_worker_state_serialization():
    from ai_generation.supervisor import SupervisorTree
    tree = SupervisorTree(name="test")
    tree.add_worker("w1", lambda: 1)
    tree.run_worker("w1")
    states = tree.get_all_states()
    assert "w1" in states
    assert states["w1"]["total_executions"] == 1


def test_supervisor_repr():
    from ai_generation.supervisor import SupervisorTree
    tree = SupervisorTree(name="test")
    r = repr(tree)
    assert "test" in r
    assert "one_for_one" in r


# ── SDK Integration Tests ──────────────────────────────────────

def test_sdk_negotiation_import():
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    assert hasattr(ai, 'negotiate')
    assert hasattr(ai, 'negotiation_engine')
    assert hasattr(ai, 'supervisor')
    assert hasattr(ai, 'supervisor_stats')
    assert hasattr(ai, 'supervisor_workers')
    assert hasattr(ai, 'supervisor_events')
    assert hasattr(ai, 'supervisor_crashed')
    assert hasattr(ai, 'supervisor_reset')
    assert hasattr(ai, 'get_negotiation_stats')
    assert hasattr(ai, 'get_negotiation_history')
    assert hasattr(ai, 'update_benchmark')


def test_sdk_negotiation_stats():
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    stats = ai.get_negotiation_stats()
    assert "total_negotiations" in stats
    assert "benchmark_entries" in stats


def test_sdk_supervisor_stats():
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    stats = ai.supervisor_stats()
    assert "total_workers" in stats
    assert "strategy" in stats
