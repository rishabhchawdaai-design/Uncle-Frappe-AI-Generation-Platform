"""Tests for orchestration.py — OrchestrationPipeline, DomainReviewAgent, KnowledgeBaseContext, RevisionLoop."""

import pytest
from ai_generation.orchestration import (
    PipelineStage, StageResult, StageOutput,
    AgentDomain, AGENT_PROMPTS,
    KnowledgeBaseContext, KBEntry,
    RevisionLoop, RevisionRound,
    OrchestrationPipeline, PipelineConfig,
)


# ── StageOutput Tests ──────────────────────────────────────────

class TestStageOutput:
    def test_create(self):
        out = StageOutput(stage="qa", result="pass", summary="All good")
        assert out.stage == "qa"
        assert out.result == "pass"
        assert out.timestamp != ""

    def test_to_dict(self):
        out = StageOutput(stage="review", result="fail", summary="Issues found",
                         findings=[{"issue": "test"}], metrics={"score": 85})
        d = out.to_dict()
        assert d["stage"] == "review"
        assert d["findings"] == [{"issue": "test"}]
        assert d["metrics"]["score"] == 85


# ── AgentDomain Tests ──────────────────────────────────────────

class TestAgentDomain:
    def test_all_domains_have_prompts(self):
        for domain in AgentDomain:
            assert domain.value in AGENT_PROMPTS

    def test_agent_prompt_structure(self):
        for domain, info in AGENT_PROMPTS.items():
            assert "name" in info
            assert "description" in info
            assert "review_areas" in info
            assert len(info["review_areas"]) >= 3


# ── KnowledgeBaseContext Tests ─────────────────────────────────

class TestKnowledgeBaseContext:
    def test_add_and_retrieve(self):
        kb = KnowledgeBaseContext()
        kb.add_entry("auth", "Authentication uses JWT tokens", source="docs/auth.md")
        results = kb.retrieve("authentication JWT")
        assert len(results) >= 1
        assert results[0].key == "auth"

    def test_retrieve_ranking(self):
        kb = KnowledgeBaseContext()
        kb.add_entry("a", "authentication authorization security")
        kb.add_entry("b", "authentication login")
        results = kb.retrieve("authentication security")
        assert results[0].key == "a"

    def test_empty_retrieve(self):
        kb = KnowledgeBaseContext()
        results = kb.retrieve("xyz123nonexistent")
        assert len(results) == 0

    def test_stats(self):
        kb = KnowledgeBaseContext()
        kb.add_entry("a", "test content", source="doc.md")
        stats = kb.get_stats()
        assert stats["total_entries"] == 1
        assert "doc.md" in stats["sources"]

    def test_relevance_score(self):
        kb = KnowledgeBaseContext()
        kb.add_entry("a", "security authentication")
        results = kb.retrieve("security authentication")
        assert results[0].relevance > 0


# ── RevisionLoop Tests ─────────────────────────────────────────

class TestRevisionLoop:
    def test_should_continue_on_changes_requested(self):
        loop = RevisionLoop(max_rounds=3)
        qa = StageOutput(stage="qa", result="pass", summary="ok")
        review = StageOutput(stage="review", result="changes_requested", summary="fix this")
        assert loop.should_continue(qa, review) is True

    def test_should_continue_on_qa_fail(self):
        loop = RevisionLoop(max_rounds=3)
        qa = StageOutput(stage="qa", result="fail", summary="tests failed")
        review = StageOutput(stage="review", result="pass", summary="ok")
        assert loop.should_continue(qa, review) is True

    def test_should_not_continue_when_pass(self):
        loop = RevisionLoop(max_rounds=3)
        qa = StageOutput(stage="qa", result="pass", summary="ok")
        review = StageOutput(stage="review", result="pass", summary="ok")
        assert loop.should_continue(qa, review) is False

    def test_should_not_continue_when_max_rounds(self):
        loop = RevisionLoop(max_rounds=2)
        qa = StageOutput(stage="qa", result="fail", summary="fail")
        review = StageOutput(stage="review", result="changes_requested", summary="fix")
        for i in range(2):
            loop.record_round(i + 1, qa, review)
        assert loop.should_continue(qa, review) is False

    def test_record_round(self):
        loop = RevisionLoop(max_rounds=3)
        qa = StageOutput(stage="qa", result="pass", summary="ok")
        review = StageOutput(stage="review", result="pass", summary="ok")
        loop.record_round(1, qa, review, ship=True)
        assert len(loop.get_rounds()) == 1
        assert loop.get_rounds()[0].decided_to_ship is True

    def test_stats(self):
        loop = RevisionLoop(max_rounds=3)
        qa = StageOutput(stage="qa", result="pass", summary="ok")
        review = StageOutput(stage="review", result="pass", summary="ok")
        loop.record_round(1, qa, review, ship=True)
        stats = loop.get_stats()
        assert stats["total_rounds"] == 1
        assert stats["shipped"] is True


# ── OrchestrationPipeline Tests ────────────────────────────────

