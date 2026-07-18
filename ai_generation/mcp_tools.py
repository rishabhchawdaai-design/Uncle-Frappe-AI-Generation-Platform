"""
MCP Tools for AI Generation — expose generation capabilities as MCP tools.
"""
import asyncio
import json
import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)

MCP_GENERATION_TOOLS = {
    "generate_image": {
        "name": "generate_image",
        "description": "Generate an image from a text prompt using AI. Supports multiple providers with automatic failover.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "prompt": {"type": "string", "description": "Text prompt describing the image to generate"},
                "style": {"type": "string", "description": "Style preset: photorealistic, cinematic, anime, digital_art, etc.", "default": ""},
                "width": {"type": "integer", "description": "Image width in pixels", "default": 1024},
                "height": {"type": "integer", "description": "Image height in pixels", "default": 1024},
                "provider": {"type": "string", "description": "Preferred provider name (auto-select if omitted)"},
                "seed": {"type": "integer", "description": "Random seed for reproducibility"},
            },
            "required": ["prompt"],
        },
    },
    "generate_video": {
        "name": "generate_video",
        "description": "Generate a video from a text prompt using AI video models.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "prompt": {"type": "string", "description": "Text prompt describing the video"},
                "duration_secs": {"type": "number", "description": "Duration in seconds", "default": 4.0},
                "width": {"type": "integer", "default": 1280},
                "height": {"type": "integer", "default": 720},
            },
            "required": ["prompt"],
        },
    },
    "enhance_prompt": {
        "name": "enhance_prompt",
        "description": "Enhance a text prompt with quality modifiers, style presets, and negative prompts.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "prompt": {"type": "string", "description": "Original prompt to enhance"},
                "style": {"type": "string", "description": "Style preset to apply", "default": "photorealistic"},
                "quality": {"type": "string", "enum": ["high", "medium", "fast"], "default": "high"},
            },
            "required": ["prompt"],
        },
    },
    "analyze_prompt": {
        "name": "analyze_prompt",
        "description": "Analyze a prompt and get suggestions for improvement.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "prompt": {"type": "string", "description": "Prompt to analyze"},
            },
            "required": ["prompt"],
        },
    },
    "list_providers": {
        "name": "list_providers",
        "description": "List all available AI generation providers with their status, tier, and capabilities.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    "list_styles": {
        "name": "list_styles",
        "description": "List all available style presets for image generation.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    "list_templates": {
        "name": "list_templates",
        "description": "List all available prompt templates organized by category.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    "get_provider_stats": {
        "name": "get_provider_stats",
        "description": "Get performance statistics for all providers including success rates and latency.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    "get_known_providers": {
        "name": "get_known_providers",
        "description": "List known free and community AI providers from the research database.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "provider_type": {"type": "string", "enum": ["image", "video"], "description": "Filter by type"},
                "tier": {"type": "string", "enum": ["free", "community", "paid"], "description": "Filter by tier"},
            },
        },
    },
    "render_template": {
        "name": "render_template",
        "description": "Render a prompt template with provided variables.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "template_name": {"type": "string", "description": "Template name"},
                "variables": {"type": "object", "description": "Template variables as key-value pairs"},
            },
            "required": ["template_name", "variables"],
        },
    },
    "evaluate_generation": {
        "name": "evaluate_generation",
        "description": "Evaluate the quality of a prompt for image generation.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "prompt": {"type": "string", "description": "Prompt to evaluate"},
                "enhanced": {"type": "string", "description": "Enhanced version if available"},
                "negative": {"type": "string", "description": "Negative prompt if available"},
            },
            "required": ["prompt"],
        },
    },
    "analyze_media_request": {"name": "analyze_media_request", "description": "Analyze a media request for strategy, providers, workflow.", "inputSchema": {"type": "object", "properties": {"prompt": {"type": "string"}, "budget": {"type": "string", "default": "free"}}, "required": ["prompt"]}},
    "edit_image": {"name": "edit_image", "description": "Image editing: img2img, inpainting, outpainting, background, style transfer, upscaling.", "inputSchema": {"type": "object", "properties": {"operation": {"type": "string", "enum": ["img2img", "inpainting", "outpainting", "background_removal", "background_replacement", "style_transfer", "upscale"]}, "input_path": {"type": "string"}, "prompt": {"type": "string"}}, "required": ["operation", "input_path"]}},
    "list_edit_operations": {"name": "list_edit_operations", "description": "List all supported image editing operations.", "inputSchema": {"type": "object", "properties": {}}},
    "generate_video_ai": {"name": "generate_video_ai", "description": "Generate true AI video (text-to-video or image-to-video).", "inputSchema": {"type": "object", "properties": {"prompt": {"type": "string"}, "mode": {"type": "string", "default": "text_to_video"}, "image_path": {"type": "string"}, "duration_secs": {"type": "number", "default": 4.0}}, "required": ["prompt"]}},
    "get_video_capabilities": {"name": "get_video_capabilities", "description": "Get video generation capabilities.", "inputSchema": {"type": "object", "properties": {}}},
    "create_cinematic_pipeline": {"name": "create_cinematic_pipeline", "description": "Create cinematic production pipeline from template.", "inputSchema": {"type": "object", "properties": {"template": {"type": "string", "enum": ["full_cinematic", "quick_ad", "storyboard_only", "character_design", "post_production"]}}, "required": ["template"]}},
    "list_cinematic_templates": {"name": "list_cinematic_templates", "description": "List cinematic pipeline templates.", "inputSchema": {"type": "object", "properties": {}}},
    "plan_media_production": {"name": "plan_media_production", "description": "Plan complete media production from natural language.", "inputSchema": {"type": "object", "properties": {"request": {"type": "string"}}, "required": ["request"]}},
    "create_character": {"name": "create_character", "description": "Create character profile for consistency.", "inputSchema": {"type": "object", "properties": {"name": {"type": "string"}, "description": {"type": "string"}}, "required": ["name"]}},
    "get_capability_matrix": {"name": "get_capability_matrix", "description": "Get capability matrix of all providers/models.", "inputSchema": {"type": "object", "properties": {}}},
    "get_provider_intelligence": {"name": "get_provider_intelligence", "description": "Get provider intelligence recommendations.", "inputSchema": {"type": "object", "properties": {}}},
    "score_cinema_output": {"name": "score_cinema_output", "description": "Score output across cinematic quality dimensions.", "inputSchema": {"type": "object", "properties": {"provider": {"type": "string"}, "scores": {"type": "object"}}, "required": ["provider"]}},
    "list_cinema_dimensions": {"name": "list_cinema_dimensions", "description": "List cinematic benchmark dimensions.", "inputSchema": {"type": "object", "properties": {}}},
    "agent_generate": {"name": "agent_generate", "description": "Agent-native generation: classify task, find best provider, execute, return result.", "inputSchema": {"type": "object", "properties": {"request": {"type": "string", "description": "Natural language generation request"}, "require_free": {"type": "boolean", "default": False}}, "required": ["request"]}},
    "agent_edit": {"name": "agent_edit", "description": "Agent-native image editing with automatic provider selection.", "inputSchema": {"type": "object", "properties": {"image_path": {"type": "string"}, "prompt": {"type": "string", "default": ""}}, "required": ["image_path"]}},
    "agent_video": {"name": "agent_video", "description": "Agent-native video generation with automatic provider selection.", "inputSchema": {"type": "object", "properties": {"request": {"type": "string"}, "require_free": {"type": "boolean", "default": False}}, "required": ["request"]}},
    "list_execution_endpoints": {"name": "list_execution_endpoints", "description": "List all execution endpoints across all 4 layers.", "inputSchema": {"type": "object", "properties": {}}},
    "health_check_providers": {"name": "health_check_providers", "description": "Run health checks on all registered providers.", "inputSchema": {"type": "object", "properties": {}}},
    "get_capability_registry": {"name": "get_capability_registry", "description": "Get the live capability registry of all providers and models.", "inputSchema": {"type": "object", "properties": {}}},
    "classify_request": {"name": "classify_request", "description": "Classify a natural language request into a task type with routing decision.", "inputSchema": {"type": "object", "properties": {"request": {"type": "string"}}, "required": ["request"]}},
    "add_remote_endpoint": {"name": "add_remote_endpoint", "description": "Add a user-configured remote inference endpoint (ComfyUI, Forge, etc.).", "inputSchema": {"type": "object", "properties": {"name": {"type": "string"}, "url": {"type": "string"}, "endpoint_type": {"type": "string", "default": "api"}}, "required": ["name", "url"]}},
    "get_provider_discovery": {"name": "get_provider_discovery", "description": "Get provider discovery research and recommendations.", "inputSchema": {"type": "object", "properties": {}}},
    # ── Phase 14 — AIG-OS Tools ──
    "aigos_status": {"name": "aigos_status", "description": "Get AIG-OS orchestrator status with all 10 autonomous agents.", "inputSchema": {"type": "object", "properties": {}}},
    "aigos_agents": {"name": "aigos_agents", "description": "List all AIG-OS autonomous agents and their current status.", "inputSchema": {"type": "object", "properties": {}}},
    "aigos_execute": {"name": "aigos_execute", "description": "Execute a natural language generation request through the AIG-OS pipeline.", "inputSchema": {"type": "object", "properties": {"request": {"type": "string", "description": "Natural language generation or editing request"}}, "required": ["request"]}},
    "aigos_knowledge_search": {"name": "aigos_knowledge_search", "description": "Search the AIG-OS provider knowledge graph.", "inputSchema": {"type": "object", "properties": {"query": {"type": "string"}, "domain": {"type": "string", "default": ""}}, "required": ["query"]}},
    "aigos_leaderboard": {"name": "aigos_leaderboard", "description": "Get the AIG-OS benchmark leaderboard.", "inputSchema": {"type": "object", "properties": {}}},
    "aigos_research_providers": {"name": "aigos_research_providers", "description": "Get all providers discovered by the Research Agent.", "inputSchema": {"type": "object", "properties": {}}},
    "aigos_discovery_endpoints": {"name": "aigos_discovery_endpoints", "description": "Get all execution endpoints discovered by the Discovery Agent.", "inputSchema": {"type": "object", "properties": {}}},
    "aigos_verify_provider": {"name": "aigos_verify_provider", "description": "Run verification checks on a provider.", "inputSchema": {"type": "object", "properties": {"provider": {"type": "string"}, "capabilities": {"type": "array", "items": {"type": "string"}, "default": ["text_to_image"]}}, "required": ["provider"]}},
    "aigos_benchmark": {"name": "aigos_benchmark", "description": "Run a benchmark on a provider for quality scoring.", "inputSchema": {"type": "object", "properties": {"provider": {"type": "string"}, "categories": {"type": "array", "items": {"type": "string"}, "default": ["realism", "prompt_adherence"]}}, "required": ["provider"]}},
    "aigos_report_failure": {"name": "aigos_report_failure", "description": "Report a provider failure to the Recovery Agent.", "inputSchema": {"type": "object", "properties": {"provider": {"type": "string"}, "error": {"type": "string", "default": "unknown"}}, "required": ["provider"]}},
    "aigos_evolve": {"name": "aigos_evolve", "description": "Trigger the Evolution Agent to refresh discovery, benchmarks, and routing.", "inputSchema": {"type": "object", "properties": {}}},
}


