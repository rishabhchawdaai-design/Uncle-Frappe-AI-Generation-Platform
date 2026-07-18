"""
Cinematic Workflow Engine — production pipelines for end-to-end media production.
Idea → Script → Shot List → Storyboard → Character Sheets → Environment Design →
Master Frames → Video Generation → Editing → Upscaling → Frame Interpolation →
Color Grading → Audio → Master Export.

Extends the existing workflow_engine.py with cinematic pipeline support.
"""
import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class PipelineStage(str, Enum):
    IDEA = "idea"
    SCRIPT = "script"
    SHOT_LIST = "shot_list"
    STORYBOARD = "storyboard"
    CHARACTER_SHEETS = "character_sheets"
    ENVIRONMENT_DESIGN = "environment_design"
    MASTER_FRAMES = "master_frames"
    VIDEO_GENERATION = "video_generation"
    EDITING = "editing"
    UPSCALING = "upscaling"
    FRAME_INTERPOLATION = "frame_interpolation"
    COLOR_GRADING = "color_grading"
    AUDIO = "audio"
    MASTER_EXPORT = "master_export"


STAGE_ORDER = [s.value for s in PipelineStage]

STAGE_DESCRIPTIONS = {
    PipelineStage.IDEA: "Define the creative concept, mood, target audience",
    PipelineStage.SCRIPT: "Write the narrative script with dialogue and scene descriptions",
    PipelineStage.SHOT_LIST: "Break script into individual shots with camera angles and timing",
    PipelineStage.STORYBOARD: "Visual rough drafts of each shot composition",
    PipelineStage.CHARACTER_SHEETS: "Design and lock character appearances for consistency",
    PipelineStage.ENVIRONMENT_DESIGN: "Design locations, lighting, atmosphere",
    PipelineStage.MASTER_FRAMES: "Generate final reference frames for each shot",
    PipelineStage.VIDEO_GENERATION: "Generate video clips from master frames or prompts",
    PipelineStage.EDITING: "Assemble clips, add transitions, pacing",
    PipelineStage.UPSCALING: "Upscale footage to target resolution",
    PipelineStage.FRAME_INTERPOLATION: "Add intermediate frames for smooth motion",
    PipelineStage.COLOR_GRADING: "Apply consistent color treatment across all shots",
    PipelineStage.AUDIO: "Add music, sound effects, dialogue",
    PipelineStage.MASTER_EXPORT: "Final render and export in target formats",
}


@dataclass
class PipelineStep:
    stage: PipelineStage
    name: str = ""
    description: str = ""
    params: Dict[str, Any] = field(default_factory=dict)
    depends_on: List[str] = field(default_factory=list)
    optional: bool = False
    status: str = "pending"
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

    def __post_init__(self):
        if not self.name:
            self.name = self.stage.value
        if not self.description:
            self.description = STAGE_DESCRIPTIONS.get(self.stage, "")


@dataclass
class CinematicPipeline:
    name: str = ""
    description: str = ""
    pipeline_id: str = ""
    steps: List[PipelineStep] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    status: str = "pending"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def __post_init__(self):
        if not self.pipeline_id:
            self.pipeline_id = "pipe-" + uuid.uuid4().hex[:8]

    def get_step(self, stage: PipelineStage) -> Optional[PipelineStep]:
        for s in self.steps:
            if s.stage == stage:
                return s
        return None

    def get_ready_steps(self) -> List[PipelineStep]:
        completed = {s.stage.value for s in self.steps if s.status == "completed"}
        return [
            s for s in self.steps
            if s.status == "pending" and all(dep in completed for dep in s.depends_on)
        ]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pipeline_id": self.pipeline_id,
            "name": self.name,
            "description": self.description,
            "status": self.status,
            "stages": [
                {"stage": s.stage.value, "name": s.name, "status": s.status, "error": s.error}
                for s in self.steps
            ],
            "created_at": self.created_at,
        }


