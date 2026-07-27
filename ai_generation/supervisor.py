"""
Supervisor Tree — Fail-Fast, Recover-Quietly framework.

Based on ACOS Research: Erlang/OTP-style supervision.
Ported from acos-research/core/supervisor.py for production use.

Constitution Adherence:
- Fail-Fast, Recover-Quietly: Erroneous states trigger immediate panics,
  caught and handled by isolated Supervisor trees.
- Strict Separation of Concerns: Supervisors handle lifecycle, not logic.
"""
import logging
import time
import traceback
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, TypeVar

T = TypeVar('T')
logger = logging.getLogger(__name__)


class SupervisionStrategy(str, Enum):
    """Erlang/OTP-style supervision strategies."""
    ONE_FOR_ONE = "one_for_one"       # Restart only the failed worker
    ONE_FOR_ALL = "one_for_all"       # Restart all workers if one fails
    REST_FOR_ONE = "rest_for_one"     # Restart failed + all started after it
    PERMANENT = "permanent"           # Always restart
    TRANSIENT = "transient"           # Restart only if abnormally terminated
    TEMPORARY = "temporary"           # Never restart


class WorkerType(str, Enum):
    """Types of supervised workers."""
    PROVIDER = "provider"
    AGENT = "agent"
    MONITOR = "monitor"
    ENGINE = "engine"
    CUSTOM = "custom"


@dataclass
class SupervisorConfig:
    """Configuration for a supervisor."""
    strategy: SupervisionStrategy = SupervisionStrategy.ONE_FOR_ONE
    max_restarts: int = 5
    restart_interval_secs: float = 60.0
    exponential_backoff_base: float = 2.0
    initial_backoff_secs: float = 0.5
    health_check_interval_secs: float = 30.0


@dataclass
class WorkerState:
    """State of a supervised worker."""
    worker_id: str = ""
    name: str = ""
    worker_type: WorkerType = WorkerType.CUSTOM
    status: str = "idle"  # idle, running, crashed, stopped, recovering
    restart_count: int = 0
    restart_history: List[float] = field(default_factory=list)
    last_restart: float = 0.0
    last_error: str = ""
    last_success: float = 0.0
    started_at: float = 0.0
    total_executions: int = 0
    total_failures: int = 0

    @property
    def success_rate(self) -> float:
        total = self.total_executions + self.total_failures
        return self.total_executions / max(total, 1)

    @property
    def is_crashed(self) -> bool:
        return self.status in ("crashed", "stopped")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "worker_id": self.worker_id,
            "name": self.name,
            "type": self.worker_type.value,
            "status": self.status,
            "restart_count": self.restart_count,
            "success_rate": round(self.success_rate, 3),
            "total_executions": self.total_executions,
            "total_failures": self.total_failures,
            "last_error": self.last_error[:200] if self.last_error else "",
            "last_success": datetime.fromtimestamp(self.last_success).isoformat() if self.last_success else "",
        }


class SupervisorError(Exception):
    """Raised when a supervised operation fails."""
    pass


class WorkerCrashError(SupervisorError):
    """Raised when a worker crashes and cannot be recovered."""
    pass


@dataclass
class SupervisionEvent:
    """An event in the supervision lifecycle."""
    event_type: str = ""  # worker_started, worker_crashed, worker_restarted, worker_stopped, supervisor_escalated
    worker_id: str = ""
    supervisor_name: str = ""
    error: str = ""
    restart_count: int = 0
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type": self.event_type,
            "worker_id": self.worker_id,
            "supervisor": self.supervisor_name,
            "error": self.error[:200],
            "restart_count": self.restart_count,
            "timestamp": datetime.fromtimestamp(self.timestamp).isoformat(),
        }