class MCPGenerationTools:
    """Handler for MCP generation tool calls."""

    def __init__(self):
        self._sdk = None

    @property
    def sdk(self):
        if self._sdk is None:
            from .sdk import UncleFrappeAI
            self._sdk = UncleFrappeAI()
        return self._sdk

    async def handle(self, tool_name, arguments):
        handlers = {
            "generate_image": self._handle_generate_image,
            "generate_video": self._handle_generate_video,
            "enhance_prompt": self._handle_enhance_prompt,
            "analyze_prompt": self._handle_analyze_prompt,
            "list_providers": self._handle_list_providers,
            "list_styles": self._handle_list_styles,
            "list_templates": self._handle_list_templates,
            "get_provider_stats": self._handle_provider_stats,
            "get_known_providers": self._handle_known_providers,
            "render_template": self._handle_render_template,
            "evaluate_generation": self._handle_evaluate,
            "analyze_media_request": self._handle_analyze_media,
            "edit_image": self._handle_edit_image,
            "list_edit_operations": self._handle_list_edits,
            "generate_video_ai": self._handle_video_ai,
            "get_video_capabilities": self._handle_video_caps,
            "create_cinematic_pipeline": self._handle_create_pipeline,
            "list_cinematic_templates": self._handle_list_templates_cinematic,
            "plan_media_production": self._handle_plan,
            "create_character": self._handle_create_character,
            "get_capability_matrix": self._handle_capability_matrix,
            "get_provider_intelligence": self._handle_intel,
            "score_cinema_output": self._handle_score_cinema,
            "list_cinema_dimensions": self._handle_cinema_dims,
            "agent_generate": self._handle_agent_generate,
            "agent_edit": self._handle_agent_edit,
            "agent_video": self._handle_agent_video,
            "list_execution_endpoints": self._handle_list_endpoints,
            "health_check_providers": self._handle_health_check,
            "get_capability_registry": self._handle_cap_registry,
            "classify_request": self._handle_classify,
            "add_remote_endpoint": self._handle_add_endpoint,
            "get_provider_discovery": self._handle_discovery,
            "aigos_status": self._handle_aigos_status,
            "aigos_agents": self._handle_aigos_agents,
            "aigos_execute": self._handle_aigos_execute,
            "aigos_knowledge_search": self._handle_aigos_knowledge_search,
            "aigos_leaderboard": self._handle_aigos_leaderboard,
            "aigos_research_providers": self._handle_aigos_research_providers,
            "aigos_discovery_endpoints": self._handle_aigos_discovery_endpoints,
            "aigos_verify_provider": self._handle_aigos_verify_provider,
            "aigos_benchmark": self._handle_aigos_benchmark,
            "aigos_report_failure": self._handle_aigos_report_failure,
            "aigos_evolve": self._handle_aigos_evolve,        }
        handler = handlers.get(tool_name)
        if not handler:
            return {"error": f"Unknown tool: {tool_name}"}
        try:
            return await handler(arguments)
        except Exception as e:
            return {"error": str(e)[:200]}

    async def _handle_generate_image(self, args):
        result = await self.sdk.generate(
            prompt=args["prompt"], style=args.get("style", ""),
            width=args.get("width", 1024), height=args.get("height", 1024),
            provider=args.get("provider"), seed=args.get("seed"),
        )
        return result.to_dict()

    async def _handle_generate_video(self, args):
        result = await self.sdk.generate_video(
            prompt=args["prompt"], duration_secs=args.get("duration_secs", 4.0),
            width=args.get("width", 1280), height=args.get("height", 720),
        )
        return result.to_dict()

    async def _handle_enhance_prompt(self, args):
        result = self.sdk.enhance_prompt(
            args["prompt"], style=args.get("style", "photorealistic"),
            quality=args.get("quality", "high"),
        )
        return {
            "original": result.original, "enhanced": result.enhanced,
            "negative_prompt": result.negative_prompt, "style": result.style,
            "techniques": result.techniques_applied,
            "confidence": result.confidence,
        }

    async def _handle_analyze_prompt(self, args):
        return self.sdk.analyze_prompt(args["prompt"])

    async def _handle_list_providers(self, args):
        return {"providers": self.sdk.list_providers()}

    async def _handle_list_styles(self, args):
        return {"styles": self.sdk.list_styles()}

    async def _handle_list_templates(self, args):
        return {"templates": self.sdk.list_templates()}

    async def _handle_provider_stats(self, args):
        return self.sdk.generation_manager.get_stats()

    async def _handle_known_providers(self, args):
        return {
            "providers": self.sdk.research_agent.get_known_providers(
                provider_type=args.get("provider_type"),
                tier=args.get("tier"),
            )
        }

    async def _handle_render_template(self, args):
        result = self.sdk.prompt_engine.render_template(
            args["template_name"], **args.get("variables", {}),
        )
        return {"rendered": result}

    async def _handle_evaluate(self, args):
        report = self.sdk.quality_engine.evaluate_prompt(
            args["prompt"], enhanced=args.get("enhanced", ""),
            negative=args.get("negative", ""),
        )
        return report.to_dict()

    # ── Phase 11 Handlers ──

    async def _handle_analyze_media(self, args):
        from ai_generation.media_intelligence import BudgetTier
        budget_map = {"free": BudgetTier.FREE, "low": BudgetTier.LOW, "medium": BudgetTier.MEDIUM,
                      "high": BudgetTier.HIGH, "unlimited": BudgetTier.UNLIMITED}
        budget = budget_map.get(args.get("budget", "free"), BudgetTier.FREE)
        analysis = self.sdk.media_intelligence.analyze_request(
            args["prompt"], budget=budget,
            prioritize_speed=args.get("prioritize_speed", False),
        )
        return analysis.to_dict()

    async def _handle_edit_image(self, args):
        from ai_generation.image_editing import EditOperation
        op_map = {
            "img2img": EditOperation.IMG2IMG, "inpainting": EditOperation.INPAINTING,
            "outpainting": EditOperation.OUTPAINTING, "background_removal": EditOperation.BACKGROUND_REMOVAL,
            "background_replacement": EditOperation.BACKGROUND_REPLACEMENT,
            "style_transfer": EditOperation.STYLE_TRANSFER, "upscale": EditOperation.UPSCALE,
            "object_removal": EditOperation.OBJECT_REMOVAL, "object_insertion": EditOperation.OBJECT_INSERTION,
            "relighting": EditOperation.RELIGHTING,
        }
        op = op_map.get(args["operation"], EditOperation.IMG2IMG)
        result = await self.sdk.image_editing.edit(
            op, args["input_path"], prompt=args.get("prompt", ""),
            strength=args.get("strength", 0.75), mask_path=args.get("mask_path", ""),
        )
        return result.to_dict()

    async def _handle_list_edits(self, args):
        return {"operations": self.sdk.image_editing.get_all_operations()}

    async def _handle_video_ai(self, args):
        from ai_generation.video_generation import VideoGenMode
        mode_map = {"text_to_video": VideoGenMode.TEXT_TO_VIDEO, "image_to_video": VideoGenMode.IMAGE_TO_VIDEO}
        mode = mode_map.get(args.get("mode", "text_to_video"), VideoGenMode.TEXT_TO_VIDEO)
        result = await self.sdk.video_generation.generate(
            mode=mode, prompt=args["prompt"],
            image_path=args.get("image_path", ""),
            duration_secs=args.get("duration_secs", 4.0),
            width=args.get("width", 1280), height=args.get("height", 720),
            fallback_to_ken_burns=args.get("fallback_ken_burns", False),
        )
        return result.to_dict()

    async def _handle_video_caps(self, args):
        return {"capabilities": self.sdk.video_generation.get_capabilities_report()}

    async def _handle_create_pipeline(self, args):
        pipeline = self.sdk.cinematic_workflow.create_pipeline(
            template=args["template"], name=args.get("name", ""),
        )
        return pipeline.to_dict()

    async def _handle_list_templates_cinematic(self, args):
        from ai_generation.cinematic_workflow import PipelineTemplates
        return {"templates": PipelineTemplates.list_all()}

    async def _handle_plan(self, args):
        plan = self.sdk.plan_request(args["request"])
        return plan.to_dict()

    async def _handle_create_character(self, args):
        char = self.sdk.create_character(args["name"], description=args.get("description", ""))
        return char.to_dict()

    async def _handle_capability_matrix(self, args):
        return self.sdk.get_capability_matrix()

    async def _handle_intel(self, args):
        return {"recommendations": self.sdk.get_provider_recommendations()}

    async def _handle_score_cinema(self, args):
        report = self.sdk.cinema_benchmark.score_output(
            provider=args["provider"],
            scores=args.get("scores"),
        )
        return report.to_dict()

    async def _handle_cinema_dims(self, args):
        return {"dimensions": self.sdk.get_cinema_dimensions()}

    async def _handle_agent_generate(self, args):
        return await self.sdk.agent_generate(args["request"], require_free=args.get("require_free", False))

    async def _handle_agent_edit(self, args):
        return await self.sdk.agent_edit(args["image_path"], prompt=args.get("prompt", ""))

    async def _handle_agent_video(self, args):
        return await self.sdk.agent_video(args["request"], require_free=args.get("require_free", False))

    async def _handle_list_endpoints(self, args):
        return {"endpoints": self.sdk.agent_providers()}

    async def _handle_health_check(self, args):
        return await self.sdk.agent_health_check()

    async def _handle_cap_registry(self, args):
        return self.sdk.agent_capability_matrix()

    async def _handle_classify(self, args):
        return self.sdk.agent_classify(args["request"])

    async def _handle_add_endpoint(self, args):
        return self.sdk.agent_add_remote_endpoint(args["name"], args["url"], endpoint_type=args.get("endpoint_type", "api"))

    async def _handle_discovery(self, args):
        return {"recommendations": self.sdk.get_provider_recommendations()}


    async def _handle_aigos_status(self, args):
        return self.sdk.aigos_status()

    async def _handle_aigos_agents(self, args):
        return {"agents": self.sdk.aigos_agents()}

    async def _handle_aigos_execute(self, args):
        return self.sdk.aigos_execute(args["request"])

    async def _handle_aigos_knowledge_search(self, args):
        return self.sdk.aigos_knowledge_query(args["query"], args.get("domain", ""))

    async def _handle_aigos_leaderboard(self, args):
        return {"leaderboard": self.sdk.aigos_benchmark_leaderboard()}

    async def _handle_aigos_research_providers(self, args):
        return {"providers": self.sdk.aigos_providers()}

    async def _handle_aigos_discovery_endpoints(self, args):
        return {"endpoints": self.sdk.aigos_endpoints()}

    async def _handle_aigos_verify_provider(self, args):
        from ai_generation.agents.base_agent import AgentTask
        task = AgentTask(task_type="verify_provider", payload={
            "provider": args["provider"], "capabilities": args.get("capabilities", ["text_to_image"]),
        })
        agent = self.sdk.aigos.registry.get_agent("verification")
        return agent.execute(task).data

    async def _handle_aigos_benchmark(self, args):
        from ai_generation.agents.base_agent import AgentTask
        task = AgentTask(task_type="benchmark_provider", payload={
            "provider": args["provider"], "categories": args.get("categories", ["realism", "prompt_adherence"]),
        })
        agent = self.sdk.aigos.registry.get_agent("benchmark")
        return agent.execute(task).data

    async def _handle_aigos_report_failure(self, args):
        from ai_generation.agents.base_agent import AgentTask
        task = AgentTask(task_type="report_failure", payload={
            "provider": args["provider"], "error": args.get("error", "unknown"),
        })
        agent = self.sdk.aigos.registry.get_agent("recovery")
        return agent.execute(task).data

    async def _handle_aigos_evolve(self, args):
        from ai_generation.agents.base_agent import AgentTask
        task = AgentTask(task_type="evolve")
        agent = self.sdk.aigos.registry.get_agent("evolution")
        return agent.execute(task).data


    async def _handle_aigos_status(self, args):
        return self.sdk.aigos_status()

    async def _handle_aigos_agents(self, args):
        return {"agents": self.sdk.aigos_agents()}

    async def _handle_aigos_execute(self, args):
        return self.sdk.aigos_execute(args["request"])

    async def _handle_aigos_knowledge_search(self, args):
        return self.sdk.aigos_knowledge_query(args["query"], args.get("domain", ""))

    async def _handle_aigos_leaderboard(self, args):
        return {"leaderboard": self.sdk.aigos_benchmark_leaderboard()}

    async def _handle_aigos_research_providers(self, args):
        return {"providers": self.sdk.aigos_providers()}

    async def _handle_aigos_discovery_endpoints(self, args):
        return {"endpoints": self.sdk.aigos_endpoints()}

    async def _handle_aigos_verify_provider(self, args):
        from ai_generation.agents.base_agent import AgentTask
        task = AgentTask(task_type="verify_provider", payload={
            "provider": args["provider"], "capabilities": args.get("capabilities", ["text_to_image"]),
        })
        agent = self.sdk.aigos.registry.get_agent("verification")
        return agent.execute(task).data

    async def _handle_aigos_benchmark(self, args):
        from ai_generation.agents.base_agent import AgentTask
        task = AgentTask(task_type="benchmark_provider", payload={
            "provider": args["provider"], "categories": args.get("categories", ["realism", "prompt_adherence"]),
        })
        agent = self.sdk.aigos.registry.get_agent("benchmark")
        return agent.execute(task).data

    async def _handle_aigos_report_failure(self, args):
        from ai_generation.agents.base_agent import AgentTask
        task = AgentTask(task_type="report_failure", payload={
            "provider": args["provider"], "error": args.get("error", "unknown"),
        })
        agent = self.sdk.aigos.registry.get_agent("recovery")
        return agent.execute(task).data

    async def _handle_aigos_evolve(self, args):
        from ai_generation.agents.base_agent import AgentTask
        task = AgentTask(task_type="evolve")
        agent = self.sdk.aigos.registry.get_agent("evolution")
        return agent.execute(task).data


def get_mcp_generation_tools():
    return MCP_GENERATION_TOOLS
