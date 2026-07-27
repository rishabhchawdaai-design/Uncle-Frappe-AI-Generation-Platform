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
        self._video_editing = None
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
        # Phase 16 — Audio Generation
        self._audio_generation = None
        self._voice_cloning = None
        self._music_generation = None
        self._audio_enhancement = None
        # Phase 17 — Decision Ledger
        self._decision_ledger = None
        # Phase 18 — Browser AI Inference Layer
        self._browser_ai = None
        # Phase 19 — Edge AI Runtime Detection
        self._edge_ai = None
        # Phase 20 — Plugin System Foundation
        self._plugin_system = None
        # Phase 21 — Observability Layer
        self._observability = None
        # Phase 22 — Search Systems
        self._search_systems = None
        self._search_backends = None
        # Phase 23 — OCR & Document Intelligence
        self._ocr_engine = None
        self._document_intelligence = None
        # Phase 24 — 3D Generation
        self._generation_3d = None
        # Phase 25 — Benchmark Regression Detection
        self._regression_detector = None
        # Phase 26 — Capability Graph
        self._capability_graph = None
        # Phase 27 — Security Layer
        self._security_manager = None
        # Phase 28 — Failure Recovery System
        self._failure_recovery = None
        # Phase 29 — Local Runtime Integrations
        self._local_runtimes = None
        # Phase 30 — Security Crypto Layer
        self._encryption_at_rest = None
        # Phase 31 — In-Memory Event Bus
        self._event_bus = None
        self._event_kernel = None
        # Phase 32 — OpenTelemetry Export
        self._otel_exporter = None
        self._encryption_in_transit = None
        self._model_security = None
        # Phase 15 — Negotiation Engine & Supervisor Tree
        self._negotiation_engine = None
        self._supervisor = None

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
    def video_editing(self):
        if self._video_editing is None:
            from .video_editing import VideoEditingEngine
            self._video_editing = VideoEditingEngine(self.config)
        return self._video_editing

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

    @property
    def decision_ledger(self):
        if self._decision_ledger is None:
            from .decision_ledger import DecisionLedger
            self._decision_ledger = DecisionLedger(self.config)
        return self._decision_ledger

    @property
    def audio_generation(self):
        if self._audio_generation is None:
            from .audio_generation import AudioGenerationEngine
            self._audio_generation = AudioGenerationEngine(self.config)
        return self._audio_generation

    @property
    def voice_cloning(self):
        if self._voice_cloning is None:
            from .voice_cloning import VoiceCloningEngine
            self._voice_cloning = VoiceCloningEngine(self.config)
        return self._voice_cloning

    @property
    def music_generation(self):
        if self._music_generation is None:
            from .music_generation import MusicGenerationEngine
            self._music_generation = MusicGenerationEngine(self.config)
        return self._music_generation

    @property
    def audio_enhancement(self):
        if self._audio_enhancement is None:
            from .audio_enhancement import AudioEnhancementEngine
            self._audio_enhancement = AudioEnhancementEngine(self.config)
        return self._audio_enhancement

    @property
    def negotiation_engine(self):
        if self._negotiation_engine is None:
            from .negotiation_engine import NegotiationEngine
            self._negotiation_engine = NegotiationEngine()
        return self._negotiation_engine

    @property
    def supervisor(self):
        if self._supervisor is None:
            from .supervisor import create_platform_supervisor
            self._supervisor = create_platform_supervisor()
        return self._supervisor

    @property
    def failure_recovery(self):
        if self._failure_recovery is None:
            from .failure_recovery import FailureRecoveryEngine
            self._failure_recovery = FailureRecoveryEngine(self.config)
        return self._failure_recovery

    @property
    def local_runtimes(self):
        if self._local_runtimes is None:
            from .local_runtimes import LocalRuntimeManager
            self._local_runtimes = LocalRuntimeManager(self.config)
        return self._local_runtimes

    @property
    def encryption_at_rest(self):
        if self._encryption_at_rest is None:
            from .security_crypto import EncryptionAtRest
            self._encryption_at_rest = EncryptionAtRest(self.config)
        return self._encryption_at_rest

    @property
    def encryption_in_transit(self):
        if self._encryption_in_transit is None:
            from .security_crypto import EncryptionInTransit
            self._encryption_in_transit = EncryptionInTransit(self.config)
        return self._encryption_in_transit

    @property
    def model_security(self):
        if self._model_security is None:
            from .security_crypto import ModelSecurity
            self._model_security = ModelSecurity(self.config)
        return self._model_security

    @property
    def event_bus(self):
        if self._event_bus is None:
            from .event_bus import EventBus
            self._event_bus = EventBus(self.config)
        return self._event_bus

    @property
    def event_kernel(self):
        if self._event_kernel is None:
            from .event_bus import EventDrivenKernel
            self._event_kernel = EventDrivenKernel(self.config)
        return self._event_kernel

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
            "video_editing": self.video_editing.get_stats(),
            "voice_cloning": self.voice_cloning.get_stats(),
            "music_generation": self.music_generation.get_stats(),
            "audio_enhancement": self.audio_enhancement.get_stats(),
            "document_intelligence": self.document_intelligence.get_stats(),
            "search_backends": self.search_backends.get_stats(),
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

    # ── Video Editing Convenience Methods ──

    async def trim_video(self, input_path, output_path="", start=0.0, end=0.0, **kwargs):
        return await self.video_editing.trim(input_path, output_path, start=start, end=end, **kwargs)

    async def concat_videos(self, input_paths, output_path="", **kwargs):
        return await self.video_editing.concat(input_paths, output_path, **kwargs)

    async def transition_videos(self, input_paths, output_path="", duration=1.0, **kwargs):
        return await self.video_editing.transition(input_paths, output_path, duration=duration, **kwargs)

    async def change_video_speed(self, input_path, output_path="", factor=1.0, **kwargs):
        return await self.video_editing.speed(input_path, output_path, factor=factor, **kwargs)

    async def interpolate_video_frames(self, input_path, output_path="", target_fps=60.0, **kwargs):
        return await self.video_editing.interpolate_frames(input_path, output_path, target_fps=target_fps, **kwargs)

    async def upscale_video(self, input_path, output_path="", scale_factor=2, **kwargs):
        return await self.video_editing.upscale(input_path, output_path, scale_factor=scale_factor, **kwargs)

    async def enhance_video(self, input_path, output_path="", **kwargs):
        return await self.video_editing.enhance(input_path, output_path, **kwargs)

    async def crop_video(self, input_path, output_path="", x=0, y=0, width=0, height=0, **kwargs):
        return await self.video_editing.crop(input_path, output_path, x=x, y=y, width=width, height=height, **kwargs)

    async def resize_video(self, input_path, output_path="", width=0, height=0, **kwargs):
        return await self.video_editing.resize(input_path, output_path, width=width, height=height, **kwargs)

    async def watermark_video(self, input_path, output_path="", text="", position="top_right", **kwargs):
        return await self.video_editing.watermark(input_path, output_path, text=text, position=position, **kwargs)

    async def extract_video_audio(self, input_path, output_path="", **kwargs):
        return await self.video_editing.extract_audio(input_path, output_path, **kwargs)

    async def reverse_video(self, input_path, output_path="", **kwargs):
        from .video_editing import VideoEditOperation
        return await self.video_editing.execute(VideoEditOperation.REVERSE, input_path=input_path, output_path=output_path, **kwargs)

    # ── Voice Cloning Convenience Methods ──

    async def clone_voice(self, reference_audio_path, text, language="en", provider=None, output_path="", **kwargs):
        return await self.voice_cloning.clone_voice(reference_audio_path, text, language=language, provider=provider, output_path=output_path, **kwargs)

    # ── Music Generation Convenience Methods ──

    async def generate_music(self, prompt, duration_secs=10.0, model="", output_path="", **kwargs):
        return await self.music_generation.generate_music(prompt=prompt, duration_secs=duration_secs, model=model, output_path=output_path, **kwargs)

    async def generate_sfx(self, prompt, duration_secs=5.0, output_path="", **kwargs):
        return await self.music_generation.generate_sfx(prompt=prompt, duration_secs=duration_secs, output_path=output_path, **kwargs)

    async def generate_melody(self, prompt, melody_path, duration_secs=10.0, output_path="", **kwargs):
        return await self.music_generation.generate_melody(prompt=prompt, melody_path=melody_path, duration_secs=duration_secs, output_path=output_path, **kwargs)

    # ── Audio Enhancement Convenience Methods ──

    async def denoise_audio(self, input_path, output_path="", **kwargs):
        return await self.audio_enhancement.denoise(input_path, output_path, **kwargs)

    async def normalize_audio(self, input_path, output_path="", **kwargs):
        return await self.audio_enhancement.normalize(input_path, output_path, **kwargs)

    async def convert_audio(self, input_path, output_path="", format="wav", **kwargs):
        return await self.audio_enhancement.convert_format(input_path, output_path, format=format, **kwargs)

    async def resample_audio(self, input_path, output_path="", sample_rate=44100, **kwargs):
        return await self.audio_enhancement.resample(input_path, output_path, sample_rate=sample_rate, **kwargs)

    async def compress_audio(self, input_path, output_path="", **kwargs):
        return await self.audio_enhancement.compress(input_path, output_path, **kwargs)

    async def mix_audio(self, input_paths, output_path="", weights=None, **kwargs):
        from .audio_enhancement import AudioEnhanceOperation
        return await self.audio_enhancement.execute(AudioEnhanceOperation.MIX, input_paths=input_paths, output_path=output_path, weights=weights, **kwargs)

    async def concat_audio(self, input_paths, output_path="", **kwargs):
        from .audio_enhancement import AudioEnhanceOperation
        return await self.audio_enhancement.execute(AudioEnhanceOperation.CONCAT, input_paths=input_paths, output_path=output_path, **kwargs)

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

    # ── Phase 15 — Negotiation Engine Convenience Methods ──

    @property
    def security(self):
        if self._security_manager is None:
            from .security import SecurityManager
            self._security_manager = SecurityManager(self.config)
        return self._security_manager

    @property
    def capability_graph(self):
        if self._capability_graph is None:
            from .capability_graph import CapabilityGraph
            self._capability_graph = CapabilityGraph(self.config)
        return self._capability_graph

    @property
    def regression_detector(self):
        if self._regression_detector is None:
            from .regression_detector import RegressionDetector
            self._regression_detector = RegressionDetector(self.config)
        return self._regression_detector

    @property
    def generation_3d(self):
        if self._generation_3d is None:
            from .generation_3d import Generation3DEngine
            self._generation_3d = Generation3DEngine(self.config)
        return self._generation_3d

    @property
    def ocr_engine(self):
        if self._ocr_engine is None:
            from .ocr_engine import OCREngine
            self._ocr_engine = OCREngine(self.config)
        return self._ocr_engine

    @property
    def document_intelligence(self):
        if self._document_intelligence is None:
            from .document_intelligence import DocumentIntelligenceEngine
            self._document_intelligence = DocumentIntelligenceEngine(self.config)
        return self._document_intelligence

    @property
    def search_systems(self):
        if self._search_systems is None:
            from .search_systems import SearchManager
            self._search_systems = SearchManager(self.config)
        return self._search_systems

    @property
    def search_backends(self):
        if self._search_backends is None:
            from .search_backends import SearchBackendManager
            self._search_backends = SearchBackendManager(self.config)
        return self._search_backends

    @property
    def observability(self):
        if self._observability is None:
            from .observability import ObservabilityManager
            self._observability = ObservabilityManager(self.config)
        return self._observability

    @property
    def plugin_system(self):
        if self._plugin_system is None:
            from .plugin_system import PluginSystem
            self._plugin_system = PluginSystem(self.config)
        return self._plugin_system

    @property
    def edge_ai(self):
        if self._edge_ai is None:
            from .edge_ai import EdgeAIManager
            self._edge_ai = EdgeAIManager(self.config)
        return self._edge_ai

    @property
    def browser_ai(self):
        if self._browser_ai is None:
            from .browser_ai import BrowserAIManager
            self._browser_ai = BrowserAIManager(self.config)
        return self._browser_ai

    def negotiate(self, request: str, **kwargs):
        """Negotiate optimal execution path for a request."""
        return self.auto_router.negotiate(request, **kwargs)

    def negotiate_with_candidates(self, request, candidates):
        """Negotiate with explicit candidate list."""
        return self.negotiation_engine.negotiate(request, candidates)

    def update_benchmark(self, provider, model, task_type, quality_score,
                         success_rate, latency_ms):
        """Update benchmark data for provider/model negotiation."""
        self.negotiation_engine.update_benchmark(
            provider, model, task_type, quality_score, success_rate, latency_ms
        )

    def get_negotiation_stats(self):
        """Get negotiation engine statistics."""
        return self.negotiation_engine.get_stats()

    def get_negotiation_history(self, limit=20):
        """Get recent negotiation history."""
        return self.negotiation_engine.get_history(limit)

    # ── Phase 15 — Supervisor Tree Convenience Methods ──

    def supervisor_stats(self):
        """Get platform supervisor statistics."""
        return self.supervisor.get_stats()

    def supervisor_workers(self):
        """Get all supervised worker states."""
        return self.supervisor.get_all_states()

    def supervisor_events(self, limit=50):
        """Get recent supervision events."""
        return self.supervisor.get_events(limit)

    def supervisor_crashed(self):
        """Get crashed workers."""
        return self.supervisor.get_crashed_workers()

    def supervisor_reset(self):
        """Reset all supervisor worker states."""
        self.supervisor.reset_all()

    # ── Phase 16 — Audio Generation Convenience Methods ──

    async def text_to_speech(self, text: str, voice: str = "default",
                             speed: float = 1.0, provider: str = None, **kwargs):
        """Generate speech from text."""
        return await self.audio_generation.text_to_speech(
            text=text, voice=voice, speed=speed, provider=provider, **kwargs
        )

    async def transcribe(self, audio_data: bytes, language: str = "en",
                         provider: str = None, **kwargs):
        """Transcribe audio to text."""
        return await self.audio_generation.transcribe(
            audio_data=audio_data, language=language, provider=provider, **kwargs
        )

    def list_audio_providers(self):
        """List all available audio providers."""
        return self.audio_generation.list_providers()

    def get_audio_stats(self):
        """Get audio generation statistics."""
        return self.audio_generation.get_stats()

    # ── Phase 17 — Decision Ledger Convenience Methods ──

    # ── Phase 18 — Browser AI ──

    def list_browser_runtimes(self) -> list:
        """List available browser AI runtimes."""
        return self.browser_ai.list_runtimes()

    def list_browser_models(self, category: str = "", runtime: str = "") -> list:
        """List browser-compatible AI models."""
        return self.browser_ai.list_models(category=category or None, runtime=runtime or None)

    def find_browser_models(self, task_type: str, max_memory_mb: float = 4000) -> list:
        """Find browser models for a task within memory limits."""
        return self.browser_ai.find_models_for_task(task_type, max_memory_mb)

    def select_browser_runtime(self, task_type: str, needs_offline: bool = False,
                               needs_mobile: bool = False) -> str:
        """Select optimal browser runtime for a task."""
        return self.browser_ai.select_optimal_runtime(task_type, needs_offline, needs_mobile)

    def generate_browser_template(self, runtime: str, task_type: str,
                                   model_id: str = "") -> dict:
        """Generate browser inference HTML/JS template."""
        return self.browser_ai.generate_inference_template(runtime, task_type, model_id or None)

    # ── Phase 19 — Edge AI ──

    def detect_edge_hardware(self) -> dict:
        """Detect edge AI hardware on this system."""
        return self.edge_ai.detect_hardware()

    def list_edge_profiles(self, hardware: str = "", platform: str = "") -> list:
        """List edge hardware profiles."""
        return self.edge_ai.list_profiles(hardware=hardware or None, platform_filter=platform or None)

    def find_optimal_edge_profile(self, task_type: str, max_power_watts: float = 100.0,
                                   min_memory_gb: float = 0.0) -> dict:
        """Find optimal edge profile for a task."""
        return self.edge_ai.find_optimal_profile(task_type, max_power_watts, min_memory_gb)

    def generate_edge_template(self, hardware: str, task_type: str) -> dict:
        """Generate edge deployment template."""
        return self.edge_ai.generate_deployment_template(hardware, task_type)

    # ── Phase 20 — Plugin System ──

    def register_plugin(self, plugin_id: str, name: str = "", version: str = "1.0.0",
                         plugin_type: str = "tool", description: str = "", **kwargs) -> dict:
        """Register a new plugin."""
        from .plugin_system import PluginType
        pt = PluginType(plugin_type) if plugin_type in [e.value for e in PluginType] else PluginType.TOOL
        entry = self.plugin_system.register_plugin(
            plugin_id=plugin_id, name=name, version=version,
            plugin_type=pt, description=description, **kwargs,
        )
        return entry.to_dict()

    def activate_plugin(self, plugin_id: str) -> bool:
        """Activate a plugin."""
        return self.plugin_system.activate_plugin(plugin_id)

    def deactivate_plugin(self, plugin_id: str) -> bool:
        """Deactivate a plugin."""
        return self.plugin_system.deactivate_plugin(plugin_id)

    def uninstall_plugin(self, plugin_id: str) -> bool:
        """Uninstall a plugin."""
        return self.plugin_system.uninstall_plugin(plugin_id)

    def list_plugins(self, plugin_type: str = "", state: str = "") -> list:
        """List registered plugins."""
        from .plugin_system import PluginType, PluginState
        pt = PluginType(plugin_type) if plugin_type else None
        ps = PluginState(state) if state else None
        return self.plugin_system.list_plugins(plugin_type=pt, state=ps)

    def get_plugin(self, plugin_id: str) -> dict:
        """Get a specific plugin."""
        return self.plugin_system.get_plugin(plugin_id) or {}

    def list_plugin_tools(self) -> list:
        """List all registered plugin tools."""
        return self.plugin_system.list_tools()

    # ── Phase 21 — Observability ──

    def observe_generation(self, request_id: str, task_type: str, provider: str = "") -> str:
        """Track generation start. Returns trace_id."""
        return self.observability.track_generation_start(request_id, task_type, provider)

    def observe_generation_end(self, trace_id: str, success: bool, latency_ms: float = 0.0,
                                provider: str = "", quality_score: float = 0.0):
        """Track generation end."""
        self.observability.track_generation_end(trace_id, success, latency_ms, provider, quality_score)

    def get_observability_metrics(self) -> dict:
        """Get all observability metrics."""
        return self.observability.export_metrics()

    def get_observability_traces(self, limit: int = 50) -> list:
        """Get recent traces."""
        return self.observability.get_recent_traces(limit)

    def get_observability_logs(self, level: str = "", source: str = "",
                                limit: int = 100) -> list:
        """Get log entries."""
        return self.observability.get_logs(level=level or None, source=source or None, limit=limit)

    # ── Phase 22 — Search Systems ──

    def index_search_documents(self, index_name: str, documents: list):
        """Index documents into a search index."""
        self.search_systems.index_documents(index_name, documents)

    def search_index(self, index_name: str, query: str, **kwargs) -> dict:
        """Search an index."""
        return self.search_systems.search(index_name, query, **kwargs).to_dict()

    def search_providers(self, query: str, provider_type: str = "", tier: str = "") -> dict:
        """Search providers."""
        return self.search_systems.search_providers(query, provider_type, tier).to_dict()

    def search_models(self, query: str, category: str = "", runtime: str = "") -> dict:
        """Search models."""
        return self.search_systems.search_models(query, category, runtime).to_dict()

    def search_knowledge(self, query: str, category: str = "", domain: str = "") -> dict:
        """Search knowledge base."""
        return self.search_systems.search_knowledge(query, category, domain).to_dict()

    def search_decisions(self, query: str, decision_type: str = "", outcome: str = "") -> dict:
        """Search decision ledger."""
        return self.search_systems.search_decisions(query, decision_type, outcome).to_dict()

    def search_benchmarks(self, query: str, provider: str = "", task_type: str = "") -> dict:
        """Search benchmark history."""
        return self.search_systems.search_benchmarks(query, provider, task_type).to_dict()

    def list_search_indexes(self) -> list:
        """List all search indexes."""
        return self.search_systems.list_indexes()

    # ── Phase 23 — OCR ──

    def list_ocr_providers(self) -> list:
        """List OCR provider profiles."""
        return self.ocr_engine.list_providers()

    def select_ocr_backend(self, document_type: str = "image", language: str = "en",
                            needs_gpu: bool = False) -> str:
        """Select best OCR backend."""
        from .ocr_engine import DocumentType
        dt = DocumentType(document_type) if document_type in [e.value for e in DocumentType] else DocumentType.IMAGE
        return self.ocr_engine.select_backend(dt, language, needs_gpu)

    def process_ocr(self, document_type: str = "image", language: str = "en",
                     backend: str = "") -> dict:
        """Process an OCR request (routing only)."""
        from .ocr_engine import OCRRequest, DocumentType
        dt = DocumentType(document_type) if document_type in [e.value for e in DocumentType] else DocumentType.IMAGE
        req = OCRRequest(document_type=dt, language=language, backend=backend or None)
        return self.ocr_engine.process(req).to_dict()

    # ── Phase 24 — 3D Generation ──

    def list_3d_models(self, mode: str = "") -> list:
        """List 3D generation models."""
        return self.generation_3d.list_models(mode=mode or None)

    def select_3d_model(self, mode: str = "text_to_3d", max_vram_gb: float = 32.0) -> str:
        """Select best 3D model for a request."""
        return self.generation_3d.select_model(mode, max_vram_gb) or ""

    def get_3d_output_formats(self, model_id: str) -> list:
        """Get output formats for a 3D model."""
        return self.generation_3d.get_output_formats(model_id)

    # ── Phase 25 — Regression Detection ──

    def set_benchmark_baseline(self, provider: str, metrics: dict):
        """Set baseline metrics for regression detection."""
        self.regression_detector.set_baseline(provider, metrics)

    def detect_regression(self, provider: str, metrics: dict) -> list:
        """Auto-detect all regression types for a provider."""
        return [a.to_dict() for a in self.regression_detector.auto_detect(provider, metrics)]

    def get_regression_alerts(self, severity: str = "", provider: str = "",
                               limit: int = 100) -> list:
        """Get regression alerts."""
        return self.regression_detector.get_all_alerts(severity or None, provider or None, limit)

    # ── Phase 26 — Capability Graph ──

    def find_capability_path(self, capability: str, preferred_provider: str = "") -> list:
        """Find execution paths to a capability."""
        return [p.to_dict() for p in self.capability_graph.find_capability_path(
            capability, preferred_provider or None)]

    def find_fallback_chain(self, capability: str, failed_provider: str = "") -> list:
        """Find fallback chain for a capability."""
        return self.capability_graph.find_fallback_chain(
            capability, failed_provider or None)

    def estimate_execution_cost(self, provider: str, capability: str) -> dict:
        """Estimate execution cost."""
        return self.capability_graph.estimate_execution_cost(provider, capability)

    # ── Phase 27 — Security ──

    def authenticate_api_key(self, api_key: str) -> dict:
        """Authenticate via API key."""
        result = self.security.authenticate_api_key(api_key)
        return result or {"error": "authentication failed"}

    def create_user(self, username: str, role: str = "viewer") -> dict:
        """Create a new user."""
        from .security import Role
        r = Role(role) if role in [e.value for e in Role] else Role.VIEWER
        result = self.security.create_user(username, r)
        return result or {"error": "user already exists"}

    def authorize(self, user_id: str, permission: str) -> dict:
        """Check if a user has a permission."""
        from .security import Permission
        try:
            p = Permission(permission)
        except ValueError:
            return {"allowed": False, "reason": f"unknown permission: {permission}"}
        return self.security.authorize(user_id, p).to_dict()

    def list_security_users(self) -> list:
        """List all users."""
        return self.security.list_users()

    def get_security_stats(self) -> dict:
        """Get security statistics."""
        return self.security.get_stats()

    def get_capability_graph_stats(self) -> dict:
        """Get capability graph statistics."""
        return self.capability_graph.get_stats()

    def dynamic_graph_add_node(self, node_id: str, node_type: str = "capability",
                                 name: str = "", attributes: dict = None) -> dict:
        from .capability_graph import NodeType
        nt = NodeType(node_type) if node_type in [e.value for e in NodeType] else NodeType.CAPABILITY
        return self.capability_graph.dynamic_add_node(node_id, nt, name, attributes or {})

    def dynamic_graph_add_edge(self, source_id: str, target_id: str,
                                 edge_type: str = "supports", weight: float = 1.0,
                                 attributes: dict = None) -> dict:
        from .capability_graph import EdgeType
        et = EdgeType(edge_type) if edge_type in [e.value for e in EdgeType] else EdgeType.SUPPORTS
        return self.capability_graph.dynamic_add_edge(source_id, target_id, et, weight, attributes or {})

    def dynamic_graph_update_node(self, node_id: str, attributes: dict) -> dict:
        return self.capability_graph.dynamic_update_node(node_id, attributes)

    def dynamic_graph_remove_node(self, node_id: str) -> dict:
        return self.capability_graph.dynamic_remove_node(node_id)

    def dynamic_graph_remove_edge(self, source_id: str, target_id: str,
                                    edge_type: str = "") -> dict:
        from .capability_graph import EdgeType
        et = EdgeType(edge_type) if edge_type and edge_type in [e.value for e in EdgeType] else None
        return self.capability_graph.dynamic_remove_edge(source_id, target_id, et)

    def dynamic_graph_batch_benchmark(self, updates: list) -> dict:
        return self.capability_graph.batch_update_benchmark(updates)

    def dynamic_graph_batch_health(self, updates: dict) -> dict:
        return self.capability_graph.batch_update_health(updates)

    def dynamic_graph_get_history(self, limit: int = 50) -> list:
        return self.capability_graph.get_update_history(limit)

    def dynamic_graph_get_stats(self) -> dict:
        return self.capability_graph.dynamic_get_stats()

    def get_regression_stats(self) -> dict:
        """Get regression detection statistics."""
        return self.regression_detector.get_stats()

    def get_3d_stats(self) -> dict:
        """Get 3D generation statistics."""
        return self.generation_3d.get_stats()

    def get_ocr_stats(self) -> dict:
        """Get OCR engine statistics."""
        return self.ocr_engine.get_stats()

    def get_search_stats(self) -> dict:
        """Get search system statistics."""
        return self.search_systems.get_stats()

    def get_observability_stats(self) -> dict:
        """Get observability statistics."""
        return self.observability.get_stats()

    def get_plugin_stats(self) -> dict:
        """Get plugin system statistics."""
        return self.plugin_system.get_stats()

    def get_edge_ai_stats(self) -> dict:
        """Get edge AI layer statistics."""
        return self.edge_ai.get_stats()

    def get_browser_ai_stats(self) -> dict:
        """Get browser AI layer statistics."""
        return self.browser_ai.get_stats()

    # ── Phase 28 — Failure Recovery Convenience Methods ──

    def attempt_recovery(self, error: str, task_context: dict) -> dict:
        """Automatically detect failure and attempt recovery."""
        return self.failure_recovery.attempt_recovery(error, task_context).to_dict()

    def detect_failure_type(self, error: str) -> str:
        """Detect the type of failure from an error message."""
        engine = self.failure_recovery
        if engine.detect_gpu_oom(error):
            return 'gpu_oom'
        if engine.detect_gpu_crash(error):
            return 'gpu_crash'
        if engine.detect_runtime_crash(error):
            return 'runtime_crash'
        return 'unknown'

    def recover_gpu_oom(self, task_context: dict) -> dict:
        """Execute GPU OOM recovery playbook."""
        return self.failure_recovery.recover_gpu_oom(task_context).to_dict()

    def recover_runtime_crash(self, task_context: dict) -> dict:
        """Execute runtime crash recovery playbook."""
        return self.failure_recovery.recover_runtime_crash(task_context).to_dict()

    def recover_gpu_crash(self, task_context: dict) -> dict:
        """Execute GPU crash recovery playbook."""
        return self.failure_recovery.recover_gpu_crash(task_context).to_dict()

    def recover_nan_inf(self, task_context: dict) -> dict:
        """Execute NaN/Inf recovery playbook."""
        return self.failure_recovery.recover_nan_inf(task_context).to_dict()

    def get_failure_events(self, limit: int = 50, failure_type: str = '') -> list:
        """Get recent failure events."""
        return self.failure_recovery.get_events(limit, failure_type or None)

    def get_failure_summary(self) -> dict:
        """Get failure recovery summary."""
        return self.failure_recovery.get_event_summary()

    # ── Phase 30 — Security Crypto Convenience Methods ──

    def generate_encryption_key(self, key_material: bytes = None, algorithm: str = "aes-256-gcm") -> dict:
        from .security_crypto import EncryptionAlgorithm
        alg = EncryptionAlgorithm(algorithm) if algorithm in [e.value for e in EncryptionAlgorithm] else EncryptionAlgorithm.AES_256_GCM
        return self.encryption_at_rest.generate_key(key_material, alg).to_dict()

    def encrypt_data(self, data: bytes, key_id: str = None) -> dict:
        result = self.encryption_at_rest.encrypt(data, key_id)
        return result.to_dict()

    def decrypt_data(self, ciphertext: bytes, nonce: bytes, tag: bytes, key_id: str = None) -> dict:
        from .security_crypto import EncryptedPayload
        payload = EncryptedPayload(ciphertext=ciphertext, nonce=nonce, tag=tag, key_id=key_id or "")
        result = self.encryption_at_rest.decrypt(payload, key_id)
        return {"success": result is not None, "data": result.hex() if result else None}

    def get_encryption_stats(self) -> dict:
        return self.encryption_at_rest.get_stats()

    async def verify_tls(self, host: str, port: int = 443) -> dict:
        return (await self.encryption_in_transit.verify_tls(host, port)).to_dict()

    def get_tls_stats(self) -> dict:
        return self.encryption_in_transit.get_stats()

    def compute_file_checksum(self, file_path: str, algorithm: str = "sha256") -> dict:
        from .security_crypto import ChecksumAlgorithm
        alg = ChecksumAlgorithm(algorithm) if algorithm in [e.value for e in ChecksumAlgorithm] else ChecksumAlgorithm.SHA256
        return self.model_security.compute_checksum(file_path, alg).to_dict()

    def verify_file_checksum(self, file_path: str, expected: str = None, algorithm: str = "sha256") -> dict:
        from .security_crypto import ChecksumAlgorithm
        alg = ChecksumAlgorithm(algorithm) if algorithm in [e.value for e in ChecksumAlgorithm] else ChecksumAlgorithm.SHA256
        if expected:
            self.model_security.register_expected(file_path, expected, alg)
        return self.model_security.verify_checksum(file_path, alg)

    def get_model_security_stats(self) -> dict:
        return self.model_security.get_stats()

    # ── Phase 32 — OTLP Export Convenience Methods ──

    async def otel_start(self) -> None:
        """Start the OTLP exporter background task."""
        return await self.otel_exporter.start()

    async def otel_stop(self) -> None:
        """Stop the OTLP exporter."""
        return await self.otel_exporter.stop()

    async def otel_export_all(self) -> list:
        """Export all signals (metrics, traces, logs) to OTLP endpoint."""
        return await self.otel_exporter.export_all()

    def get_otel_stats(self) -> dict:
        """Get OTLP exporter statistics."""
        return self.otel_exporter.get_stats()

    def get_otel_history(self, limit: int = 50) -> list:
        """Get OTLP export history."""
        return self.otel_exporter.get_export_history(limit)

    # ── Phase 31 — Event Bus Convenience Methods ──

    def event_bus_subscribe(self, subject: str, callback=None) -> dict:
        sub = self.event_bus.subscribe(subject, callback)
        return {"subscription_id": sub.subscription_id, "subject": sub.subject}

    def event_bus_unsubscribe(self, subscription_id: str) -> bool:
        return self.event_bus.unsubscribe(subscription_id)

    def event_bus_publish_sync(self, subject: str, payload=None, publisher: str = "") -> dict:
        msg = self.event_bus.publish_sync(subject, payload, publisher=publisher)
        return msg.to_dict()

    def event_bus_get_history(self, subject: str = None, limit: int = 50) -> list:
        return self.event_bus.get_history(subject, limit)

    def event_bus_get_subscriptions(self) -> list:
        return self.event_bus.get_subscriptions()

    def get_event_bus_stats(self) -> dict:
        return self.event_bus.get_stats()

    def emit_event(self, event_type: str, data=None, source: str = "") -> dict:
        import asyncio
        loop = asyncio.new_event_loop()
        try:
            msg = loop.run_until_complete(self.event_kernel.emit(event_type, data, source))
            return msg.to_dict()
        finally:
            loop.close()

    def get_event_kernel_stats(self) -> dict:
        return self.event_kernel.get_stats()

    # ── Phase 29 — Local Runtime Convenience Methods ──

    async def discover_local_runtimes(self) -> dict:
        """Discover available local runtimes (vLLM, llama.cpp, Ollama)."""
        return {k: v.to_dict() for k, v in (await self.local_runtimes.discover_runtimes()).items()}

    def list_local_models(self) -> dict:
        """List models available on all healthy local runtimes."""
        import asyncio
        loop = asyncio.get_event_loop()
        if loop.is_running():
            return {"error": "Use await discover_local_runtimes() from async context"}
        return loop.run_until_complete(self.local_runtimes.list_all_models())

    def get_local_runtime_stats(self) -> dict:
        """Get local runtime statistics."""
        return self.local_runtimes.get_stats()

    def get_local_runtime_profile(self, runtime_type: str) -> dict:
        """Get profile for a specific local runtime."""
        from .local_runtimes import RuntimeType
        rt = RuntimeType(runtime_type) if runtime_type in [e.value for e in RuntimeType] else RuntimeType.VLLM
        profile = self.local_runtimes.get_runtime_profile(rt)
        return profile or {"error": f"Runtime {runtime_type} not discovered"}

    def configure_local_runtime(self, runtime_type: str, url: str = "", **kwargs) -> dict:
        """Configure a local runtime endpoint."""
        from .local_runtimes import RuntimeType
        rt = RuntimeType(runtime_type) if runtime_type in [e.value for e in RuntimeType] else RuntimeType.VLLM
        if url:
            kwargs["url"] = url
        self.local_runtimes.configure_runtime(rt, **kwargs)
        return {"success": True, "runtime": runtime_type, "config": kwargs}

    async def generate_local(self, model: str, prompt: str, runtime: str = "", **kwargs) -> dict:
        """Generate text using a local runtime."""
        from .local_runtimes import RuntimeType
        rt = RuntimeType(runtime) if runtime and runtime in [e.value for e in RuntimeType] else None
        result = await self.local_runtimes.generate(model, prompt, runtime=rt, **kwargs)
        return result.to_dict()

    def get_failure_recovery_stats(self) -> dict:
        """Get failure recovery statistics."""
        return self.failure_recovery.get_stats()

    def get_decision_stats(self):
        """Get decision ledger statistics."""
        return self.decision_ledger.get_stats()

    def get_recent_decisions(self, limit=50):
        """Get recent decisions from the ledger."""
        return self.decision_ledger.get_recent(limit)

    def get_provider_decisions(self, provider, limit=50):
        """Get decisions for a specific provider."""
        return self.decision_ledger.get_by_provider(provider, limit)

    def get_decision_failures(self, limit=50):
        """Get all failed decisions."""
        return self.decision_ledger.get_failures(limit)
