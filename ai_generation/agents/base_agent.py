"""
Base Agent — foundation class for all AIG-OS autonomous agents.
Provides lifecycle management, task execution, health tracking, and event logging.
"""
import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class AgentStatus(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"
    STOPPED = "stopped"


class AgentPriority(int, Enum):
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class AgentTask:
    task_id: str = ""
    task_type: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)
    priority: AgentPriority = AgentPriority.NORMAL
    created_at: str = ""
    timeout_secs: float = 300.0
    retry_count: int = 0
    max_retries: int = 3

    def __post_init__(self):
        if not self.task_id:
            self.task_id = str(uuid.uuid4())[:8]
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()


@dataclass
class AgentResult:
    success: bool = True
    task_id: str = ""
    agent_name: str = ""
    data: Dict[str, Any] = field(default_factory=dict)
    error: str = ""
    duration_ms: float = 0.0
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "task_id": self.task_id,
            "agent_name": self.agent_name,
            "data": self.data,
            "error": self.error,
            "duration_ms": round(self.duration_ms, 1),
            "timestamp": self.timestamp,
        }


class BaseAgent:
    """
    Foundation for all AIG-OS agents.

    Provides:
    - Lifecycle management (start, stop, pause, resume)
    - Task queue and execution
    - Health tracking
    - Event logging
    - Configuration management
    """

    agent_name: str = "base"
    agent_description: str = ""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._status = AgentStatus.IDLE
        self._task_history: List[AgentResult] = []
        self._error_count = 0
        self._success_count = 0
        self._last_run: Optional[str] = None
        self._start_time = time.time()
        self._event_log: List[Dict[str, Any]] = []

    @property
    def status(self) -> AgentStatus:
        return self._status

    def start(self):
        self._status = AgentStatus.IDLE
        self._log_event("agent_started")

    def stop(self):
        self._status = AgentStatus.STOPPED
        self._log_event("agent_stopped")

    def pause(self):
        self._status = AgentStatus.PAUSED
        self._log_event("agent_paused")

    def resume(self):
        self._status = AgentStatus.IDLE
        self._log_event("agent_resumed")

    def execute(self, task: AgentTask) -> AgentResult:
        """Execute a task. Override in subclasses."""
        start = time.time()
        try:
            self._status = AgentStatus.RUNNING
            result = self._execute_task(task)
            result.task_id = task.task_id
            result.agent_name = self.agent_name
            result.duration_ms = (time.time() - start) * 1000
            self._success_count += 1
            self._task_history.append(result)
            self._last_run = datetime.now(timezone.utc).isoformat()
            self._status = AgentStatus.IDLE
            self._log_event("task_completed", {"task_id": task.task_id, "success": result.success})
            return result
        except Exception as e:
            result = AgentResult(
                success=False, task_id=task.task_id, agent_name=self.agent_name,
                error=str(e), duration_ms=(time.time() - start) * 1000,
            )
            self._error_count += 1
            self._task_history.append(result)
            self._status = AgentStatus.ERROR
            self._log_event("task_failed", {"task_id": task.task_id, "error": str(e)})
            logger.error(f"{self.agent_name} task {task.task_id} failed: {e}")
            return result

    def _execute_task(self, task: AgentTask) -> AgentResult:
        """Override in subclasses to implement agent logic."""
        raise NotImplementedError(f"{self.agent_name} must implement _execute_task")

    def get_stats(self) -> Dict[str, Any]:
        uptime = time.time() - self._start_time
        return {
            "agent_name": self.agent_name,
            "status": self._status.value,
            "total_tasks": self._success_count + self._error_count,
            "successful": self._success_count,
            "failed": self._error_count,
            "uptime_secs": round(uptime, 1),
            "last_run": self._last_run,
            "event_count": len(self._event_log),
        }

    def get_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        return [r.to_dict() for r in self._task_history[-limit:]]

    def _log_event(self, event_type: str, data: Optional[Dict[str, Any]] = None):
        self._event_log.append({
            "event": event_type,
            "agent": self.agent_name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": data or {},
        })
