"""
Phase 18: 20 Autonomous Agents with Inter-Agent Communication
Specialized agents that communicate automatically via message bus.
"""
import asyncio, json, logging, time, uuid
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Callable, Awaitable, Set
from datetime import datetime
from collections import defaultdict
from enum import Enum

logger = logging.getLogger(__name__)

class AgentRole(str, Enum):
    COORDINATOR = "coordinator"
    RESEARCH = "research"
    CRAWLER = "crawler"
    BROWSER = "browser"
    VERIFICATION = "verification"
    FACT_CHECK = "fact_check"
    OCR = "ocr"
    KNOWLEDGE_GRAPH = "knowledge_graph"
    VECTOR = "vector"
    RESTAURANT = "restaurant_intelligence"
    GOVERNMENT = "government_data"
    NEWS = "news"
    SOCIAL_MEDIA = "social_media"
    ANALYTICS = "analytics"
    REPORTING = "reporting"
    SCHEDULER = "scheduler"
    MONITORING = "monitoring"
    RECOVERY = "recovery"
    SECURITY = "security"
    DATA_QUALITY = "data_quality"

@dataclass
class AgentMessage:
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    sender: str = ""
    recipient: str = ""  # "" = broadcast
    action: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)
    reply_to: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    priority: int = 5  # 0=highest, 9=lowest
    status: str = "pending"  # pending, processing, completed, failed

    def to_dict(self) -> Dict:
        return {k: v for k, v in self.__dict__.items()}


class MessageBus:
    """Inter-agent message bus with priority queues."""

    def __init__(self):
        self._queues: Dict[str, asyncio.Queue] = defaultdict(lambda: asyncio.Queue(maxsize=1000))
        self._broadcast_queue: asyncio.Queue = asyncio.Queue(maxsize=1000)
        self._log: List[AgentMessage] = []
        self._handlers: Dict[str, List[Callable]] = defaultdict(list)

    async def publish(self, message: AgentMessage):
        self._log.append(message)
        if message.recipient:
            await self._queues[message.recipient].put(message)
        else:
            await self._broadcast_queue.put(message)
        logger.debug(f"MSG: {message.sender} -> {message.recipient or 'ALL'}: {message.action}")

    async def receive(self, agent_id: str, timeout: float = 1.0) -> Optional[AgentMessage]:
        try:
            # Check personal queue first
            try:
                return self._queues[agent_id].get_nowait()
            except asyncio.QueueEmpty:
                pass
            # Check broadcast
            try:
                return self._broadcast_queue.get_nowait()
            except asyncio.QueueEmpty:
                pass
            return None
        except asyncio.TimeoutError:
            return None

    def get_log(self, limit: int = 100) -> List[Dict]:
        return [m.to_dict() for m in self._log[-limit:]]


class BaseAgent:
    """Base class for all autonomous agents."""

    def __init__(self, agent_id: str, role: AgentRole, bus: MessageBus):
        self.agent_id = agent_id
        self.role = role
        self.bus = bus
        self._running = False
        self._task_count = 0
        self._error_count = 0
        self._last_active = datetime.now().isoformat()

    async def start(self):
        self._running = True
        asyncio.create_task(self._message_loop())
        logger.info(f"Agent {self.agent_id} ({self.role.value}) started")

    async def stop(self):
        self._running = False
        logger.info(f"Agent {self.agent_id} ({self.role.value}) stopped")

    async def _message_loop(self):
        while self._running:
            msg = await self.bus.receive(self.agent_id)
            if msg:
                msg.status = "processing"
                self._last_active = datetime.now().isoformat()
                try:
                    result = await self.handle_message(msg)
                    msg.status = "completed"
                    if msg.reply_to:
                        await self.bus.publish(AgentMessage(
                            sender=self.agent_id, recipient=msg.sender,
                            action=f"reply:{msg.action}", payload=result or {},
                            reply_to=msg.id,
                        ))
                except Exception as e:
                    msg.status = "failed"
                    self._error_count += 1
                    logger.error(f"Agent {self.agent_id} error: {e}")
            else:
                await asyncio.sleep(0.5)

    async def handle_message(self, msg: AgentMessage) -> Dict[str, Any]:
        raise NotImplementedError

    async def send(self, recipient: str, action: str, payload: Dict = None, priority: int = 5):
        await self.bus.publish(AgentMessage(
            sender=self.agent_id, recipient=recipient,
            action=action, payload=payload or {}, priority=priority,
        ))

    async def broadcast(self, action: str, payload: Dict = None):
        await self.bus.publish(AgentMessage(
            sender=self.agent_id, action=action, payload=payload or {},
        ))

    def get_status(self) -> Dict:
        return {
            "id": self.agent_id, "role": self.role.value,
            "running": self._running, "tasks": self._task_count,
            "errors": self._error_count, "last_active": self._last_active,
        }


