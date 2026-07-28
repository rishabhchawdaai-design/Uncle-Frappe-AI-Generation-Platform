"""
Planner Agent — coordinates all agents. Determines what to research,
benchmark, integrate, remove, execute, and retry. Central coordinator for AIG-OS.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .base_agent import BaseAgent, AgentTask, AgentResult


class PlannerAgent(BaseAgent):
    agent_name = "planner"
    agent_description = "Coordinates all AIG-OS agents and orchestrates end-to-end workflows"

    def __init__(self, config=None):
        super().__init__(config)
        self._execution_plans: List[Dict[str, Any]] = []
        self._workflow_history: List[Dict[str, Any]] = []
        self._active_plan: Optional[Dict[str, Any]] = None

    def _execute_task(self, task: AgentTask) -> AgentResult:
        task_type = task.task_type
        if task_type == "execute_request":
            return self._plan_and_execute(task)
        elif task_type == "create_plan":
            return self._create_plan(task)
        elif task_type == "get_plan":
            return AgentResult(data={"active_plan": self._active_plan})
        elif task_type == "get_history":
            return AgentResult(data={"history": self._workflow_history[-20:], "total": len(self._workflow_history)})
        return AgentResult(data={"status": "unknown_task"})

    def _plan_and_execute(self, task: AgentTask) -> AgentResult:
        request = task.payload.get("request", "")
        plan = self._create_execution_plan(request)
        self._execution_plans.append(plan)
        self._active_plan = plan

        workflow = {
            "request": request, "plan": plan,
            "status": "planned", "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self._workflow_history.append(workflow)

        return AgentResult(data={
            "request": request,
            "plan": plan,
            "status": "ready_for_execution",
            "note": "Plan created. Use execution agent to run.",
        })

    def _create_execution_plan(self, request: str) -> Dict[str, Any]:
        request_lower = request.lower()
        task_type = "text_to_image"
        if any(w in request_lower for w in ["video", "animation", "clip"]):
            task_type = "text_to_video"
        elif any(w in request_lower for w in ["remove background", "cutout"]):
            task_type = "background_removal"
        elif any(w in request_lower for w in ["upscale", "4k", "8k"]):
            task_type = "upscale"
        elif any(w in request_lower for w in ["edit", "inpaint", "outpaint"]):
            task_type = "image_editing"
        elif any(w in request_lower for w in ["audio", "music", "sound"]):
            task_type = "text_to_audio"

        steps = [
            {"step": 1, "agent": "research", "action": "identify_providers", "status": "pending"},
            {"step": 2, "agent": "discovery", "action": "find_endpoints", "status": "pending"},
            {"step": 3, "agent": "verification", "action": "verify_providers", "status": "pending"},
            {"step": 4, "agent": "benchmark", "action": "rank_providers", "status": "pending"},
            {"step": 5, "agent": "execution", "action": "execute_generation", "status": "pending"},
            {"step": 6, "agent": "knowledge", "action": "record_result", "status": "pending"},
        ]

        return {
            "request": request, "task_type": task_type,
            "steps": steps, "total_steps": len(steps),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

    def _create_plan(self, task: AgentTask) -> AgentResult:
        request = task.payload.get("request", "")
        plan = self._create_execution_plan(request)
        return AgentResult(data=plan)

    def get_stats(self) -> Dict[str, Any]:
        base = super().get_stats()
        base.update({
            "total_plans": len(self._execution_plans),
            "total_workflows": len(self._workflow_history),
            "has_active_plan": self._active_plan is not None,
        })
        return base
