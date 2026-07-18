"""
Workflow Engine — multi-step generation pipelines with dependencies,
conditional branching, and parallel execution.
"""
import asyncio
import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class StepStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class WorkflowStep:
    name: str
    action: str  # "generate_image", "generate_video", "enhance_prompt", "evaluate", "custom"
    params: Dict[str, Any] = field(default_factory=dict)
    depends_on: List[str] = field(default_factory=list)
    condition: Optional[str] = None  # python expression evaluated against context
    retry_count: int = 2
    timeout_secs: float = 120.0
    status: StepStatus = StepStatus.PENDING
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    step_id: str = ""

    def __post_init__(self):
        if not self.step_id:
            self.step_id = self.name.replace(" ", "_").lower()


@dataclass
class Workflow:
    name: str
    description: str = ""
    steps: List[WorkflowStep] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    workflow_id: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    status: str = "pending"

    def __post_init__(self):
        if not self.workflow_id:
            self.workflow_id = "wf-" + uuid.uuid4().hex[:8]

    def get_step(self, name: str):
        for s in self.steps:
            if s.step_id == name or s.name == name:
                return s
        return None

    def get_ready_steps(self):
        completed = {s.step_id for s in self.steps if s.status == StepStatus.COMPLETED}
        return [
            s for s in self.steps
            if s.status == StepStatus.PENDING
            and all(dep in completed for dep in s.depends_on)
        ]


class WorkflowEngine:
    """Execute multi-step generation workflows."""

    def __init__(self, generation_manager=None, prompt_engine=None):
        self._gm = generation_manager
        self._pe = prompt_engine
        self._workflows: Dict[str, Workflow] = {}
        self._history: List[Dict[str, Any]] = []

    def create_workflow(self, name, steps, description="", metadata=None):
        wf = Workflow(
            name=name, description=description,
            steps=[WorkflowStep(**s) if isinstance(s, dict) else s for s in steps],
            metadata=metadata or {},
        )
        self._workflows[wf.workflow_id] = wf
        return wf

    def get_workflow(self, workflow_id):
        return self._workflows.get(workflow_id)

    def list_workflows(self):
        return [
            {"id": wf.workflow_id, "name": wf.name, "status": wf.status, "steps": len(wf.steps)}
            for wf in self._workflows.values()
        ]

    async def execute(self, workflow_id, context=None):
        wf = self._workflows.get(workflow_id)
        if not wf:
            return {"error": f"Workflow {workflow_id} not found"}

        ctx = context or {}
        wf.status = "running"
        start = time.time()

        max_iterations = len(wf.steps) * 3
        iteration = 0

        while iteration < max_iterations:
            iteration += 1
            ready = wf.get_ready_steps()
            if not ready:
                break

            tasks = [self._execute_step(step, ctx) for step in ready]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for step, result in zip(ready, results):
                if isinstance(result, Exception):
                    step.status = StepStatus.FAILED
                    step.error = str(result)[:200]
                elif step.status not in (StepStatus.FAILED, StepStatus.SKIPPED):
                    step.status = StepStatus.COMPLETED
                    step.result = result if isinstance(result, dict) else {"output": str(result)}

                if step.result:
                    ctx[step.step_id] = step.result

        all_completed = all(s.status == StepStatus.COMPLETED for s in wf.steps)
        any_failed = any(s.status == StepStatus.FAILED for s in wf.steps)
        wf.status = "completed" if all_completed else "failed" if any_failed else "partial"

        elapsed = round((time.time() - start) * 1000, 1)
        summary = {
            "workflow_id": workflow_id,
            "name": wf.name,
            "status": wf.status,
            "elapsed_ms": elapsed,
            "steps": [
                {"name": s.name, "status": s.status.value, "error": s.error}
                for s in wf.steps
            ],
            "context_keys": list(ctx.keys()),
        }
        self._history.append(summary)
        return summary

    async def _execute_step(self, step, ctx):
        step.status = StepStatus.RUNNING
        step.started_at = datetime.now().isoformat()

        try:
            if step.condition:
                try:
                    if not eval(step.condition, {"__builtins__": {"True": True, "False": False, "None": None}}, ctx):
                        step.status = StepStatus.SKIPPED
                        return {"skipped": True, "reason": "condition_false"}
                except Exception:
                    step.status = StepStatus.SKIPPED
                    return {"skipped": True, "reason": "condition_error"}

            params = self._resolve_params(step.params, ctx)

            if step.action == "generate_image" and self._gm:
                from .providers.base import ProviderType
                request = self._gm.plan_generation
                result = await self._gm.generate_image(**params)
                return result.to_dict()

            elif step.action == "generate_video" and self._gm:
                result = await self._gm.generate_video(**params)
                return result.to_dict()

            elif step.action == "enhance_prompt" and self._pe:
                result = self._pe.enhance(**params)
                return {
                    "enhanced": result.enhanced,
                    "negative_prompt": result.negative_prompt,
                    "techniques": result.techniques_applied,
                }

            elif step.action == "evaluate":
                return {"evaluated": True, "params": params}

            elif step.action == "custom":
                func = params.pop("func", None)
                if callable(func):
                    return await func(**params) if asyncio.iscoroutinefunction(func) else func(**params)
                return {"custom": True, "params": params}

            else:
                return {"action": step.action, "params": params, "note": "no_handler"}

        except Exception as e:
            step.status = StepStatus.FAILED
            step.error = str(e)[:200]
            raise
        finally:
            step.completed_at = datetime.now().isoformat()

    def _resolve_params(self, params, ctx):
        resolved = {}
        for k, v in params.items():
            if isinstance(v, str) and v.startswith("$"):
                ref = v[1:]
                resolved[k] = ctx.get(ref, v)
            elif isinstance(v, dict):
                resolved[k] = self._resolve_params(v, ctx)
            else:
                resolved[k] = v
        return resolved

    def get_stats(self):
        return {
            "total_workflows": len(self._workflows),
            "executed": len(self._history),
            "by_status": {},
        }


# Preset workflows
def create_image_series_workflow(prompts, style="photorealistic", provider_type="image"):
    steps = []
    for i, prompt in enumerate(prompts):
        step = {
            "name": f"generate_{i}",
            "action": "enhance_prompt",
            "params": {"prompt": prompt, "style": style},
        }
        if i > 0:
            step["depends_on"] = [f"generate_{i-1}"]
        steps.append(step)
    return steps
