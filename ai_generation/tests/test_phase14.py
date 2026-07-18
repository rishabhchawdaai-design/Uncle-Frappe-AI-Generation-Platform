"""
Phase 14 Tests — AIG-OS Autonomous Agent System
Comprehensive tests for all 10 agents, knowledge graph, dynamic adapters,
benchmark lab, SDK extensions, and MCP tools.
"""
import pytest


# ── Base Agent Tests ─────────────────────────────────────────────

def test_base_agent_import():
    from ai_generation.agents.base_agent import BaseAgent, AgentStatus, AgentTask, AgentResult, AgentPriority
    assert AgentStatus.IDLE.value == "idle"
    assert AgentPriority.LOW.value == 1

def test_base_agent_lifecycle():
    from ai_generation.agents.base_agent import BaseAgent, AgentStatus, AgentTask, AgentResult
    agent = BaseAgent()
    assert agent.status == AgentStatus.IDLE
    agent.start()
    assert agent.status == AgentStatus.IDLE
    agent.pause()
    assert agent.status == AgentStatus.PAUSED
    agent.resume()
    assert agent.status == AgentStatus.IDLE
    agent.stop()
    assert agent.status == AgentStatus.STOPPED

def test_base_agent_task():
    from ai_generation.agents.base_agent import AgentTask, AgentResult
    task = AgentTask(task_type="test", payload={"key": "value"})
    assert task.task_type == "test"
    assert task.payload["key"] == "value"
    assert task.task_id  # auto-generated
    result = AgentResult(success=True, data={"ok": True})
    d = result.to_dict()
    assert d["success"] is True
    assert d["data"]["ok"] is True

def test_base_agent_stats():
    from ai_generation.agents.base_agent import BaseAgent
    agent = BaseAgent()
    stats = agent.get_stats()
    assert stats["agent_name"] == "base"
    assert stats["status"] == "idle"
    assert stats["total_tasks"] == 0

# ── Agent Registry Tests ─────────────────────────────────────────

def test_agent_registry_import():
    from ai_generation.agents.agent_registry import AgentRegistry
    reg = AgentRegistry()
    assert reg.list_agents() == []

def test_agent_registry_create():
    from ai_generation.agents.agent_registry import AgentRegistry
    from ai_generation.agents.base_agent import BaseAgent
    reg = AgentRegistry()
    reg.register_agent_class("test", BaseAgent)
    agent = reg.create_agent("test")
    assert agent.agent_name == "base"
    assert len(reg.list_agents()) == 1

def test_agent_registry_stats():
    from ai_generation.agents.agent_registry import AgentRegistry
    from ai_generation.agents.base_agent import BaseAgent
    reg = AgentRegistry()
    reg.register_agent_class("test", BaseAgent)
    reg.create_agent("test")
    stats = reg.get_stats()
    assert stats["total_agents"] == 1

# ── Orchestrator Tests ──────────────────────────────────────────

def test_orchestrator_import():
    from ai_generation.agents.agent_registry import AgentOrchestrator
    orch = AgentOrchestrator()
    assert not orch._initialized

def test_orchestrator_initialize():
    from ai_generation.agents.agent_registry import AgentOrchestrator
    orch = AgentOrchestrator()
    orch.initialize()
    assert orch._initialized
    assert len(orch.registry._agents) == 10

def test_orchestrator_stats():
    from ai_generation.agents.agent_registry import AgentOrchestrator
    orch = AgentOrchestrator()
    orch.initialize()
    stats = orch.get_stats()
    assert stats["total_agents"] == 10

def test_orchestrator_status():
    from ai_generation.agents.agent_registry import AgentOrchestrator
    orch = AgentOrchestrator()
    orch.initialize()
    status = orch.get_status()
    assert status["initialized"] is True
    assert status["registry"]["total_agents"] == 10

# ── Research Agent Tests ─────────────────────────────────────────

def test_research_agent_import():
    from ai_generation.agents.research_agent import ResearchAgent
    agent = ResearchAgent()
    assert agent.agent_name == "research"