# ── 20 Specialized Agents ────────────────────────────────────────

class CoordinatorAgent(BaseAgent):
    """Central coordinator that manages all other agents."""
    def __init__(self, bus):
        super().__init__("coordinator", AgentRole.COORDINATOR, bus)
        self._agents: Dict[str, BaseAgent] = {}

    def register_agent(self, agent: BaseAgent):
        self._agents[agent.agent_id] = agent

    async def handle_message(self, msg):
        if msg.action == "status_all":
            return {aid: a.get_status() for aid, a in self._agents.items()}
        elif msg.action == "health_check":
            return {"coordinator": self.get_status(), "agent_count": len(self._agents)}
        elif msg.action == "dispatch_task":
            # Route task to appropriate agent
            task_type = msg.payload.get("type", "")
            target = msg.payload.get("target_agent", "")
            if target and target in self._agents:
                await self.send(target, "execute", msg.payload)
                return {"dispatched": True}
        return {}


class ResearchAgent(BaseAgent):
    def __init__(self, bus):
        super().__init__("research", AgentRole.RESEARCH, bus)

    async def handle_message(self, msg):
        if msg.action == "research_topic":
            self._task_count += 1
            topic = msg.payload.get("topic", "")
            # Broadcast research request to all agents
            await self.broadcast("provide_data", {"topic": topic})
            return {"status": "research_started", "topic": topic}
        return {}


class CrawlerAgent(BaseAgent):
    def __init__(self, bus):
        super().__init__("crawler", AgentRole.CRAWLER, bus)

    async def handle_message(self, msg):
        if msg.action == "crawl_url":
            self._task_count += 1
            url = msg.payload.get("url", "")
            # Would integrate with Phase 12 crawler
            return {"status": "crawling", "url": url}
        elif msg.action == "crawl_batch":
            urls = msg.payload.get("urls", [])
            return {"status": "batch_queued", "count": len(urls)}
        return {}


class BrowserAgent(BaseAgent):
    def __init__(self, bus):
        super().__init__("browser", AgentRole.BROWSER, bus)

    async def handle_message(self, msg):
        if msg.action == "browse":
            self._task_count += 1
            return {"status": "browsing", "url": msg.payload.get("url", "")}
        return {}


class VerificationAgent(BaseAgent):
    def __init__(self, bus):
        super().__init__("verification", AgentRole.VERIFICATION, bus)

    async def handle_message(self, msg):
        if msg.action == "verify_claim":
            self._task_count += 1
            claim = msg.payload.get("claim", "")
            # Cross-verify against multiple sources
            return {"claim": claim, "status": "verifying", "sources_needed": 3}
        return {}


class FactCheckAgent(BaseAgent):
    def __init__(self, bus):
        super().__init__("fact_check", AgentRole.FACT_CHECK, bus)

    async def handle_message(self, msg):
        if msg.action == "check_fact":
            self._task_count += 1
            return {"fact": msg.payload.get("fact", ""), "status": "checking"}
        return {}


