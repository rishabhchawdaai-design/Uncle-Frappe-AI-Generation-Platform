"""
AIG-OS Autonomous Agent System

10 autonomous agents that power the AI Generation Operating System.
Each agent handles a specific domain of the platform lifecycle.
"""
from .base_agent import BaseAgent, AgentStatus, AgentTask, AgentResult
from .agent_registry import AgentRegistry, AgentOrchestrator

__all__ = [
    "BaseAgent", "AgentStatus", "AgentTask", "AgentResult",
    "AgentRegistry", "AgentOrchestrator",
]