def test_research_agent_get_providers():
    from ai_generation.agents.research_agent import ResearchAgent
    from ai_generation.agents.base_agent import AgentTask
    agent = ResearchAgent()
    task = AgentTask(task_type="get_providers")
    result = agent.execute(task)
    assert result.success
    assert result.data["total"] >= 10

def test_research_agent_get_sources():
    from ai_generation.agents.research_agent import ResearchAgent
    from ai_generation.agents.base_agent import AgentTask
    agent = ResearchAgent()
    task = AgentTask(task_type="get_sources")
    result = agent.execute(task)
    assert result.success
    assert result.data["total"] >= 5

def test_research_agent_add_discovery():
    from ai_generation.agents.research_agent import ResearchAgent
    from ai_generation.agents.base_agent import AgentTask
    agent = ResearchAgent()
    task = AgentTask(task_type="add_discovery", payload={"name": "test_provider", "type": "image"})
    result = agent.execute(task)
    assert result.success
    assert result.data["total_discoveries"] >= 1

def test_research_agent_stats():
    from ai_generation.agents.research_agent import ResearchAgent
    agent = ResearchAgent()
    stats = agent.get_stats()
    assert stats["total_providers"] >= 10
    assert stats["research_sources"] >= 5

# ── Discovery Agent Tests ────────────────────────────────────────

def test_discovery_agent_import():
    from ai_generation.agents.discovery_agent import DiscoveryAgent
    agent = DiscoveryAgent()
    assert agent.agent_name == "discovery"

def test_discovery_agent_get_endpoints():
    from ai_generation.agents.discovery_agent import DiscoveryAgent
    from ai_generation.agents.base_agent import AgentTask
    agent = DiscoveryAgent()
    task = AgentTask(task_type="get_endpoints")
    result = agent.execute(task)
    assert result.success
    assert result.data["total"] >= 9

def test_discovery_agent_add_endpoint():
    from ai_generation.agents.discovery_agent import DiscoveryAgent
    from ai_generation.agents.base_agent import AgentTask
    agent = DiscoveryAgent()
    task = AgentTask(task_type="add_endpoint", payload={"name": "test_ep", "url": "http://test.com", "tasks": ["text_to_image"]})
    result = agent.execute(task)
    assert result.success
    assert result.data["endpoint"]["name"] == "test_ep"

def test_discovery_agent_search():
    from ai_generation.agents.discovery_agent import DiscoveryAgent
    from ai_generation.agents.base_agent import AgentTask
    agent = DiscoveryAgent()
    task = AgentTask(task_type="search_endpoints", payload={"query": "pollinations"})
    result = agent.execute(task)
    assert result.success
    assert result.data["total"] >= 1

def test_discovery_agent_stats():
    from ai_generation.agents.discovery_agent import DiscoveryAgent
    agent = DiscoveryAgent()
    stats = agent.get_stats()
    assert stats["total_endpoints"] >= 9

# ── Integration Agent Tests ──────────────────────────────────────

def test_integration_agent_import():
    from ai_generation.agents.integration_agent import IntegrationAgent
    agent = IntegrationAgent()
    assert agent.agent_name == "integration"

def test_integration_agent_integrate():
    from ai_generation.agents.integration_agent import IntegrationAgent
    from ai_generation.agents.base_agent import AgentTask
    agent = IntegrationAgent()
    task = AgentTask(task_type="integrate_provider", payload={
        "provider": "test_provider", "schema_type": "json_schema",
        "schema_data": {"properties": {"generate": {"type": "string", "description": "Generate image"}}},
    })
    result = agent.execute(task)
    assert result.success
    assert result.data["status"] == "integrated"

def test_integration_agent_list():
    from ai_generation.agents.integration_agent import IntegrationAgent
    from ai_generation.agents.base_agent import AgentTask
    agent = IntegrationAgent()
    task = AgentTask(task_type="list_integrations")
    result = agent.execute(task)
    assert result.success