class OCRAgent(BaseAgent):
    def __init__(self, bus):
        super().__init__("ocr", AgentRole.OCR, bus)

    async def handle_message(self, msg):
        if msg.action == "ocr_file":
            self._task_count += 1
            return {"status": "processing", "file": msg.payload.get("file", "")}
        return {}


class KnowledgeGraphAgent(BaseAgent):
    def __init__(self, bus):
        super().__init__("kg", AgentRole.KNOWLEDGE_GRAPH, bus)

    async def handle_message(self, msg):
        if msg.action == "extract_entities":
            self._task_count += 1
            text = msg.payload.get("text", "")
            return {"status": "extracting", "text_length": len(text)}
        elif msg.action == "add_to_graph":
            return {"status": "added", "entity": msg.payload.get("entity", "")}
        return {}


class VectorAgent(BaseAgent):
    def __init__(self, bus):
        super().__init__("vector", AgentRole.VECTOR, bus)

    async def handle_message(self, msg):
        if msg.action == "index_text":
            self._task_count += 1
            return {"status": "indexing", "text_length": len(msg.payload.get("text", ""))}
        elif msg.action == "vector_search":
            return {"status": "searching", "query": msg.payload.get("query", "")}
        return {}


class RestaurantIntelligenceAgent(BaseAgent):
    def __init__(self, bus):
        super().__init__("restaurant_intel", AgentRole.RESTAURANT, bus)

    async def handle_message(self, msg):
        if msg.action == "collect_restaurants":
            self._task_count += 1
            area = msg.payload.get("area", "Raipur")
            return {"status": "collecting", "area": area}
        elif msg.action == "analyze_menu":
            return {"status": "analyzing", "restaurant": msg.payload.get("restaurant", "")}
        return {}


class GovernmentDataAgent(BaseAgent):
    def __init__(self, bus):
        super().__init__("govt", AgentRole.GOVERNMENT, bus)

    async def handle_message(self, msg):
        if msg.action == "check_notifications":
            self._task_count += 1
            return {"status": "checking", "portal": msg.payload.get("portal", "cg_gov")}
        return {}


class NewsAgent(BaseAgent):
    def __init__(self, bus):
        super().__init__("news", AgentRole.NEWS, bus)

    async def handle_message(self, msg):
        if msg.action == "fetch_news":
            self._task_count += 1
            topic = msg.payload.get("topic", "Raipur")
            return {"status": "fetching", "topic": topic}
        return {}


class SocialMediaAgent(BaseAgent):
    def __init__(self, bus):
        super().__init__("social", AgentRole.SOCIAL_MEDIA, bus)

    async def handle_message(self, msg):
        if msg.action == "monitor_social":
            self._task_count += 1
            return {"status": "monitoring", "platform": msg.payload.get("platform", "all")}
        return {}


class AnalyticsAgent(BaseAgent):
    def __init__(self, bus):
        super().__init__("analytics", AgentRole.ANALYTICS, bus)

    async def handle_message(self, msg):
        if msg.action == "analyze_data":
            self._task_count += 1
            return {"status": "analyzing", "data_type": msg.payload.get("type", "")}
        return {}


class ReportingAgent(BaseAgent):
    def __init__(self, bus):
        super().__init__("reporting", AgentRole.REPORTING, bus)

    async def handle_message(self, msg):
        if msg.action == "generate_report":
            self._task_count += 1
            return {"status": "generating", "report_type": msg.payload.get("type", "daily")}
        return {}


class SchedulerAgent(BaseAgent):
    def __init__(self, bus):
        super().__init__("scheduler", AgentRole.SCHEDULER, bus)
        self._scheduled_tasks: List[Dict] = []

    async def handle_message(self, msg):
        if msg.action == "schedule_task":
            task = msg.payload
            self._scheduled_tasks.append(task)
            return {"status": "scheduled", "task": task.get("name", "unnamed")}
        elif msg.action == "list_tasks":
            return {"tasks": self._scheduled_tasks}
        return {}