class PipelineTemplates:
    """Reusable cinematic pipeline templates."""

    @staticmethod
    def full_cinematic(
        name: str = "Full Cinematic Production",
        include_audio: bool = True,
        include_interpolation: bool = True,
    ) -> CinematicPipeline:
        steps = [
            PipelineStep(stage=PipelineStage.IDEA, name="Define Concept"),
            PipelineStep(stage=PipelineStage.SCRIPT, name="Write Script",
                        depends_on=["idea"]),
            PipelineStep(stage=PipelineStage.SHOT_LIST, name="Create Shot List",
                        depends_on=["script"]),
            PipelineStep(stage=PipelineStage.STORYBOARD, name="Create Storyboard",
                        depends_on=["shot_list"]),
            PipelineStep(stage=PipelineStage.CHARACTER_SHEETS, name="Design Characters",
                        depends_on=["script"]),
            PipelineStep(stage=PipelineStage.ENVIRONMENT_DESIGN, name="Design Environments",
                        depends_on=["script"]),
            PipelineStep(stage=PipelineStage.MASTER_FRAMES, name="Generate Master Frames",
                        depends_on=["storyboard", "character_sheets", "environment_design"]),
            PipelineStep(stage=PipelineStage.VIDEO_GENERATION, name="Generate Video Clips",
                        depends_on=["master_frames"]),
            PipelineStep(stage=PipelineStage.EDITING, name="Edit and Assemble",
                        depends_on=["video_generation"]),
            PipelineStep(stage=PipelineStage.UPSCALING, name="Upscale Footage",
                        depends_on=["editing"]),
        ]
        if include_interpolation:
            steps.append(PipelineStep(
                stage=PipelineStage.FRAME_INTERPOLATION, name="Frame Interpolation",
                depends_on=["upscaling"],
            ))
        steps.append(PipelineStep(
            stage=PipelineStage.COLOR_GRADING, name="Color Grade",
            depends_on=["frame_interpolation"] if include_interpolation else ["upscaling"],
        ))
        if include_audio:
            steps.append(PipelineStep(
                stage=PipelineStage.AUDIO, name="Add Audio",
                depends_on=["color_grading"],
            ))
        steps.append(PipelineStep(
            stage=PipelineStage.MASTER_EXPORT, name="Final Export",
            depends_on=["audio"] if include_audio else ["color_grading"],
        ))
        return CinematicPipeline(name=name, steps=steps)

    @staticmethod
    def quick_ad(
        name: str = "Quick Ad Production",
        duration_secs: float = 15.0,
    ) -> CinematicPipeline:
        return CinematicPipeline(name=name, steps=[
            PipelineStep(stage=PipelineStage.IDEA, name="Ad Concept",
                        params={"duration_secs": duration_secs}),
            PipelineStep(stage=PipelineStage.SCRIPT, name="Ad Script", depends_on=["idea"]),
            PipelineStep(stage=PipelineStage.MASTER_FRAMES, name="Key Frames",
                        depends_on=["script"]),
            PipelineStep(stage=PipelineStage.VIDEO_GENERATION, name="Generate Clips",
                        depends_on=["master_frames"]),
            PipelineStep(stage=PipelineStage.EDITING, name="Edit", depends_on=["video_generation"]),
            PipelineStep(stage=PipelineStage.COLOR_GRADING, name="Color Grade", depends_on=["editing"]),
            PipelineStep(stage=PipelineStage.MASTER_EXPORT, name="Export", depends_on=["color_grading"]),
        ])

    @staticmethod
    def storyboard_only(name: str = "Storyboard Pipeline") -> CinematicPipeline:
        return CinematicPipeline(name=name, steps=[
            PipelineStep(stage=PipelineStage.IDEA, name="Concept"),
            PipelineStep(stage=PipelineStage.SCRIPT, name="Script", depends_on=["idea"]),
            PipelineStep(stage=PipelineStage.SHOT_LIST, name="Shot List", depends_on=["script"]),
            PipelineStep(stage=PipelineStage.STORYBOARD, name="Storyboard", depends_on=["shot_list"]),
        ])

    @staticmethod
    def character_design(name: str = "Character Design Pipeline") -> CinematicPipeline:
        return CinematicPipeline(name=name, steps=[
            PipelineStep(stage=PipelineStage.IDEA, name="Character Concept"),
            PipelineStep(stage=PipelineStage.CHARACTER_SHEETS, name="Character Sheets",
                        depends_on=["idea"]),
            PipelineStep(stage=PipelineStage.ENVIRONMENT_DESIGN, name="Environment",
                        depends_on=["idea"]),
            PipelineStep(stage=PipelineStage.MASTER_FRAMES, name="Master Frames",
                        depends_on=["character_sheets", "environment_design"]),
        ])

    @staticmethod
    def post_production(name: str = "Post-Production Pipeline") -> CinematicPipeline:
        return CinematicPipeline(name=name, steps=[
            PipelineStep(stage=PipelineStage.UPSCALING, name="Upscale"),
            PipelineStep(stage=PipelineStage.FRAME_INTERPOLATION, name="Interpolation",
                        depends_on=["upscaling"]),
            PipelineStep(stage=PipelineStage.COLOR_GRADING, name="Color Grade",
                        depends_on=["frame_interpolation"]),
            PipelineStep(stage=PipelineStage.AUDIO, name="Audio", depends_on=["color_grading"]),
            PipelineStep(stage=PipelineStage.MASTER_EXPORT, name="Export", depends_on=["audio"]),
        ])

    @staticmethod
    def list_all() -> List[Dict[str, Any]]:
        return [
            {"name": "full_cinematic", "description": "Complete end-to-end cinematic production"},
            {"name": "quick_ad", "description": "Fast ad/mercial production pipeline"},
            {"name": "storyboard_only", "description": "Idea to storyboard only"},
            {"name": "character_design", "description": "Character and environment design"},
            {"name": "post_production", "description": "Upscaling, interpolation, grading, export"},
        ]