def test_integration_agent_stats():
    from ai_generation.agents.integration_agent import IntegrationAgent
    agent = IntegrationAgent()
    stats = agent.get_stats()
    assert "total_integrations" in stats

# ── Verification Agent Tests ─────────────────────────────────────

def test_verification_agent_import():
    from ai_generation.agents.verification_agent import VerificationAgent
    agent = VerificationAgent()
    assert agent.agent_name == "verification"

def test_verification_agent_verify():
    from ai_generation.agents.verification_agent import VerificationAgent
    from ai_generation.agents.base_agent import AgentTask
    agent = VerificationAgent()
    task = AgentTask(task_type="verify_provider", payload={"provider": "test", "capabilities": ["text_to_image"]})
    result = agent.execute(task)
    assert result.success
    assert result.data["score"] >= 0.5

def test_verification_agent_promote():
    from ai_generation.agents.verification_agent import VerificationAgent
    from ai_generation.agents.base_agent import AgentTask
    agent = VerificationAgent()
    verify_task = AgentTask(task_type="verify_provider", payload={"provider": "good_provider", "capabilities": ["text_to_image"]})
    agent.execute(verify_task)
    promote_task = AgentTask(task_type="promote_provider", payload={"provider": "good_provider"})
    result = agent.execute(promote_task)
    assert result.success
    assert result.data["promoted"] is True

def test_verification_agent_list():
    from ai_generation.agents.verification_agent import VerificationAgent
    from ai_generation.agents.base_agent import AgentTask
    agent = VerificationAgent()
    verify_task = AgentTask(task_type="verify_provider", payload={"provider": "test", "capabilities": ["text_to_image"]})
    agent.execute(verify_task)
    list_task = AgentTask(task_type="list_verified")
    result = agent.execute(list_task)
    assert result.success
    assert "test" in result.data["providers"]

def test_verification_agent_stats():
    from ai_generation.agents.verification_agent import VerificationAgent
    agent = VerificationAgent()
    stats = agent.get_stats()
    assert stats["total_verified"] == 0

# ── Benchmark Agent Tests ────────────────────────────────────────

def test_benchmark_agent_import():
    from ai_generation.agents.benchmark_agent import BenchmarkAgent
    agent = BenchmarkAgent()
    assert agent.agent_name == "benchmark"

def test_benchmark_agent_benchmark():
    from ai_generation.agents.benchmark_agent import BenchmarkAgent
    from ai_generation.agents.base_agent import AgentTask
    agent = BenchmarkAgent()
    task = AgentTask(task_type="benchmark_provider", payload={"provider": "test", "categories": ["realism"]})
    result = agent.execute(task)
    assert result.success
    assert result.data["composite_score"] >= 0

def test_benchmark_agent_leaderboard():
    from ai_generation.agents.benchmark_agent import BenchmarkAgent
    from ai_generation.agents.base_agent import AgentTask
    agent = BenchmarkAgent()
    task = AgentTask(task_type="benchmark_provider", payload={"provider": "test", "categories": ["realism"]})
    agent.execute(task)
    lb_task = AgentTask(task_type="get_leaderboard")
    result = agent.execute(lb_task)
    assert result.success
    assert len(result.data["leaderboard"]) >= 1

def test_benchmark_agent_stats():
    from ai_generation.agents.benchmark_agent import BenchmarkAgent
    agent = BenchmarkAgent()
    stats = agent.get_stats()
    assert stats["total_benchmarked"] == 0

# ── Execution Agent Tests ────────────────────────────────────────

def test_execution_agent_import():
    from ai_generation.agents.execution_agent_p14 import ExecutionAgentV2
    agent = ExecutionAgentV2()
    assert agent.agent_name == "execution"

def test_execution_agent_execute():
    from ai_generation.agents.execution_agent_p14 import ExecutionAgentV2
    from ai_generation.agents.base_agent import AgentTask
    agent = ExecutionAgentV2()
    task = AgentTask(task_type="execute_generation", payload={
        "prompt": "test prompt", "task_type": "text_to_image", "providers": ["test_provider"],
    })
    result = agent.execute(task)
    assert result.success
    assert result.data["provider"] == "test_provider"