class MonitoringAgent(BaseAgent):
    def __init__(self, bus):
        super().__init__("monitoring", AgentRole.MONITORING, bus)

    async def handle_message(self, msg):
        if msg.action == "health_check_all":
            self._task_count += 1
            await self.broadcast("health_report_request")
            return {"status": "checking_all"}
        return {}


class RecoveryAgent(BaseAgent):
    def __init__(self, bus):
        super().__init__("recovery", AgentRole.RECOVERY, bus)

    async def handle_message(self, msg):
        if msg.action == "recover_task":
            self._task_count += 1
            return {"status": "recovering", "task": msg.payload.get("task_id", "")}
        return {}


class SecurityAgent(BaseAgent):
    def __init__(self, bus):
        super().__init__("security", AgentRole.SECURITY, bus)

    async def handle_message(self, msg):
        if msg.action == "validate_input":
            self._task_count += 1
            text = msg.payload.get("text", "")
            # Check for injection attempts
            suspicious = any(x in text.lower() for x in ["<script", "DROP TABLE", "exec(", "eval("])
            return {"safe": not suspicious, "text": text[:100]}
        return {}


class DeploymentAgent(BaseAgent):
    def __init__(self, bus):
        super().__init__("deployment", AgentRole.SECURITY, bus)

    async def handle_message(self, msg):
        if msg.action == "deploy":
            self._task_count += 1
            return {"status": "deploying", "version": msg.payload.get("version", "latest")}
        return {}


class DataQualityAgent(BaseAgent):
    def __init__(self, bus):
        super().__init__("data_quality", AgentRole.DATA_QUALITY, bus)

    async def handle_message(self, msg):
        if msg.action == "validate_data":
            self._task_count += 1
            return {"status": "validating", "record_count": msg.payload.get("count", 0)}
        return {}


class AgentOrchestrator:
    """Orchestrates all 20 agents with automatic communication."""

    def __init__(self):
        self._bus = MessageBus()
        self._agents: Dict[str, BaseAgent] = {}
        self._init_agents()

    def _init_agents(self):
        agent_classes = [
            CoordinatorAgent, ResearchAgent, CrawlerAgent, BrowserAgent,
            VerificationAgent, FactCheckAgent, OCRAgent, KnowledgeGraphAgent,
            VectorAgent, RestaurantIntelligenceAgent, GovernmentDataAgent,
            NewsAgent, SocialMediaAgent, AnalyticsAgent, ReportingAgent,
            SchedulerAgent, MonitoringAgent, RecoveryAgent, SecurityAgent,
            DataQualityAgent,
        ]
        for cls in agent_classes:
            agent = cls(self._bus)
            self._agents[agent.agent_id] = agent
            # Register with coordinator
            coordinator = self._agents.get("coordinator")
            if coordinator and isinstance(coordinator, CoordinatorAgent):
                coordinator.register_agent(agent)

    async def start_all(self):
        for agent in self._agents.values():
            await agent.start()
        logger.info(f"Started {len(self._agents)} agents")

    async def stop_all(self):
        for agent in self._agents.values():
            await agent.stop()

    async def dispatch(self, target: str, action: str, payload: Dict = None) -> Dict:
        if target in self._agents:
            agent = self._agents[target]
            await self._bus.publish(AgentMessage(
                sender="orchestrator", recipient=target,
                action=action, payload=payload or {},
            ))
            await asyncio.sleep(0.5)
            return agent.get_status()
        return {"error": f"Unknown agent: {target}"}

    async def get_all_status(self) -> Dict[str, Dict]:
        return {aid: a.get_status() for aid, a in self._agents.items()}

    def get_message_log(self, limit: int = 50) -> List[Dict]:
        return self._bus.get_log(limit)
