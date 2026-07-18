"""
Agent Registry & Orchestrator — manages all AIG-OS agents.
Coordinates task assignment, health monitoring, and lifecycle.
"""
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Type

from .base_agent import AgentStatus, AgentTask, AgentResult, BaseAgent

logger = logging.getLogger(__name__)


class AgentRegistry:
    """Registry for all AIG-OS agents."""

    def __init__(self):
        self._agents: Dict[str, BaseAgent] = {}
        self._agent_classes: Dict[str, Type[BaseAgent]] = {}

    def register_agent_class(self, name: str, agent_class: Type[BaseAgent]):
        self._agent_classes[name] = agent_class

    def create_agent(self, name: str, config: Optional[Dict[str, Any]] = None) -> BaseAgent:
        if name not in self._agent_classes:
            raise ValueError(f"Unknown agent class: {name}")
        agent = self._agent_classes[name](config)
        self._agents[name] = agent
        return agent

    def get_agent(self, name: str) -> Optional[BaseAgent]:
        return self._agents.get(name)

    def list_agents(self) -> List[Dict[str, Any]]:
        return [a.get_stats() for a in self._agents.values()]

    def start_all(self):
        for agent in self._agents.values():
            agent.start()

    def stop_all(self):
        for agent in self._agents.values():
            agent.stop()

    def get_healthy_agents(self) -> List[str]:
        return [name for name, a in self._agents.items() if a.status != AgentStatus.ERROR]

    def get_stats(self) -> Dict[str, Any]:
        return {
            "total_agents": len(self._agents),
            "registered_classes": len(self._agent_classes),
            "healthy": len(self.get_healthy_agents()),
            "agents": {name: a.get_stats() for name, a in self._agents.items()},
        }


class AgentOrchestrator:
    """
    Orchestrates all agents for end-to-end AIG-OS execution.
    Routes tasks, coordinates agents, manages workflows.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.registry = AgentRegistry()
        self._execution_log: List[Dict[str, Any]] = []
        self._initialized = False

    def initialize(self):
        """Register all built-in agent classes."""
        if self._initialized:
            return
        from .research_agent import ResearchAgent
        from .discovery_agent import DiscoveryAgent
        from .integration_agent import IntegrationAgent
        from .verification_agent import VerificationAgent
        from .benchmark_agent import BenchmarkAgent
        from .execution_agent_p14 import ExecutionAgentV2
        from .recovery_agent import RecoveryAgent
        from .evolution_agent import EvolutionAgent
        from .knowledge_agent import KnowledgeAgent
        from .planner_agent import PlannerAgent

        self.registry.register_agent_class("research", ResearchAgent)
        self.registry.register_agent_class("discovery", DiscoveryAgent)
        self.registry.register_agent_class("integration", IntegrationAgent)
        self.registry.register_agent_class("verification", VerificationAgent)
        self.registry.register_agent_class("benchmark", BenchmarkAgent)
        self.registry.register_agent_class("execution", ExecutionAgentV2)
        self.registry.register_agent_class("recovery", RecoveryAgent)
        self.registry.register_agent_class("evolution", EvolutionAgent)
        self.registry.register_agent_class("knowledge", KnowledgeAgent)
        self.registry.register_agent_class("planner", PlannerAgent)

        for name in self.registry._agent_classes:
            self.registry.create_agent(name, self.config)

        self.registry.start_all()
        self._initialized = True
        logger.info("AIG-OS Orchestrator initialized with %d agents", len(self.registry._agents))

    def submit_task(self, task: AgentTask, agent_name: Optional[str] = None) -> AgentResult:
        """Submit a task to a specific agent or let the planner decide."""
        self.initialize()
        if agent_name:
            agent = self.registry.get_agent(agent_name)
            if not agent:
                return AgentResult(success=False, error=f"Agent not found: {agent_name}")
            return agent.execute(task)

        planner = self.registry.get_agent("planner")
        if planner:
            return planner.execute(task)
        return AgentResult(success=False, error="No planner agent available")

    def execute_request(self, request: str) -> Dict[str, Any]:
        """High-level: execute a natural language request through the full pipeline."""
        self.initialize()
        planner = self.registry.get_agent("planner")
        if not planner:
            return {"error": "Planner not available"}
        task = AgentTask(
            task_type="execute_request",
            payload={"request": request},
        )
        result = planner.execute(task)
        return result.to_dict()

    def get_status(self) -> Dict[str, Any]:
        self.initialize()
        return {
            "initialized": self._initialized,
            "registry": self.registry.get_stats(),
            "recent_executions": self._execution_log[-5:],
        }

    def get_stats(self) -> Dict[str, Any]:
        self.initialize()
        return {
            "initialized": self._initialized,
            "total_agents": len(self.registry._agents),
            "total_executions": len(self._execution_log),
            "agent_stats": {name: a.get_stats() for name, a in self.registry._agents.items()},
        }