def test_execution_agent_rank():
    from ai_generation.agents.execution_agent_p14 import ExecutionAgentV2
    from ai_generation.agents.base_agent import AgentTask
    agent = ExecutionAgentV2()
    task = AgentTask(task_type="rank_providers", payload={"task_type": "text_to_image", "providers": ["a", "b"], "scores": {"a": 0.9, "b": 0.7}})
    result = agent.execute(task)
    assert result.success
    assert result.data["rankings"][0]["provider"] == "a"

def test_execution_agent_stats():
    from ai_generation.agents.execution_agent_p14 import ExecutionAgentV2
    agent = ExecutionAgentV2()
    stats = agent.get_stats()
    assert stats["total_executions"] == 0

# ── Recovery Agent Tests ─────────────────────────────────────────

def test_recovery_agent_import():
    from ai_generation.agents.recovery_agent import RecoveryAgent
    agent = RecoveryAgent()
    assert agent.agent_name == "recovery"

def test_recovery_agent_report_failure():
    from ai_generation.agents.recovery_agent import RecoveryAgent
    from ai_generation.agents.base_agent import AgentTask
    agent = RecoveryAgent()
    task = AgentTask(task_type="report_failure", payload={"provider": "bad", "error": "timeout"})
    result = agent.execute(task)
    assert result.success
    assert result.data["provider"] == "bad"

def test_recovery_agent_blacklist():
    from ai_generation.agents.recovery_agent import RecoveryAgent
    from ai_generation.agents.base_agent import AgentTask
    agent = RecoveryAgent()
    task = AgentTask(task_type="blacklist_provider", payload={"provider": "bad", "reason": "test"})
    result = agent.execute(task)
    assert result.success
    assert result.data["blacklisted"] is True

def test_recovery_agent_health_check():
    from ai_generation.agents.recovery_agent import RecoveryAgent
    from ai_generation.agents.base_agent import AgentTask
    agent = RecoveryAgent()
    task = AgentTask(task_type="check_health", payload={"provider": "good"})
    result = agent.execute(task)
    assert result.success
    assert result.data["healthy"] is True

def test_recovery_agent_stats():
    from ai_generation.agents.recovery_agent import RecoveryAgent
    agent = RecoveryAgent()
    stats = agent.get_stats()
    assert stats["total_incidents"] == 0

# ── Evolution Agent Tests ────────────────────────────────────────

def test_evolution_agent_import():
    from ai_generation.agents.evolution_agent import EvolutionAgent
    agent = EvolutionAgent()
    assert agent.agent_name == "evolution"

def test_evolution_agent_evolve():
    from ai_generation.agents.evolution_agent import EvolutionAgent
    from ai_generation.agents.base_agent import AgentTask
    agent = EvolutionAgent()
    task = AgentTask(task_type="evolve")
    result = agent.execute(task)
    assert result.success
    assert result.data["version"] == 2

def test_evolution_agent_routing():
    from ai_generation.agents.evolution_agent import EvolutionAgent
    from ai_generation.agents.base_agent import AgentTask
    agent = EvolutionAgent()
    task = AgentTask(task_type="refresh_routing", payload={"task_type": "text_to_image", "rankings": [{"provider": "a", "score": 0.9}]})
    result = agent.execute(task)
    assert result.success

def test_evolution_agent_stats():
    from ai_generation.agents.evolution_agent import EvolutionAgent
    agent = EvolutionAgent()
    stats = agent.get_stats()
    assert stats["version"] == 1

# ── Knowledge Agent Tests ────────────────────────────────────────

def test_knowledge_agent_import():
    from ai_generation.agents.knowledge_agent import KnowledgeAgent
    agent = KnowledgeAgent()
    assert agent.agent_name == "knowledge"