class SupervisorTree:
    """
    Fail-Fast, Recover-Quietly supervisor tree.

    Provides fault tolerance for providers, agents, engines, and monitors.
    If a worker crashes, the supervisor automatically restarts it with
    exponential backoff. If max restarts exceeded, the supervisor escalates.

    Inspired by Erlang/OTP supervisor philosophy.
    """

    def __init__(self, name: str = "root", config: Optional[SupervisorConfig] = None):
        self.name = name
        self.config = config or SupervisorConfig()
        self._workers: Dict[str, Callable] = {}
        self._worker_configs: Dict[str, Dict[str, Any]] = {}
        self._worker_states: Dict[str, WorkerState] = {}
        self._children: Dict[str, 'SupervisorTree'] = {}
        self._parent: Optional['SupervisorTree'] = None
        self._events: List[SupervisionEvent] = []
        self._event_handlers: List[Callable] = []

    def add_worker(self, worker_id: str, fn: Callable[[], T],
                   name: str = "", worker_type: WorkerType = WorkerType.CUSTOM,
                   config: Optional[Dict[str, Any]] = None):
        """Register a supervised worker function."""
        self._workers[worker_id] = fn
        self._worker_configs[worker_id] = config or {}
        self._worker_states[worker_id] = WorkerState(
            worker_id=worker_id,
            name=name or worker_id,
            worker_type=worker_type,
        )
        logger.debug(f"Supervisor '{self.name}': registered worker '{worker_id}'")

    def add_child(self, name: str, supervisor: 'SupervisorTree'):
        """Add a child supervisor (forms the hierarchy)."""
        self._children[name] = supervisor
        supervisor._parent = self

    def on_event(self, handler: Callable[[SupervisionEvent], None]):
        """Register an event handler for supervision events."""
        self._event_handlers.append(handler)

    def run_worker(self, worker_id: str, *args, **kwargs) -> Any:
        """
        Run a worker with supervision.

        Fail-Fast: If the worker raises, the supervisor handles recovery.
        """
        if worker_id not in self._workers:
            raise SupervisorError(f"Unknown worker: {worker_id}")

        fn = self._workers[worker_id]
        state = self._worker_states[worker_id]

        while True:
            try:
                state.status = "running"
                state.started_at = time.time()
                result = fn(*args, **kwargs)
                state.status = "idle"
                state.total_executions += 1
                state.last_success = time.time()
                return result
            except Exception as e:
                error_msg = f"{type(e).__name__}: {e}"
                state.last_error = error_msg
                state.total_failures += 1
                state.restart_count += 1
                state.last_restart = time.time()
                state.status = "crashed"

                state.restart_history.append(state.last_restart)
                self._emit_event(SupervisionEvent(
                    event_type="worker_crashed",
                    worker_id=worker_id,
                    supervisor_name=self.name,
                    error=error_msg,
                    restart_count=state.restart_count,
                ))

                logger.warning(
                    f"Supervisor '{self.name}': worker '{worker_id}' crashed: {error_msg}"
                )

                # Check restart limits
                if state.restart_count > self.config.max_restarts:
                    cutoff = time.time() - self.config.restart_interval_secs
                    recent = sum(1 for r in state.restart_history if r > cutoff)
                    if recent >= self.config.max_restarts:
                        logger.error(
                            f"Supervisor '{self.name}': worker '{worker_id}' "
                            f"exceeded max restarts ({self.config.max_restarts}) "
                            f"in {self.config.restart_interval_secs}s. Giving up."
                        )
                        state.status = "stopped"
                        self._emit_event(SupervisionEvent(
                            event_type="supervisor_escalated",
                            worker_id=worker_id,
                            supervisor_name=self.name,
                            error=f"Max restarts exceeded: {error_msg}",
                            restart_count=state.restart_count,
                        ))
                        raise WorkerCrashError(
                            f"Worker {worker_id} crashed {state.restart_count} times: {error_msg}"
                        )

                # Exponential backoff
                backoff = self.config.initial_backoff_secs * (
                    self.config.exponential_backoff_base ** (state.restart_count - 1)
                )
                backoff = min(backoff, 30.0)  # Cap at 30 seconds
                logger.info(
                    f"Supervisor '{self.name}': restarting '{worker_id}' "
                    f"in {backoff:.1f}s (attempt {state.restart_count})"
                )
                state.status = "recovering"
                time.sleep(backoff)

                # Apply strategy
                if self.config.strategy == SupervisionStrategy.ONE_FOR_ALL:
                    self._restart_all_workers()
                elif self.config.strategy == SupervisionStrategy.REST_FOR_ONE:
                    self._restart_rest_for_one(worker_id)

                self._emit_event(SupervisionEvent(
                    event_type="worker_restarted",
                    worker_id=worker_id,
                    supervisor_name=self.name,
                    restart_count=state.restart_count,
                ))

    def run_worker_safe(self, worker_id: str, *args, **kwargs) -> Optional[Any]:
        """
        Run a worker safely — catches all exceptions and returns None on failure.
        Use this for non-critical workers where crashing should not propagate.
        """
        try:
            return self.run_worker(worker_id, *args, **kwargs)
        except (SupervisorError, Exception) as e:
            logger.error(f"Supervisor '{self.name}': safe run of '{worker_id}' failed: {e}")
            return None

    def stop_worker(self, worker_id: str):
        """Stop a supervised worker."""
        if worker_id in self._worker_states:
            state = self._worker_states[worker_id]
            state.status = "stopped"
            self._emit_event(SupervisionEvent(
                event_type="worker_stopped",
                worker_id=worker_id,
                supervisor_name=self.name,
            ))

    def stop_all(self):
        """Stop all workers."""
        for worker_id in list(self._workers.keys()):
            self.stop_worker(worker_id)
        for child in self._children.values():
            child.stop_all()

    def start_worker(self, worker_id: str):
        """Reset a worker to idle state (allow re-execution)."""
        if worker_id in self._worker_states:
            state = self._worker_states[worker_id]
            state.status = "idle"
            state.restart_count = 0
            state.restart_history.clear()

    def get_worker_state(self, worker_id: str) -> Optional[Dict[str, Any]]:
        """Get the state of a worker."""
        state = self._worker_states.get(worker_id)
        return state.to_dict() if state else None

    def get_all_states(self) -> Dict[str, Dict[str, Any]]:
        """Get states of all workers."""
        return {wid: s.to_dict() for wid, s in self._worker_states.items()}

    def get_crashed_workers(self) -> List[str]:
        """Get list of crashed worker IDs."""
        return [wid for wid, s in self._worker_states.items() if s.is_crashed]

    def get_healthy_workers(self) -> List[str]:
        """Get list of healthy (non-crashed) worker IDs."""
        return [wid for wid, s in self._worker_states.items() if not s.is_crashed]

    def get_stats(self) -> Dict[str, Any]:
        """Get supervisor statistics."""
        total_workers = len(self._workers)
        crashed = len(self.get_crashed_workers())
        total_restarts = sum(s.restart_count for s in self._worker_states.values())
        total_executions = sum(s.total_executions for s in self._worker_states.values())
        total_failures = sum(s.total_failures for s in self._worker_states.values())
        return {
            "supervisor": self.name,
            "strategy": self.config.strategy.value,
            "total_workers": total_workers,
            "healthy": total_workers - crashed,
            "crashed": crashed,
            "total_restarts": total_restarts,
            "total_executions": total_executions,
            "total_failures": total_failures,
            "success_rate": round(total_executions / max(total_executions + total_failures, 1), 3),
            "children": len(self._children),
            "events": len(self._events),
        }

    def get_events(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent supervision events."""
        return [e.to_dict() for e in self._events[-limit:]]

    def reset_all(self):
        """Reset all worker states (clear crash counts, restart histories)."""
        for state in self._worker_states.values():
            state.restart_count = 0
            state.restart_history.clear()
            state.status = "idle"
            state.last_error = ""

    def _restart_all_workers(self):
        """Restart all workers (ONE_FOR_ALL strategy)."""
        for worker_id in self._workers:
            if worker_id in self._worker_states:
                state = self._worker_states[worker_id]
                if state.is_crashed:
                    state.status = "idle"
                    self._emit_event(SupervisionEvent(
                        event_type="worker_restarted",
                        worker_id=worker_id,
                        supervisor_name=self.name,
                        restart_count=state.restart_count,
                    ))

    def _restart_rest_for_one(self, failed_worker_id: str):
        """Restart the failed worker and all workers started after it."""
        worker_ids = list(self._workers.keys())
        try:
            idx = worker_ids.index(failed_worker_id)
        except ValueError:
            return
        for worker_id in worker_ids[idx:]:
            if worker_id in self._worker_states:
                state = self._worker_states[worker_id]
                if state.is_crashed:
                    state.status = "idle"

    def _emit_event(self, event: SupervisionEvent):
        """Emit a supervision event to all handlers."""
        self._events.append(event)
        for handler in self._event_handlers:
            try:
                handler(event)
            except Exception:
                pass  # Don't let event handler failures crash the supervisor

    def __repr__(self) -> str:
        return (
            f"SupervisorTree(name='{self.name}', "
            f"workers={len(self._workers)}, "
            f"strategy={self.config.strategy.value})"
        )


# ── Pre-built Supervision Trees ───────────────────────────────

def create_provider_supervisor() -> SupervisorTree:
    """Create a supervisor tree for AI generation providers."""
    return SupervisorTree(
        name="providers",
        config=SupervisorConfig(
            strategy=SupervisionStrategy.ONE_FOR_ONE,
            max_restarts=3,
            restart_interval_secs=120.0,
            exponential_backoff_base=2.0,
            initial_backoff_secs=1.0,
        ),
    )


def create_agent_supervisor() -> SupervisorTree:
    """Create a supervisor tree for AIG-OS agents."""
    return SupervisorTree(
        name="agents",
        config=SupervisorConfig(
            strategy=SupervisionStrategy.ONE_FOR_ONE,
            max_restarts=5,
            restart_interval_secs=60.0,
            exponential_backoff_base=2.0,
            initial_backoff_secs=0.5,
        ),
    )


def create_engine_supervisor() -> SupervisorTree:
    """Create a supervisor tree for platform engines."""
    return SupervisorTree(
        name="engines",
        config=SupervisorConfig(
            strategy=SupervisionStrategy.REST_FOR_ONE,
            max_restarts=3,
            restart_interval_secs=60.0,
            exponential_backoff_base=2.0,
            initial_backoff_secs=0.5,
        ),
    )


def create_platform_supervisor() -> SupervisorTree:
    """
    Create the top-level platform supervisor with child supervisors.
    This is the root of the supervision tree.
    """
    root = SupervisorTree(
        name="platform",
        config=SupervisorConfig(
            strategy=SupervisionStrategy.ONE_FOR_ONE,
            max_restarts=10,
            restart_interval_secs=300.0,
        ),
    )
    root.add_child("providers", create_provider_supervisor())
    root.add_child("agents", create_agent_supervisor())
    root.add_child("engines", create_engine_supervisor())
    return root
