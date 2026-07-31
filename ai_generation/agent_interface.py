"""
Agent Interface — simple interface for AI agents.
The agent calls one interface; the platform decides how to fulfill the request.
"""
import asyncio
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class AgentInterface:
    """
    Simple interface for AI agents.

    Usage:
        agent = AgentInterface()
        result = await agent.generate_image("a beautiful sunset")
        result = await agent.edit_image("/path/to/image.png", "remove background")
        result = await agent.generate_video("a cinematic scene")
        result = await agent.generate_audio("upbeat music for a cafe ad")
        result = await agent.chat("explain latent MoE", strategy="negotiate")
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._auto_router = None
        self._execution_engine = None
        self._capability_registry = None
        self._provider_discovery = None
        self._provider_verifier = None
        self._health_monitor = None
        self._remote_endpoints = None
        self._kimi_k3 = None
        self._event_bus = None

    @property
    def auto_router(self):
        if self._auto_router is None:
            from .auto_router import AutoRouter
            self._auto_router = AutoRouter(
                capability_registry=self.capability_registry,
                provider_discovery=self.provider_discovery,
                execution_engine=self.execution_engine,
                provider_verifier=self.provider_verifier,
            )
        return self._auto_router

    @property
    def execution_engine(self):
        if self._execution_engine is None:
            from .execution_engine import ExecutionEngine
            self._execution_engine = ExecutionEngine(self.config)
            self._execution_engine.initialize()
        return self._execution_engine

    @property
    def capability_registry(self):
        if self._capability_registry is None:
            from .capability_registry import CapabilityRegistry
            self._capability_registry = CapabilityRegistry()
        return self._capability_registry

    @property
    def provider_discovery(self):
        if self._provider_discovery is None:
            from .provider_discovery import ProviderDiscoveryEngine
            self._provider_discovery = ProviderDiscoveryEngine()
        return self._provider_discovery

    @property
    def provider_verifier(self):
        if self._provider_verifier is None:
            from .provider_verifier import ProviderVerifier
            self._provider_verifier = ProviderVerifier()
        return self._provider_verifier

    @property
    def health_monitor(self):
        if self._health_monitor is None:
            from .health_monitor import HealthMonitor
            self._health_monitor = HealthMonitor()
        return self._health_monitor

    @property
    def remote_endpoints(self):
        if self._remote_endpoints is None:
            from .remote_endpoints import RemoteEndpointManager
            self._remote_endpoints = RemoteEndpointManager()
        return self._remote_endpoints

    @property
    def event_bus(self):
        """Platform Event Bus shared by agent-facing subsystems."""
        if self._event_bus is None:
            from .event_bus import EventBus
            self._event_bus = EventBus(self.config)
        return self._event_bus

    @property
    def kimi_k3(self):
        """Kimi K3 manager — cloud API + self-hosted vLLM/SGLang execution."""
        if self._kimi_k3 is None:
            from .kimi_k3 import KimiK3Manager
            self._kimi_k3 = KimiK3Manager(self.config, event_bus=self.event_bus)
        return self._kimi_k3

    async def generate_image(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Generate an image from a prompt. Platform decides best provider."""
        result = await self.auto_router.plan_and_execute(prompt, **kwargs)
        return result

    async def edit_image(self, image_path: str, prompt: str = "", **kwargs) -> Dict[str, Any]:
        """Edit an image. Platform decides best provider and operation."""
        task_desc = f"Edit image: {prompt}" if prompt else f"Edit image at {image_path}"
        result = await self.auto_router.plan_and_execute(
            task_desc, input_path=image_path, prompt=prompt, **kwargs,
        )
        return result

    async def generate_video(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Generate a video. Platform decides best provider."""
        result = await self.auto_router.plan_and_execute(prompt, **kwargs)
        return result

    async def generate_audio(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Generate audio. Platform decides best provider."""
        result = await self.auto_router.plan_and_execute(prompt, **kwargs)
        return result

    async def chat(self, prompt: str, provider: str = "auto",
                  strategy: str = "auto", system_prompt: str = "",
                  images: Optional[List[str]] = None,
                  history: Optional[List[Dict[str, Any]]] = None,
                  reasoning_effort: str = "max",
                  max_tokens: Optional[int] = None,
                  temperature: Optional[float] = None,
                  top_p: Optional[float] = None,
                  timeout_secs: float = 120.0) -> Dict[str, Any]:
        """Chat with Kimi K3 through the best available execution path.

        provider: "auto" | "kimi_k3_cloud" | "kimi_k3_vllm" | "kimi_k3_sglang"
        strategy: "auto" (priority order + fallback) or "negotiate"
        (Negotiation Engine selects the optimal official path).
        """
        if strategy == "negotiate":
            result = await self.kimi_k3.chat_negotiated(
                prompt, system_prompt=system_prompt,
                reasoning_effort=reasoning_effort,
            )
        else:
            result = await self.kimi_k3.chat(
                prompt, provider=provider, system_prompt=system_prompt,
                images=images, history=history,
                reasoning_effort=reasoning_effort, max_tokens=max_tokens,
                temperature=temperature, top_p=top_p, timeout_secs=timeout_secs,
            )
        return result.to_dict()

    def kimi_k3_info(self) -> Dict[str, Any]:
        """Return the canonical Kimi K3 specification and supported paths."""
        return self.kimi_k3.info()

    async def kimi_k3_health(self) -> Dict[str, Any]:
        """Health-check every configured Kimi K3 execution path."""
        return await self.kimi_k3.health()

    async def kimi_k3_benchmark(self, prompt: str, runs: int = 2,
                                provider: str = "auto",
                                reasoning_effort: str = "low") -> Dict[str, Any]:
        """Benchmark Kimi K3 chat latency and quality."""
        return await self.kimi_k3.benchmark(
            prompt, runs=runs, provider=provider,
            reasoning_effort=reasoning_effort,
        )

    def get_available_providers(self) -> List[Dict[str, Any]]:
        """List all available providers across all layers."""
        return self.execution_engine.get_all_endpoints()

    def get_healthy_providers(self) -> List[str]:
        """List currently healthy providers."""
        return self.health_monitor.get_healthy_providers()

    def add_remote_endpoint(self, name: str, url: str, **kwargs) -> Dict[str, Any]:
        """Add a user-configured remote endpoint."""
        ep = self.remote_endpoints.add_endpoint(name, url, **kwargs)
        return ep.to_dict()

    def get_capability_matrix(self) -> Dict[str, Any]:
        """Get the full capability matrix."""
        return self.capability_registry.get_summary()

    def classify_request(self, request: str) -> Dict[str, Any]:
        """Classify a request and get routing decision."""
        decision = self.auto_router.classify_task(request)
        return decision.to_dict()

    def get_provider_recommendations(self) -> List[Dict[str, Any]]:
        """Get provider recommendations based on research."""
        return self.provider_discovery.get_recommendations()

    async def health_check(self) -> Dict[str, Any]:
        """Run health checks on all registered providers."""
        endpoints = {}
        for ep in self.execution_engine.get_all_endpoints():
            if ep.get("healthy", True):
                endpoints[ep["name"]] = ep.get("url", "")
        if endpoints:
            return await self.health_monitor.check_all(endpoints)
        return {"note": "No endpoints registered"}

    def get_stats(self) -> Dict[str, Any]:
        return {
            "execution_engine": self.execution_engine.get_stats(),
            "capability_registry": self.capability_registry.get_stats(),
            "provider_discovery": self.provider_discovery.get_stats(),
            "health_monitor": self.health_monitor.get_stats(),
            "remote_endpoints": self.remote_endpoints.get_stats(),
            "auto_router": self.auto_router.get_stats(),
            "kimi_k3": self.kimi_k3.get_stats(),
        }