def test_knowledge_agent_store_query():
    from ai_generation.agents.knowledge_agent import KnowledgeAgent
    from ai_generation.agents.base_agent import AgentTask
    agent = KnowledgeAgent()
    store_task = AgentTask(task_type="store", payload={"domain": "providers", "key": "test", "value": {"url": "http://test.com"}})
    result = agent.execute(store_task)
    assert result.success
    query_task = AgentTask(task_type="query", payload={"domain": "providers", "key": "test"})
    result = agent.execute(query_task)
    assert result.success
    assert result.data["url"] == "http://test.com"

def test_knowledge_agent_search():
    from ai_generation.agents.knowledge_agent import KnowledgeAgent
    from ai_generation.agents.base_agent import AgentTask
    agent = KnowledgeAgent()
    store_task = AgentTask(task_type="store", payload={"domain": "providers", "key": "pollinations", "value": {"url": "http://pollinations.ai"}})
    agent.execute(store_task)
    search_task = AgentTask(task_type="search", payload={"query": "pollinations"})
    result = agent.execute(search_task)
    assert result.success
    assert result.data["total_matches"] >= 1

def test_knowledge_agent_stats():
    from ai_generation.agents.knowledge_agent import KnowledgeAgent
    agent = KnowledgeAgent()
    stats = agent.get_stats()
    assert stats["total_entries"] >= 0

# ── Planner Agent Tests ──────────────────────────────────────────

def test_planner_agent_import():
    from ai_generation.agents.planner_agent import PlannerAgent
    agent = PlannerAgent()
    assert agent.agent_name == "planner"

def test_planner_agent_plan():
    from ai_generation.agents.planner_agent import PlannerAgent
    from ai_generation.agents.base_agent import AgentTask
    agent = PlannerAgent()
    task = AgentTask(task_type="execute_request", payload={"request": "Generate a luxury cafe advertisement"})
    result = agent.execute(task)
    assert result.success
    assert result.data["plan"]["task_type"] == "text_to_image"
    assert result.data["plan"]["total_steps"] == 6

def test_planner_agent_video_plan():
    from ai_generation.agents.planner_agent import PlannerAgent
    from ai_generation.agents.base_agent import AgentTask
    agent = PlannerAgent()
    task = AgentTask(task_type="execute_request", payload={"request": "Create a 15-second product video"})
    result = agent.execute(task)
    assert result.success
    assert result.data["plan"]["task_type"] == "text_to_video"

def test_planner_agent_stats():
    from ai_generation.agents.planner_agent import PlannerAgent
    agent = PlannerAgent()
    stats = agent.get_stats()
    assert stats["total_plans"] == 0

# ── Knowledge Graph Tests ────────────────────────────────────────

def test_knowledge_graph_import():
    from ai_generation.knowledge_graph import KnowledgeGraph, GraphNode, GraphEdge
    kg = KnowledgeGraph()
    assert kg.get_stats()["total_nodes"] >= 0

def test_knowledge_graph_add_node():
    from ai_generation.knowledge_graph import KnowledgeGraph, GraphNode
    kg = KnowledgeGraph()
    node = GraphNode(node_id="provider_1", node_type="provider", name="test_provider", properties={"url": "http://test.com"})
    kg.add_node(node)
    assert kg.get_node("provider_1").name == "test_provider"

def test_knowledge_graph_add_edge():
    from ai_generation.knowledge_graph import KnowledgeGraph, GraphNode, GraphEdge
    kg = KnowledgeGraph()
    kg.add_node(GraphNode(node_id="p1", node_type="provider", name="p1"))
    kg.add_node(GraphNode(node_id="m1", node_type="model", name="m1"))
    kg.add_edge(GraphEdge(source_id="p1", target_id="m1", edge_type="offers_model"))
    neighbors = kg.get_neighbors("p1")
    assert len(neighbors) == 1
    assert neighbors[0].node_id == "m1"