class CinematicWorkflowEngine:
    """
    Production-grade cinematic workflow engine.
    Extends the base workflow_engine with cinematic pipeline support.
    """

    def __init__(self, generation_manager=None, prompt_engine=None):
        self._gm = generation_manager
        self._pe = prompt_engine
        self._pipelines: Dict[str, CinematicPipeline] = {}
        self._history: List[Dict[str, Any]] = []

    def create_pipeline(self, template: Optional[str] = None, name: str = "", **kwargs) -> CinematicPipeline:
        templates = {
            "full_cinematic": PipelineTemplates.full_cinematic,
            "quick_ad": PipelineTemplates.quick_ad,
            "storyboard_only": PipelineTemplates.storyboard_only,
            "character_design": PipelineTemplates.character_design,
            "post_production": PipelineTemplates.post_production,
        }
        if template and template in templates:
            pipeline = templates[template](name=name or template, **kwargs)
        else:
            pipeline = CinematicPipeline(name=name or "custom_pipeline")
        self._pipelines[pipeline.pipeline_id] = pipeline
        return pipeline

    def get_pipeline(self, pipeline_id: str) -> Optional[CinematicPipeline]:
        return self._pipelines.get(pipeline_id)

    def list_pipelines(self) -> List[Dict[str, Any]]:
        return [p.to_dict() for p in self._pipelines.values()]

    async def execute_stage(self, pipeline_id: str, stage: PipelineStage,
                            handler: Optional[Callable] = None, context: Optional[Dict] = None):
        pipeline = self._pipelines.get(pipeline_id)
        if not pipeline:
            return {"error": f"Pipeline {pipeline_id} not found"}

        step = pipeline.get_step(stage)
        if not step:
            return {"error": f"Stage {stage.value} not in pipeline"}

        if step.status == "completed":
            return {"status": "already_completed", "stage": stage.value}

        ready = pipeline.get_ready_steps()
        if step not in ready:
            unmet = [d for d in step.depends_on if d not in {s.stage.value for s in pipeline.steps if s.status == "completed"}]
            return {"error": f"Dependencies not met: {unmet}"}

        step.status = "running"
        try:
            if handler:
                result = await handler(step, context or {}) if callable(handler) else handler
                step.result = result if isinstance(result, dict) else {"output": str(result)}
            else:
                step.result = {"stage": stage.value, "note": "no_handler_provided"}
            step.status = "completed"
        except Exception as e:
            step.status = "failed"
            step.error = str(e)[:200]
            return {"error": step.error}

        return {"status": "completed", "stage": stage.value, "result": step.result}

    async def execute_pipeline(self, pipeline_id: str, handlers: Optional[Dict[str, Callable]] = None,
                               context: Optional[Dict] = None):
        pipeline = self._pipelines.get(pipeline_id)
        if not pipeline:
            return {"error": f"Pipeline {pipeline_id} not found"}

        pipeline.status = "running"
        start = time.time()
        handlers = handlers or {}
        ctx = context or {}

        max_iter = len(pipeline.steps) * 3
        for _ in range(max_iter):
            ready = pipeline.get_ready_steps()
            if not ready:
                break
            for step in ready:
                handler = handlers.get(step.stage.value)
                await self.execute_stage(pipeline_id, step.stage, handler=handler, context=ctx)

        all_ok = all(s.status == "completed" for s in pipeline.steps)
        any_fail = any(s.status == "failed" for s in pipeline.steps)
        pipeline.status = "completed" if all_ok else "failed" if any_fail else "partial"

        elapsed = round((time.time() - start) * 1000, 1)
        summary = pipeline.to_dict()
        summary["elapsed_ms"] = elapsed
        self._history.append(summary)
        return summary

    def get_stats(self) -> Dict[str, Any]:
        statuses = {}
        for p in self._pipelines.values():
            statuses[p.status] = statuses.get(p.status, 0) + 1
        return {
            "total_pipelines": len(self._pipelines),
            "executed": len(self._history),
            "by_status": statuses,
            "templates": len(PipelineTemplates.list_all()),
        }