class TestOrchestrationPipeline:
    def test_plan_agents(self):
        pipeline = OrchestrationPipeline()
        agents = pipeline.plan_agents("Implement JWT authentication with rate limiting")
        assert len(agents) >= 2
        domains = [a["domain"] for a in agents]
        assert "security" in domains

    def test_plan_agents_performance(self):
        pipeline = OrchestrationPipeline()
        agents = pipeline.plan_agents("Optimize database queries and add caching")
        domains = [a["domain"] for a in agents]
        assert "performance" in domains

    def test_run_intent_stage(self):
        pipeline = OrchestrationPipeline()
        output = pipeline.run_stage("intent", "x = 1", {"description": "security fix"})
        assert output.result == StageResult.PASS.value
        assert output.metrics["agents_selected"] >= 1

    def test_run_qa_stage_clean(self):
        pipeline = OrchestrationPipeline()
        output = pipeline.run_stage("qa", "import logging\nlogger = logging.getLogger(__name__)\n")
        assert output.result == StageResult.PASS.value

    def test_run_qa_stage_with_issues(self):
        pipeline = OrchestrationPipeline()
        output = pipeline.run_stage("qa", "result = eval(input())")
        assert output.result == StageResult.FAIL.value
        assert output.metrics["critical"] > 0

    def test_run_review_stage(self):
        pipeline = OrchestrationPipeline()
        output = pipeline.run_stage("review", "x = 1")
        assert output.result in (StageResult.PASS.value, StageResult.CHANGES_REQUESTED.value)

    def test_run_security_stage_clean(self):
        pipeline = OrchestrationPipeline()
        output = pipeline.run_stage("security", "x = 1")
        assert output.result == StageResult.PASS.value

    def test_run_security_stage_with_secrets(self):
        pipeline = OrchestrationPipeline()
        output = pipeline.run_stage("security", "API_KEY = 'sk-1234567890abcdefghijklmnopqrst'")
        assert output.result == StageResult.FAIL.value

    def test_run_full_pipeline(self):
        pipeline = OrchestrationPipeline()
        result = pipeline.run_full_pipeline("import logging\nlogger = logging.getLogger(__name__)\n", "clean.py")
        assert "stages" in result
        assert result["total_stages"] >= 3  # stops at QA due to critical issues
        assert "elapsed_seconds" in result

    def test_run_full_pipeline_with_secret(self):
        pipeline = OrchestrationPipeline()
        result = pipeline.run_full_pipeline("API_KEY = 'sk-1234567890abcdefghijklmnopqrst'", "bad.py")
        assert result["total_findings"] > 0

    def test_knowledge_base_integration(self):
        pipeline = OrchestrationPipeline()
        pipeline.knowledge_base.add_entry("auth", "JWT authentication", source="docs")
        result = pipeline.run_full_pipeline("x = 1", description="implement auth")
        assert "stages" in result

    def test_pipeline_stats(self):
        pipeline = OrchestrationPipeline()
        pipeline.run_full_pipeline("x = 1")
        stats = pipeline.get_stats()
        assert stats["total_pipelines_run"] == 1

    def test_run_unknown_stage(self):
        pipeline = OrchestrationPipeline()
        output = pipeline.run_stage("nonexistent", "x = 1")
        assert output.result == StageResult.SKIPPED.value

    def test_fast_path_config(self):
        config = PipelineConfig(enable_fast_path=True, fast_path_max_files=1, fast_path_max_lines=10)
        pipeline = OrchestrationPipeline(config)
        assert pipeline.config.enable_fast_path is True

    def test_revision_loop_integration(self):
        pipeline = OrchestrationPipeline()
        qa = StageOutput(stage="qa", result="pass", summary="ok")
        review = StageOutput(stage="review", result="pass", summary="ok")
        pipeline._revision_loop.record_round(1, qa, review, ship=True)
        stats = pipeline.get_stats()
        assert stats["revision_stats"]["total_rounds"] == 1


# ── Integration Tests ──────────────────────────────────────────

class TestOrchestrationIntegration:
    def test_end_to_end_pipeline(self):
        """Test complete pipeline with code analysis integration."""
        code = """
import os
# TODO: add rate limiting
API_KEY = 'sk-1234567890abcdefghijklmnopqrst'
result = eval(input())
"""
        pipeline = OrchestrationPipeline()
        pipeline.knowledge_base.add_entry("security", "Use environment variables for secrets")
        pipeline.knowledge_base.add_entry("auth", "JWT token authentication")
        result = pipeline.run_full_pipeline(code, "bad.py", "security implementation")
        assert result["total_stages"] >= 3  # stops at QA due to critical issues
        assert result["total_findings"] > 0

    def test_agent_selection_varies_by_task(self):
        pipeline = OrchestrationPipeline()
        security_agents = pipeline.plan_agents("Fix SQL injection vulnerability")
        perf_agents = pipeline.plan_agents("Optimize database query performance")
        security_domains = [a["domain"] for a in security_agents]
        perf_domains = [a["domain"] for a in perf_agents]
        assert "security" in security_domains
        assert "performance" in perf_domains