def test_knowledge_graph_query():
    from ai_generation.knowledge_graph import KnowledgeGraph, GraphNode, GraphEdge
    kg = KnowledgeGraph()
    kg.add_node(GraphNode(node_id="p1", node_type="provider", name="test"))
    kg.add_node(GraphNode(node_id="c1", node_type="capability", name="text_to_image"))
    kg.add_edge(GraphEdge(source_id="p1", target_id="c1", edge_type="supports"))
    providers = kg.query_providers_by_capability("text_to_image")
    assert "p1" in providers

def test_knowledge_graph_stats():
    from ai_generation.knowledge_graph import KnowledgeGraph, GraphNode
    kg = KnowledgeGraph()
    kg.add_node(GraphNode(node_id="n1", node_type="provider", name="p1"))
    stats = kg.get_stats()
    assert stats["total_nodes"] >= 1

# ── Dynamic Adapter Tests ────────────────────────────────────────

def test_dynamic_adapter_import():
    from ai_generation.dynamic_adapter import DynamicAdapterManager
    mgr = DynamicAdapterManager()
    assert mgr.get_stats()["total_adapters"] == 0

def test_dynamic_adapter_parse_openapi():
    from ai_generation.dynamic_adapter import SchemaParser
    parser = SchemaParser()
    schema = {"paths": {"/generate": {"post": {"operationId": "generate", "summary": "Generate image"}}}, "securityDefinitions": {"api_key": {"type": "apiKey"}}}
    adapter = parser.parse_openapi(schema)
    assert len(adapter.endpoints) == 1
    assert adapter.endpoints[0]["operation_id"] == "generate"

def test_dynamic_adapter_parse_mcp():
    from ai_generation.dynamic_adapter import SchemaParser
    parser = SchemaParser()
    tools = {"generate_image": {"description": "Generate image", "inputSchema": {"type": "object"}}}
    adapter = parser.parse_mcp_tools(tools, provider="test")
    assert len(adapter.endpoints) == 1

def test_dynamic_adapter_compile():
    from ai_generation.dynamic_adapter import DynamicAdapterManager
    mgr = DynamicAdapterManager()
    adapter = mgr.register_schema("test", {"generate": {"method": "POST", "path": "/api"}}, "custom")
    assert adapter.provider == "test"
    assert len(adapter.endpoint_handlers) == 1

def test_dynamic_adapter_stats():
    from ai_generation.dynamic_adapter import DynamicAdapterManager
    mgr = DynamicAdapterManager()
    mgr.register_schema("test", {"gen": {"method": "POST"}}, "custom")
    stats = mgr.get_stats()
    assert stats["total_adapters"] == 1

# ── Benchmark Lab Tests ──────────────────────────────────────────

def test_benchmark_lab_import():
    from ai_generation.benchmark_lab import BenchmarkLab
    lab = BenchmarkLab()
    assert lab.get_stats()["total_results"] >= 0

def test_benchmark_lab_categories():
    from ai_generation.benchmark_lab import BenchmarkLab
    lab = BenchmarkLab()
    cats = lab.get_all_categories()
    assert len(cats) >= 5
    assert "realism" in cats

def test_benchmark_lab_prompts():
    from ai_generation.benchmark_lab import BenchmarkLab
    lab = BenchmarkLab()
    prompts = lab.get_benchmark_prompts("realism")
    assert len(prompts) >= 2

def test_benchmark_lab_record():
    from ai_generation.benchmark_lab import BenchmarkLab, BenchmarkResult
    lab = BenchmarkLab()
    result = BenchmarkResult(provider="test", model="m1", category="realism", prompt="test", quality_score=0.8, prompt_adherence=0.9, latency_ms=1000, success=True)
    lab.record_result(result)
    assert lab.get_stats()["total_results"] >= 1

def test_benchmark_lab_leaderboard():
    from ai_generation.benchmark_lab import BenchmarkLab, BenchmarkResult
    lab = BenchmarkLab()
    lab.record_result(BenchmarkResult(provider="a", model="m1", category="realism", prompt="t", quality_score=0.9, prompt_adherence=0.8, latency_ms=500, success=True))
    lab.record_result(BenchmarkResult(provider="b", model="m2", category="realism", prompt="t", quality_score=0.7, prompt_adherence=0.6, latency_ms=2000, success=True))
    lb = lab.get_leaderboard()
    assert len(lb) >= 2
    assert lb[0]["provider"] == "a"

