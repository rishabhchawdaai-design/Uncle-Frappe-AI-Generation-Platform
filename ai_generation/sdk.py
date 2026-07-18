"""
SDK — Python SDK for the AI Generation Platform.
High-level API for consumers.
"""
import asyncio
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class UncleFrappeAI:
    """
    Uncle Frappe AI SDK — unified interface for image/video generation.

    Usage:
        ai = UncleFrappeAI()
        result = await ai.generate("a beautiful sunset over Raipur")
        result = await ai.generate_image("coffee cup", style="product_photo")
        result = await ai.generate_video("city timelapse")
        results = await ai.batch_generate(["prompt1", "prompt2"])
    """

    def __init__(self, config=None):
        self.config = config or {}
        self._generation_manager = None
        self._prompt_engine = None
        self._quality_engine = None
        self._workflow_engine = None
        self._benchmark_engine = None
        self._asset_intelligence = None
        self._research_agent = None
        # Phase 11 — Media Intelligence & Cinematic Production
        self._media_intelligence = None
        self._image_editing = None
        self._video_generation = None
        self._cinematic_workflow = None
        self._character_manager = None
        self._project_manager = None
        self._cinema_benchmark = None
        self._provider_intelligence = None
        self._capability_matrix = None
        self._agent_planner = None
        # Phase 13 — Agent-Native Remote Execution
        self._agent_interface = None
        self._execution_engine = None
        self._auto_router = None
        self._capability_registry = None
        self._provider_discovery_engine = None
        self._provider_verifier = None
        self._health_monitor = None
        self._remote_endpoint_manager = None
        # Phase 14 — AIG-OS Autonomous Agents
        self._aigos_orchestrator = None
        self._knowledge_graph = None
        self._dynamic_adapter_manager = None
        self._benchmark_lab = None

    @property
    def generation_manager(self):
        if self._generation_manager is None:
            from .generation_manager import GenerationManager
            self._generation_manager = GenerationManager(self.config)
        return self._generation_manager

    @property
    def prompt_engine(self):
        if self._prompt_engine is None:
            from .prompt_engine import PromptEngine
            self._prompt_engine = PromptEngine(self.config)
        return self._prompt_engine

    @property
    def quality_engine(self):
        if self._quality_engine is None:
            from .quality_engine import QualityEngine
            self._quality_engine = QualityEngine()
        return self._quality_engine

    @property
    def workflow_engine(self):
        if self._workflow_engine is None:
            from .workflow_engine import WorkflowEngine
            self._workflow_engine = WorkflowEngine(self.generation_manager, self.prompt_engine)
        return self._workflow_engine

    @property
    def benchmark_engine(self):
        if self._benchmark_engine is None:
            from .benchmark_engine import BenchmarkEngine
            self._benchmark_engine = BenchmarkEngine()
        return self._benchmark_engine

    @property
    def asset_intelligence(self):
        if self._asset_intelligence is None:
            from .asset_intelligence import AssetIntelligence
            self._asset_intelligence = AssetIntelligence(
                self.config.get("output_dir", "./output/assets")
            )
        return self._asset_intelligence

    @property
    def research_agent(self):
        if self._research_agent is None:
            from .research_agent import ResearchAgent
            self._research_agent = ResearchAgent()
        return self._research_agent

    # ── Phase 11 — Media Intelligence & Cinematic Production ──

    @property
    def media_intelligence(self):
        if self._media_intelligence is None:
            from .media_intelligence import MediaIntelligenceEngine
            self._media_intelligence = MediaIntelligenceEngine(self.config)
        return self._media_intelligence

    @property
    def image_editing(self):
        if self._image_editing is None:
            from .image_editing import ImageEditingEngine
            self._image_editing = ImageEditingEngine(self.config)
        return self._image_editing

    @property
    def video_generation(self):
        if self._video_generation is None:
            from .video_generation import VideoGenerationLayer
            self._video_generation = VideoGenerationLayer(self.config)
        return self._video_generation

    @property
    def cinematic_workflow(self):
        if self._cinematic_workflow is None:
            from .cinematic_workflow import CinematicWorkflowEngine
            self._cinematic_workflow = CinematicWorkflowEngine(self.generation_manager, self.prompt_engine)
        return self._cinematic_workflow

    @property
    def character_manager(self):
        if self._character_manager is None:
            from .character_manager import CharacterManager
            self._character_manager = CharacterManager()
        return self._character_manager

    @property
    def project_manager(self):
        if self._project_manager is None:
            from .project_manager import ProjectManager
            self._project_manager = ProjectManager()
        return self._project_manager

    @property
    def cinema_benchmark(self):
        if self._cinema_benchmark is None:
            from .cinema_benchmark import CinemaBenchmarkEngine
            self._cinema_benchmark = CinemaBenchmarkEngine()
        return self._cinema_benchmark

    @property
    def provider_intelligence(self):
        if self._provider_intelligence is None:
            from .provider_intelligence import ProviderIntelligenceEngine
            self._provider_intelligence = ProviderIntelligenceEngine()
        return self._provider_intelligence

    @property
    def capability_matrix(self):
        if self._capability_matrix is None:
            from .capability_matrix import CapabilityMatrix
            self._capability_matrix = CapabilityMatrix()
        return self._capability_matrix

    @property
    def agent_planner(self):
        if self._agent_planner is None:
            from .agent_planner import AgentPlanner
            self._agent_planner = AgentPlanner(
                self.media_intelligence, self.capability_matrix,
                self.prompt_engine, self.project_manager,
            )
        return self._agent_planner

    # ── Phase 13 — Agent-Native Remote Execution ──

    @property
    def agent_interface(self):
        if not hasattr(self, '_agent_interface'):
            self._agent_interface = None
        if self._agent_interface is None:
            from .agent_interface import AgentInterface
            self._agent_interface = AgentInterface(self.config)
        return self._agent_interface

    @property
    def execution_engine(self):
        return self.agent_interface.execution_engine

    @property
    def auto_router(self):
        return self.agent_interface.auto_router

    @property
    def capability_registry(self):
        return self.agent_interface.capability_registry

    @property
    def provider_discovery_engine(self):
        return self.agent_interface.provider_discovery

    @property
    def provider_verifier(self):
        return self.agent_interface.provider_verifier

    @property
    def health_monitor(self):
        return self.agent_interface.health_monitor

    @property
    def remote_endpoint_manager(self):
        return self.agent_interface.remote_endpoints

    # ── Phase 14 — AIG-OS Autonomous Agents ──

    @property
    def aigos(self):
        if self._aigos_orchestrator is None:
            from .agents.agent_registry import AgentOrchestrator
            self._aigos_orchestrator = AgentOrchestrator(self.config)
            self._aigos_orchestrator.initialize()
        return self._aigos_orchestrator

    @property
    def knowledge_graph(self):
        if self._knowledge_graph is None:
            from .knowledge_graph import KnowledgeGraph
            self._knowledge_graph = KnowledgeGraph()
        return self._knowledge_graph

    @property
    def dynamic_adapter_manager(self):
        if self._dynamic_adapter_manager is None:
            from .dynamic_adapter import DynamicAdapterManager
            self._dynamic_adapter_manager = DynamicAdapterManager()
        return self._dynamic_adapter_manager

    @property
    def benchmark_lab(self):
        if self._benchmark_lab is None:
            from .benchmark_lab import BenchmarkLab
            self._benchmark_lab = BenchmarkLab()
        return self._benchmark_lab

    async def generate(self, prompt, style="", quality="high", enhance_prompt=True,
                       provider=None, width=1024, height=1024, seed=None, **kwargs):
        if enhance_prompt:
            enhancement = self.prompt_engine.enhance(prompt, style=style, quality=quality)
            final_prompt = enhancement.enhanced
            negative = enhancement.negative_prompt
        else:
            final_prompt = prompt
            negative = kwargs.get("negative_prompt", "")

        from .generation_manager import GenerationRequest
        from .providers.base import ProviderType
        request = GenerationRequest(
            prompt=final_prompt, provider_type=ProviderType.IMAGE,
            preferred_provider=provider, width=width, height=height,
            negative_prompt=negative, seed=seed, style=style, **kwargs,
        )
        result = await self.generation_manager.generate(request)
        if result.success:
            report = self.quality_engine.evaluate_generation(result, prompt, style)
            result.metadata["quality_score"] = report.overall_score
        return result

    async def generate_image(self, prompt, **kwargs):
        return await self.generate(prompt, **kwargs)

    async def generate_video(self, prompt, duration_secs=4.0, **kwargs):
        from .generation_manager import GenerationRequest
        from .providers.base import ProviderType
        request = GenerationRequest(
            prompt=prompt, provider_type=ProviderType.VIDEO,
            duration_secs=duration_secs, **kwargs,
        )
        return await self.generation_manager.generate(request)

    async def batch_generate(self, prompts, concurrency=3, **kwargs):
        return await self.generation_manager.batch_generate(
            prompts, concurrency=concurrency, **kwargs,
        )

    def enhance_prompt(self, prompt, style="", quality="high"):
        return self.prompt_engine.enhance(prompt, style=style, quality=quality)

    def analyze_prompt(self, prompt):
        return self.prompt_engine.analyze_prompt(prompt)

    def create_workflow(self, name, steps, **kwargs):
        return self.workflow_engine.create_workflow(name, steps, **kwargs)

    async def execute_workflow(self, workflow_id, context=None):
        return await self.workflow_engine.execute(workflow_id, context)

    def list_providers(self):
        return self.generation_manager.list_providers()

    def list_templates(self):
        return self.prompt_engine.list_templates()

    def list_styles(self):
        from .prompt_engine import STYLE_PRESETS
        return list(STYLE_PRESETS.keys())

    def get_stats(self):
        return {
            "generation": self.generation_manager.get_stats(),
            "prompts": self.prompt_engine.get_stats(),
            "quality": self.quality_engine.get_stats(),
            "workflows": self.workflow_engine.get_stats(),
            "benchmarks": self.benchmark_engine.get_stats(),
            "assets": self.asset_intelligence.get_stats(),
            "research": self.research_agent.get_stats(),
            "media_intelligence": {"total_analyses": len(getattr(self.media_intelligence, '_history', []))},
            "image_editing": self.image_editing.get_stats(),
            "video_generation": self.video_generation.get_stats(),
            "cinematic_workflow": self.cinematic_workflow.get_stats(),
            "characters": self.character_manager.get_stats(),
            "projects": self.project_manager.get_stats(),
            "cinema_benchmark": self.cinema_benchmark.get_stats(),
            "provider_intelligence": self.provider_intelligence.get_stats(),
            "capability_matrix": self.capability_matrix.get_stats(),
            "agent_planner": self.agent_planner.get_stats(),
            "execution_engine": self.execution_engine.get_stats(),
            "capability_registry": self.capability_registry.get_stats(),
            "provider_discovery": self.provider_discovery_engine.get_stats(),
            "health_monitor": self.health_monitor.get_stats(),
            "auto_router": self.auto_router.get_stats(),
        }

    # ── Phase 11 Convenience Methods ──

    def analyze_request(self, prompt, **kwargs):
        return self.media_intelligence.analyze_request(prompt, **kwargs)

    async def edit_image(self, operation, input_path, prompt="", **kwargs):
        return await self.image_editing.edit(operation, input_path, prompt=prompt, **kwargs)

    async def img2img(self, input_path, prompt, **kwargs):
        return await self.image_editing.img2img(input_path, prompt, **kwargs)

    async def inpaint(self, input_path, mask_path, prompt, **kwargs):
        return await self.image_editing.inpaint(input_path, mask_path, prompt, **kwargs)

    async def remove_background(self, input_path, **kwargs):
        return await self.image_editing.remove_background(input_path, **kwargs)

    async def replace_background(self, input_path, prompt, **kwargs):
        return await self.image_editing.replace_background(input_path, prompt, **kwargs)

    async def style_transfer(self, input_path, prompt, **kwargs):
        return await self.image_editing.style_transfer(input_path, prompt, **kwargs)

    async def upscale_image(self, input_path, **kwargs):
        return await self.image_editing.upscale(input_path, **kwargs)

    async def text_to_video(self, prompt, **kwargs):
        return await self.video_generation.text_to_video(prompt, **kwargs)

    async def image_to_video(self, image_path, prompt="", **kwargs):
        return await self.video_generation.image_to_video(image_path, prompt, **kwargs)

    def create_cinematic_pipeline(self, template="full_cinematic", name="", **kwargs):
        return self.cinematic_workflow.create_pipeline(template=template, name=name, **kwargs)

    def create_character(self, name, description="", **kwargs):
        return self.character_manager.create_character(name, description, **kwargs)

    def create_project(self, name, description="", **kwargs):
        return self.project_manager.create_project(name, description, **kwargs)

    def plan_request(self, request, **kwargs):
        return self.agent_planner.plan(request, **kwargs)

    def get_capability_matrix(self):
        return self.capability_matrix.get_stats()

    def get_provider_recommendations(self):
        return self.provider_intelligence.get_recommendations()

    def get_cinema_dimensions(self):
        return self.cinema_benchmark.list_dimensions()

    # ── Phase 13 Convenience Methods ──

    async def agent_generate(self, request: str, **kwargs) -> Dict[str, Any]:
        return await self.agent_interface.generate_image(request, **kwargs)

    async def agent_edit(self, image_path: str, prompt: str = "", **kwargs) -> Dict[str, Any]:
        return await self.agent_interface.edit_image(image_path, prompt, **kwargs)

    async def agent_video(self, request: str, **kwargs) -> Dict[str, Any]:
        return await self.agent_interface.generate_video(request, **kwargs)

    async def agent_health_check(self) -> Dict[str, Any]:
        return await self.agent_interface.health_check()

    def agent_classify(self, request: str) -> Dict[str, Any]:
        return self.agent_interface.classify_request(request)

    def agent_providers(self) -> List[Dict[str, Any]]:
        return self.agent_interface.get_available_providers()

    def agent_add_remote_endpoint(self, name: str, url: str, **kwargs) -> Dict[str, Any]:
        return self.agent_interface.add_remote_endpoint(name, url, **kwargs)

    def agent_capability_matrix(self) -> Dict[str, Any]:
        return self.agent_interface.get_capability_matrix()

    # ── Phase 14 — AIG-OS Convenience Methods ──

    def aigos_execute(self, request: str) -> Dict[str, Any]:
        return self.aigos.execute_request(request)

    def aigos_status(self) -> Dict[str, Any]:
        return self.aigos.get_status()

    def aigos_agents(self) -> List[Dict[str, Any]]:
        return self.aigos.registry.list_agents()

    def aigos_knowledge_query(self, query: str, domain: str = "") -> Dict[str, Any]:
        from .agents.base_agent import AgentTask
        task = AgentTask(task_type="search", payload={"query": query, "domain": domain})
        agent = self.aigos.registry.get_agent("knowledge")
        return agent.execute(task).data

    def aigos_benchmark_leaderboard(self) -> List[Dict[str, Any]]:
        from .agents.base_agent import AgentTask
        task = AgentTask(task_type="get_leaderboard")
        agent = self.aigos.registry.get_agent("benchmark")
        return agent.execute(task).data.get("leaderboard", [])

    def aigos_providers(self) -> List[Dict[str, Any]]:
        from .agents.base_agent import AgentTask
        task = AgentTask(task_type="get_providers")
        agent = self.aigos.registry.get_agent("research")
        return agent.execute(task).data.get("providers", [])

    def aigos_endpoints(self) -> List[Dict[str, Any]]:
        from .agents.base_agent import AgentTask
        task = AgentTask(task_type="get_endpoints")
        agent = self.aigos.registry.get_agent("discovery")
        return agent.execute(task).data.get("endpoints", [])