# ── SDK Phase 14 Tests ──────────────────────────────────────────

def test_sdk_phase14_properties():
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    assert hasattr(ai, 'aigos')
    assert hasattr(ai, 'knowledge_graph')
    assert hasattr(ai, 'dynamic_adapter_manager')
    assert hasattr(ai, 'benchmark_lab')

def test_sdk_aigos_status():
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    status = ai.aigos_status()
    assert status["initialized"] is True
    assert status["registry"]["total_agents"] == 10

def test_sdk_aigos_agents():
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    agents = ai.aigos_agents()
    assert len(agents) == 10
    names = [a["agent_name"] for a in agents]
    assert "research" in names
    assert "execution" in names
    assert "planner" in names

def test_sdk_aigos_providers():
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    providers = ai.aigos_providers()
    assert len(providers) >= 10

def test_sdk_aigos_endpoints():
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    endpoints = ai.aigos_endpoints()
    assert len(endpoints) >= 9

def test_sdk_aigos_knowledge():
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    result = ai.aigos_knowledge_query("test")
    assert "total_matches" in result

def test_sdk_aigos_execute():
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    result = ai.aigos_execute("Generate a luxury cafe advertisement")
    assert result["success"] is True
    assert "plan" in result.get("data", {})

# ── MCP Phase 14 Tests ──────────────────────────────────────────

def test_mcp_phase14_tools():
    from ai_generation.mcp_tools import get_mcp_generation_tools
    tools = get_mcp_generation_tools()
    assert len(tools) >= 44
    p14_tools = [t for t in tools if t.startswith("aigos_")]
    assert len(p14_tools) >= 11
    assert "aigos_status" in tools
    assert "aigos_execute" in tools
    assert "aigos_agents" in tools
    assert "aigos_knowledge_search" in tools
    assert "aigos_leaderboard" in tools
    assert "aigos_verify_provider" in tools
    assert "aigos_benchmark" in tools
    assert "aigos_report_failure" in tools
    assert "aigos_evolve" in tools

@pytest.mark.asyncio
async def test_mcp_aigos_status():
    from ai_generation.mcp_tools import MCPGenerationTools
    handler = MCPGenerationTools()
    result = await handler.handle("aigos_status", {})
    assert result["initialized"] is True
    assert result["registry"]["total_agents"] == 10

@pytest.mark.asyncio
async def test_mcp_aigos_agents():
    from ai_generation.mcp_tools import MCPGenerationTools
    handler = MCPGenerationTools()
    result = await handler.handle("aigos_agents", {})
    assert len(result["agents"]) == 10

# ── Integration: Full Pipeline Test ──────────────────────────────

def test_full_orchestrator_pipeline():
    from ai_generation.agents.agent_registry import AgentOrchestrator
    orch = AgentOrchestrator()
    orch.initialize()
    result = orch.execute_request("Generate a cinematic coffee advertisement")
    assert result["success"] is True
    plan = result.get("data", {}).get("plan", {})
    assert plan.get("task_type") == "text_to_image"
    assert plan.get("total_steps", 0) >= 4

# ── Existing Test Compatibility ──────────────────────────────────

def test_existing_generation_still_works():
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    stats = ai.get_stats()
    assert "generation" in stats
    assert "prompts" in stats

def test_existing_mcp_still_works():
    from ai_generation.mcp_tools import get_mcp_generation_tools
    tools = get_mcp_generation_tools()
    assert "generate_image" in tools
    assert "generate_video" in tools
    assert "enhance_prompt" in tools

def test_existing_cli_imports():
    from ai_generation.cli import main
    assert callable(main)

def test_existing_sdk_imports():
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    assert hasattr(ai, 'generate')
    assert hasattr(ai, 'prompt_engine')
    assert hasattr(ai, 'quality_engine')
