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
    "edit_video": {"name": "edit_video", "description": "Execute a video editing operation (trim, concat, transition, speed, crop, resize, rotate, reverse, stabilize, watermark, audio_extract, audio_replace, subtitle_burn, enhance, frame_interpolation, upscale).", "inputSchema": {"type": "object", "properties": {"operation": {"type": "string", "enum": ["trim", "concat", "transition", "speed", "crop", "resize", "rotate", "reverse", "stabilize", "watermark", "audio_extract", "audio_replace", "subtitle_burn", "enhance", "frame_interpolation", "upscale"]}, "input_path": {"type": "string"}, "input_paths": {"type": "array", "items": {"type": "string"}}, "output_path": {"type": "string", "default": ""}}, "required": ["operation"]}},
    "trim_video": {"name": "trim_video", "description": "Trim video to start/end timestamps.", "inputSchema": {"type": "object", "properties": {"input_path": {"type": "string"}, "output_path": {"type": "string", "default": ""}, "start": {"type": "number", "default": 0.0}, "end": {"type": "number", "default": 0.0}}, "required": ["input_path"]}},
    "concat_videos": {"name": "concat_videos", "description": "Concatenate multiple video files sequentially.", "inputSchema": {"type": "object", "properties": {"input_paths": {"type": "array", "items": {"type": "string"}}, "output_path": {"type": "string", "default": ""}}, "required": ["input_paths"]}},
    "interpolate_video_frames": {"name": "interpolate_video_frames", "description": "Increase FPS using frame interpolation (RIFE/minterpolate).", "inputSchema": {"type": "object", "properties": {"input_path": {"type": "string"}, "output_path": {"type": "string", "default": ""}, "target_fps": {"type": "number", "default": 60.0}}, "required": ["input_path"]}},
    "upscale_video": {"name": "upscale_video", "description": "Upscale video resolution (2x or 4x) using Lanczos or Real-ESRGAN.", "inputSchema": {"type": "object", "properties": {"input_path": {"type": "string"}, "output_path": {"type": "string", "default": ""}, "scale_factor": {"type": "integer", "default": 2, "enum": [2, 4]}}, "required": ["input_path"]}},
    "enhance_video": {"name": "enhance_video", "description": "Enhance video quality (denoise, sharpen, color grade).", "inputSchema": {"type": "object", "properties": {"input_path": {"type": "string"}, "output_path": {"type": "string", "default": ""}, "denoise": {"type": "boolean", "default": True}, "sharpen": {"type": "boolean", "default": True}}, "required": ["input_path"]}},
    "get_video_edit_profiles": {"name": "get_video_edit_profiles", "description": "List all video editing operations and their requirements.", "inputSchema": {"type": "object", "properties": {}}},
    
    "clone_voice": {"name": "clone_voice", "description": "Clone a voice from reference audio and generate speech. Supports XTTS, Fish Speech, OpenVoice.", "inputSchema": {"type": "object", "properties": {"reference_audio_path": {"type": "string"}, "text": {"type": "string"}, "language": {"type": "string", "default": "en"}, "provider": {"type": "string", "enum": ["xtts", "fish_speech", "openvoice"]}, "output_path": {"type": "string", "default": ""}}, "required": ["reference_audio_path", "text"]}},
    "get_voice_clone_profiles": {"name": "get_voice_clone_profiles", "description": "List available voice cloning providers and their capabilities.", "inputSchema": {"type": "object", "properties": {}}},
    "generate_music": {"name": "generate_music", "description": "Generate music from text prompt using AudioCraft/MusicGen.", "inputSchema": {"type": "object", "properties": {"prompt": {"type": "string"}, "duration_secs": {"type": "number", "default": 10.0}, "model": {"type": "string", "default": ""}, "output_path": {"type": "string", "default": ""}}, "required": ["prompt"]}},
    "generate_sfx": {"name": "generate_sfx", "description": "Generate sound effects from text prompt using AudioCraft/AudioGen.", "inputSchema": {"type": "object", "properties": {"prompt": {"type": "string"}, "duration_secs": {"type": "number", "default": 5.0}, "output_path": {"type": "string", "default": ""}}, "required": ["prompt"]}},
    "generate_melody": {"name": "generate_melody", "description": "Generate melody-conditioned music from text prompt and reference melody.", "inputSchema": {"type": "object", "properties": {"prompt": {"type": "string"}, "melody_path": {"type": "string"}, "duration_secs": {"type": "number", "default": 10.0}, "output_path": {"type": "string", "default": ""}}, "required": ["prompt", "melody_path"]}},
        "enhance_audio": {"name": "enhance_audio", "description": "Execute audio enhancement operation (denoise, normalize, equalize, remove_silence, convert_format, resample, compress, limit, fade_in, fade_out, speed, pitch, reverse, mix, concat, gain).", "inputSchema": {"type": "object", "properties": {"operation": {"type": "string", "enum": ["denoise", "normalize", "equalize", "remove_silence", "convert_format", "resample", "compress", "limit", "fade_in", "fade_out", "trim_silence", "speed", "pitch", "reverse", "concat", "mix", "gain"]}, "input_path": {"type": "string"}, "input_paths": {"type": "array", "items": {"type": "string"}}, "output_path": {"type": "string", "default": ""}}, "required": ["operation"]}},
    "denoise_audio": {"name": "denoise_audio", "description": "Remove noise from audio.", "inputSchema": {"type": "object", "properties": {"input_path": {"type": "string"}, "output_path": {"type": "string", "default": ""}, "strength": {"type": "string", "enum": ["light", "medium", "strong"], "default": "medium"}}, "required": ["input_path"]}},
    "normalize_audio": {"name": "normalize_audio", "description": "Normalize audio loudness.", "inputSchema": {"type": "object", "properties": {"input_path": {"type": "string"}, "output_path": {"type": "string", "default": ""}, "target_level": {"type": "number", "default": -16}}, "required": ["input_path"]}},
    "convert_audio": {"name": "convert_audio", "description": "Convert audio format (wav, mp3, aac, ogg, flac).", "inputSchema": {"type": "object", "properties": {"input_path": {"type": "string"}, "output_path": {"type": "string", "default": ""}, "format": {"type": "string", "enum": ["wav", "mp3", "aac", "ogg", "flac"], "default": "wav"}}, "required": ["input_path"]}},
    "mix_audio": {"name": "mix_audio", "description": "Mix multiple audio files together.", "inputSchema": {"type": "object", "properties": {"input_paths": {"type": "array", "items": {"type": "string"}}, "output_path": {"type": "string", "default": ""}, "weights": {"type": "array", "items": {"type": "number"}}}, "required": ["input_paths"]}},
        "parse_document": {"name": "parse_document", "description": "Parse document to Markdown (PDF, DOCX, HTML, EPUB, PPTX). Uses Marker, Nougat, or Docling.", "inputSchema": {"type": "object", "properties": {"input_path": {"type": "string"}, "output_path": {"type": "string", "default": ""}, "backend": {"type": "string", "enum": ["auto", "marker", "nougat", "docling", "builtin"], "default": "auto"}}, "required": ["input_path"]}},
    "extract_tables": {"name": "extract_tables", "description": "Extract tables from PDF documents. Uses Camelot or Tabula.", "inputSchema": {"type": "object", "properties": {"input_path": {"type": "string"}, "backend": {"type": "string", "enum": ["auto", "camelot", "tabula", "builtin"], "default": "auto"}, "pages": {"type": "string", "default": "all"}}, "required": ["input_path"]}},
    "analyze_layout": {"name": "analyze_layout", "description": "Analyze document layout (regions, columns, headers). Uses LayoutLMv3, DETR, or Surya.", "inputSchema": {"type": "object", "properties": {"input_path": {"type": "string"}, "backend": {"type": "string", "enum": ["auto", "layoutlmv3", "detr", "surya", "builtin"], "default": "auto"}}, "required": ["input_path"]}},
    "get_doc_intelligence_profiles": {"name": "get_doc_intelligence_profiles", "description": "List available document intelligence backends.", "inputSchema": {"type": "object", "properties": {}}},
    "concat_audio": {"name": "concat_audio", "description": "Concatenate multiple audio files sequentially.", "inputSchema": {"type": "object", "properties": {"input_paths": {"type": "array", "items": {"type": "string"}}, "output_path": {"type": "string", "default": ""}}, "required": ["input_paths"]}},
    "get_music_profiles": {"name": "get_music_profiles", "description": "List available music/SFX generation models.", "inputSchema": {"type": "object", "properties": {}}},
    "probe_video": {"name": "probe_video", "description": "Probe video file metadata (resolution, fps, codec, duration).", "inputSchema": {"type": "object", "properties": {"input_path": {"type": "string"}}, "required": ["input_path"]}},

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

    # ── Phase 16 — Audio Generation Tools ──
    "text_to_speech": {
        "name": "text_to_speech",
        "description": "Convert text to speech using AI. Supports multiple providers (OpenAI, Kokoro, Piper) with automatic failover.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Text to convert to speech"},
                "voice": {"type": "string", "description": "Voice name or ID", "default": "default"},
                "provider": {"type": "string", "description": "Preferred provider (auto-select if omitted)"},
                "output_path": {"type": "string", "description": "Output file path (optional)"},
                "speed": {"type": "number", "description": "Speech speed multiplier (0.5-2.0)", "default": 1.0},
            },
            "required": ["text"],
        },
    },
    "transcribe": {
        "name": "transcribe",
        "description": "Transcribe audio to text using AI speech recognition. Supports Whisper and other STT providers.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "audio_path": {"type": "string", "description": "Path to audio file to transcribe"},
                "language": {"type": "string", "description": "Language code (e.g., 'en', 'es')", "default": "en"},
                "provider": {"type": "string", "description": "Preferred provider (auto-select if omitted)"},
            },
            "required": ["audio_path"],
        },
    },
    "list_audio_providers": {
        "name": "list_audio_providers",
        "description": "List all available audio generation and speech recognition providers.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    "get_audio_stats": {
        "name": "get_audio_stats",
        "description": "Get performance statistics for audio providers.",
        "inputSchema": {"type": "object", "properties": {}},
    },

    # ── Phase 18 — Browser AI Inference Tools ──
    "list_browser_runtimes": {
        "name": "list_browser_runtimes",
        "description": "List available browser AI runtimes (Transformers.js, WebLLM, ONNX Web, TF.js).",
        "inputSchema": {"type": "object", "properties": {}},
    },
    "list_browser_models": {
        "name": "list_browser_models",
        "description": "List browser-compatible AI models with optional category/runtime filtering.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "category": {"type": "string", "description": "Filter by category (llm, embedding, classification)"},
                "runtime": {"type": "string", "description": "Filter by runtime"},
            },
        },
    },
    "find_browser_models": {
        "name": "find_browser_models",
        "description": "Find browser models suitable for a task type within memory limits.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "task_type": {"type": "string", "description": "Task type (text_generation, embedding, etc.)"},
                "max_memory_mb": {"type": "number", "description": "Max memory in MB", "default": 4000},
            },
            "required": ["task_type"],
        },
    },
    "select_browser_runtime": {
        "name": "select_browser_runtime",
        "description": "Select optimal browser runtime for a task type.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "task_type": {"type": "string", "description": "Task type"},
                "needs_offline": {"type": "boolean", "default": False},
                "needs_mobile": {"type": "boolean", "default": False},
            },
            "required": ["task_type"],
        },
    },
    "generate_browser_template": {
        "name": "generate_browser_template",
        "description": "Generate browser inference HTML/JS template for a runtime and task.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "runtime": {"type": "string", "description": "Browser runtime (transformers_js, webllm, onnx_web, tensorflow_js)"},
                "task_type": {"type": "string", "description": "Task type (text_generation, text_classification, etc.)"},
                "model_id": {"type": "string", "description": "Optional model ID"},
            },
            "required": ["runtime", "task_type"],
        },
    },
    "get_browser_ai_stats": {
        "name": "get_browser_ai_stats",
        "description": "Get browser AI layer statistics.",
        "inputSchema": {"type": "object", "properties": {}},
    },

    # ── Phase 19 — Edge AI Runtime Detection Tools ──
    "detect_edge_hardware": {
        "name": "detect_edge_hardware",
        "description": "Detect edge AI hardware on this system (Apple ANE, Qualcomm NPU, Intel NPU, Jetson, Coral).",
        "inputSchema": {"type": "object", "properties": {}},
    },
    "list_edge_profiles": {
        "name": "list_edge_profiles",
        "description": "List edge hardware profiles with optional filtering.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "hardware": {"type": "string", "description": "Filter by hardware type (apple_ane, qualcomm_npu, etc.)"},
                "platform": {"type": "string", "description": "Filter by platform (macos, linux, android)"},
            },
        },
    },
    "find_edge_profile": {
        "name": "find_edge_profile",
        "description": "Find optimal edge profile for a task within power/memory constraints.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "task_type": {"type": "string", "description": "Task type (text_generation, image_classification, etc.)"},
                "max_power_watts": {"type": "number", "description": "Max power budget in watts", "default": 100},
                "min_memory_gb": {"type": "number", "description": "Minimum memory in GB", "default": 0},
            },
            "required": ["task_type"],
        },
    },
    "generate_edge_template": {
        "name": "generate_edge_template",
        "description": "Generate deployment template for edge AI hardware.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "hardware": {"type": "string", "description": "Edge hardware type"},
                "task_type": {"type": "string", "description": "Task type"},
            },
            "required": ["hardware", "task_type"],
        },
    },
    "get_edge_ai_stats": {
        "name": "get_edge_ai_stats",
        "description": "Get edge AI layer statistics and detected hardware.",
        "inputSchema": {"type": "object", "properties": {}},
    },

    # ── Phase 20 — Plugin System Tools ──
    "list_plugins": {
        "name": "list_plugins",
        "description": "List all registered plugins with optional type/state filtering.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "plugin_type": {"type": "string", "description": "Filter by type (tool, runtime, compute, workflow, extension)"},
                "state": {"type": "string", "description": "Filter by state (active, registered, installed, etc.)"},
            },
        },
    },
    "get_plugin": {
        "name": "get_plugin",
        "description": "Get details of a specific plugin.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "plugin_id": {"type": "string", "description": "Plugin ID"},
            },
            "required": ["plugin_id"],
        },
    },
    "list_plugin_tools": {
        "name": "list_plugin_tools",
        "description": "List all MCP tools registered by plugins.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    "get_plugin_stats": {
        "name": "get_plugin_stats",
        "description": "Get plugin system statistics.",
        "inputSchema": {"type": "object", "properties": {}},
    },

    # ── Phase 21 — Observability Tools ──
    "get_observability_metrics": {
        "name": "get_observability_metrics",
        "description": "Get all observability metrics (counters, gauges, histograms).",
        "inputSchema": {"type": "object", "properties": {}},
    },
    "get_observability_traces": {
        "name": "get_observability_traces",
        "description": "Get recent distributed traces.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "description": "Max traces to return", "default": 50},
            },
        },
    },
    "get_observability_logs": {
        "name": "get_observability_logs",
        "description": "Get structured log entries with optional filtering.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "level": {"type": "string", "description": "Filter by level (info, warning, error)"},
                "source": {"type": "string", "description": "Filter by source"},
                "limit": {"type": "integer", "description": "Max logs", "default": 100},
            },
        },
    },
    "get_observability_stats": {
        "name": "get_observability_stats",
        "description": "Get observability layer statistics.",
        "inputSchema": {"type": "object", "properties": {}},
    },

    # ── Phase 22 — Search Systems Tools ──
    "search_index": {
        "name": "search_index",
        "description": "Search a document index with full-text search, filtering, and faceting.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "index_name": {"type": "string", "description": "Index to search (providers, models, knowledge, decisions, benchmarks)"},
                "query": {"type": "string", "description": "Search query"},
                "filter": {"type": "object", "description": "Filter expression"},
                "page": {"type": "integer", "default": 1},
                "hits_per_page": {"type": "integer", "default": 20},
            },
            "required": ["index_name", "query"],
        },
    },
    "search_providers": {
        "name": "search_providers",
        "description": "Search AI providers with filtering by type and tier.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "provider_type": {"type": "string"},
                "tier": {"type": "string"},
            },
            "required": ["query"],
        },
    },
    "search_models": {
        "name": "search_models",
        "description": "Search AI models with category and runtime filtering.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "category": {"type": "string"},
                "runtime": {"type": "string"},
            },
            "required": ["query"],
        },
    },
    "list_search_indexes": {
        "name": "list_search_indexes",
        "description": "List all available search indexes and their document counts.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    "get_search_stats": {
        "name": "get_search_stats",
        "description": "Get search system statistics.",
        "inputSchema": {"type": "object", "properties": {}},
    },

    # ── Phase 23 — OCR Tools ──
    "list_ocr_providers": {
        "name": "list_ocr_providers",
        "description": "List available OCR provider profiles (Tesseract, PaddleOCR, EasyOCR, Surya).",
        "inputSchema": {"type": "object", "properties": {}},
    },
    "select_ocr_backend": {
        "name": "select_ocr_backend",
        "description": "Select optimal OCR backend for a document type and language.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "document_type": {"type": "string", "default": "image"},
                "language": {"type": "string", "default": "en"},
                "needs_gpu": {"type": "boolean", "default": False},
            },
        },
    },
    "process_ocr": {
        "name": "process_ocr",
        "description": "Route an OCR request to the best available backend.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "document_type": {"type": "string", "default": "image"},
                "language": {"type": "string", "default": "en"},
                "backend": {"type": "string"},
            },
        },
    },
    "get_ocr_stats": {
        "name": "get_ocr_stats",
        "description": "Get OCR engine statistics.",
        "inputSchema": {"type": "object", "properties": {}},
    },

    # ── Phase 24 — 3D Generation Tools ──
    "list_3d_models": {
        "name": "list_3d_models",
        "description": "List available 3D generation models (TRELLIS, Hunyuan3D, Point-E, Shap-E).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "mode": {"type": "string", "description": "Filter by mode (text_to_3d, image_to_3d)"},
            },
        },
    },
    "select_3d_model": {
        "name": "select_3d_model",
        "description": "Select optimal 3D model for a generation mode and VRAM budget.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "mode": {"type": "string", "default": "text_to_3d"},
                "max_vram_gb": {"type": "number", "default": 32},
            },
        },
    },
    "get_3d_output_formats": {
        "name": "get_3d_output_formats",
        "description": "Get supported output formats for a 3D model.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "model_id": {"type": "string"},
            },
            "required": ["model_id"],
        },
    },
    "get_3d_stats": {
        "name": "get_3d_stats",
        "description": "Get 3D generation statistics.",
        "inputSchema": {"type": "object", "properties": {}},
    },

    # ── Phase 25 — Regression Detection Tools ──
    "detect_regression": {
        "name": "detect_regression",
        "description": "Auto-detect latency, quality, and stability regressions for a provider.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "provider": {"type": "string"},
                "metrics": {"type": "object"},
            },
            "required": ["provider", "metrics"],
        },
    },
    "get_regression_alerts": {
        "name": "get_regression_alerts",
        "description": "Get regression alerts with optional filtering.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "severity": {"type": "string"},
                "provider": {"type": "string"},
                "limit": {"type": "integer", "default": 100},
            },
        },
    },
    "get_regression_stats": {
        "name": "get_regression_stats",
        "description": "Get regression detection statistics.",
        "inputSchema": {"type": "object", "properties": {}},
    },

    # ── Phase 26 — Capability Graph Tools ──
    "find_capability_path": {
        "name": "find_capability_path",
        "description": "Find execution paths from providers to a capability.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "capability": {"type": "string", "description": "Target capability (text_to_image, text_to_video, etc.)"},
                "preferred_provider": {"type": "string"},
            },
            "required": ["capability"],
        },
    },
    "find_fallback_chain": {
        "name": "find_fallback_chain",
        "description": "Find fallback chain for a capability, excluding failed providers.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "capability": {"type": "string"},
                "failed_provider": {"type": "string"},
            },
            "required": ["capability"],
        },
    },
    "estimate_execution_cost": {
        "name": "estimate_execution_cost",
        "description": "Estimate execution cost for a provider-capability pair.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "provider": {"type": "string"},
                "capability": {"type": "string"},
            },
            "required": ["provider", "capability"],
        },
    },
    "get_capability_graph_stats": {
        "name": "get_capability_graph_stats",
        "description": "Get capability graph statistics.",
        "inputSchema": {"type": "object", "properties": {}},
    },

    # ── Phase 27 — Security Tools ──
    "list_security_users": {
        "name": "list_security_users",
        "description": "List all platform users and their roles.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    "authorize_user": {
        "name": "authorize_user",
        "description": "Check if a user has a specific permission.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string"},
                "permission": {"type": "string"},
            },
            "required": ["user_id", "permission"],
        },
    },
    "get_security_stats": {
        "name": "get_security_stats",
        "description": "Get security statistics.",
        "inputSchema": {"type": "object", "properties": {}},
    },

    # ── Phase 28 — Failure Recovery Tools ──
    "attempt_recovery": {
        "name": "attempt_recovery",
        "description": "Automatically detect failure type and attempt recovery.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "error": {"type": "string", "description": "Error message to analyze"},
                "task_context": {"type": "object", "description": "Task context with model, batch_size, vram_gb, etc."},
            },
            "required": ["error", "task_context"],
        },
    },
    "recover_gpu_oom": {
        "name": "recover_gpu_oom",
        "description": "Execute GPU OOM recovery playbook.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "task_context": {"type": "object", "description": "Task context with model, batch_size, vram_gb, etc."},
            },
            "required": ["task_context"],
        },
    },
    "recover_runtime_crash": {
        "name": "recover_runtime_crash",
        "description": "Execute runtime crash recovery playbook.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "task_context": {"type": "object", "description": "Task context with runtime_id, model, can_restart, etc."},
            },
            "required": ["task_context"],
        },
    },
    "recover_gpu_crash": {
        "name": "recover_gpu_crash",
        "description": "Execute GPU crash recovery playbook.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "task_context": {"type": "object", "description": "Task context with gpu_id, healthy_gpus, etc."},
            },
            "required": ["task_context"],
        },
    },
    "recover_nan_inf": {
        "name": "recover_nan_inf",
        "description": "Execute NaN/Inf recovery playbook.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "task_context": {"type": "object", "description": "Task context with has_nan, has_inf, layer, etc."},
            },
            "required": ["task_context"],
        },
    },
    "get_failure_events": {
        "name": "get_failure_events",
        "description": "Get recent failure events.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "description": "Max events to return"},
                "failure_type": {"type": "string", "description": "Filter by failure type"},
            },
        },
    },
    "get_failure_recovery_stats": {
        "name": "get_failure_recovery_stats",
        "description": "Get failure recovery statistics.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    # ── Phase 28b — Dynamic Graph Update Tools ──
    "dynamic_graph_add_node": {
        "name": "dynamic_graph_add_node",
        "description": "Add a new node to the capability graph at runtime.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "node_id": {"type": "string", "description": "Unique node identifier"},
                "node_type": {"type": "string", "description": "Node type: provider, runtime, hardware, model, capability"},
                "name": {"type": "string", "description": "Human-readable name"},
                "attributes": {"type": "object", "description": "Node attributes"},
            },
            "required": ["node_id"],
        },
    },
    "dynamic_graph_add_edge": {
        "name": "dynamic_graph_add_edge",
        "description": "Add a new edge between nodes in the capability graph.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "source_id": {"type": "string"},
                "target_id": {"type": "string"},
                "edge_type": {"type": "string", "description": "Edge type: supports, requires, depends_on, fallback_to, cost"},
                "weight": {"type": "number", "description": "Edge weight (higher = better)"},
            },
            "required": ["source_id", "target_id"],
        },
    },
    "dynamic_graph_update_node": {
        "name": "dynamic_graph_update_node",
        "description": "Update node attributes (scores, health, etc.) at runtime.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "node_id": {"type": "string"},
                "attributes": {"type": "object", "description": "Attributes to update"},
            },
            "required": ["node_id", "attributes"],
        },
    },
    "dynamic_graph_remove_node": {
        "name": "dynamic_graph_remove_node",
        "description": "Remove a node and its edges from the capability graph.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "node_id": {"type": "string"},
            },
            "required": ["node_id"],
        },
    },
    "dynamic_graph_batch_benchmark": {
        "name": "dynamic_graph_batch_benchmark",
        "description": "Batch update benchmark scores on nodes.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "updates": {"type": "array", "items": {"type": "object"}, "description": "List of {node_id, benchmark_score, latency_ms, quality_score}"},
            },
            "required": ["updates"],
        },
    },
    "dynamic_graph_batch_health": {
        "name": "dynamic_graph_batch_health",
        "description": "Batch update health scores for nodes.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "updates": {"type": "object", "description": "Dict of {node_id: health_score}"},
            },
            "required": ["updates"],
        },
    },
    "dynamic_graph_get_history": {
        "name": "dynamic_graph_get_history",
        "description": "Get recent graph update history.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "description": "Max entries to return"},
            },
        },
    },
    "dynamic_graph_get_stats": {
        "name": "dynamic_graph_get_stats",
        "description": "Get enhanced graph statistics including update count.",
        "inputSchema": {"type": "object", "properties": {}},
    },


    # ── Phase 29 — Local Runtime Tools ──
    "discover_local_runtimes": {
        "name": "discover_local_runtimes",
        "description": "Discover available local runtimes (vLLM, llama.cpp, Ollama).",
        "inputSchema": {"type": "object", "properties": {}},
    },
    "configure_local_runtime": {
        "name": "configure_local_runtime",
        "description": "Configure a local runtime endpoint URL.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "runtime_type": {"type": "string", "description": "Runtime: vllm, llamacpp, ollama"},
                "url": {"type": "string", "description": "Runtime server URL"},
            },
            "required": ["runtime_type", "url"],
        },
    },
    "get_local_runtime_stats": {
        "name": "get_local_runtime_stats",
        "description": "Get statistics for local runtime usage.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    "get_local_runtime_profile": {
        "name": "get_local_runtime_profile",
        "description": "Get detailed profile for a specific local runtime.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "runtime_type": {"type": "string", "description": "Runtime: vllm, llamacpp, ollama"},
            },
            "required": ["runtime_type"],
        },
    },
    "generate_local": {
        "name": "generate_local",
        "description": "Generate text using a local runtime (vLLM, llama.cpp, Ollama).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "model": {"type": "string", "description": "Model name"},
                "prompt": {"type": "string", "description": "Input prompt"},
                "runtime": {"type": "string", "description": "Preferred runtime: vllm, llamacpp, ollama"},
                "max_tokens": {"type": "integer", "description": "Max tokens to generate", "default": 512},
                "temperature": {"type": "number", "description": "Sampling temperature", "default": 0.7},
            },
            "required": ["model", "prompt"],
        },
    },

    # ── Phase 30 — Security Crypto Tools ──
    "generate_encryption_key": {
        "name": "generate_encryption_key",
        "description": "Generate an encryption key for data at rest.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "algorithm": {"type": "string", "description": "Encryption algorithm: aes-256-gcm, aes-128-gcm, chacha20-poly1305", "default": "aes-256-gcm"},
            },
        },
    },
    "encrypt_data": {
        "name": "encrypt_data",
        "description": "Encrypt data using AES-256-GCM.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "data": {"type": "string", "description": "Data to encrypt (hex encoded)"},
                "key_id": {"type": "string", "description": "Encryption key ID"},
            },
            "required": ["data"],
        },
    },
    "get_encryption_stats": {
        "name": "get_encryption_stats",
        "description": "Get encryption at rest statistics.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    "compute_file_checksum": {
        "name": "compute_file_checksum",
        "description": "Compute checksum of a file for integrity verification.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "Path to file"},
                "algorithm": {"type": "string", "description": "Checksum algorithm: sha256, sha512, sha3-256, blake2b", "default": "sha256"},
            },
            "required": ["file_path"],
        },
    },
    "verify_file_checksum": {
        "name": "verify_file_checksum",
        "description": "Verify a file's checksum against expected value.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "Path to file"},
                "expected": {"type": "string", "description": "Expected checksum"},
                "algorithm": {"type": "string", "description": "Checksum algorithm", "default": "sha256"},
            },
            "required": ["file_path"],
        },
    },
    "get_model_security_stats": {
        "name": "get_model_security_stats",
        "description": "Get model security statistics.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    "get_tls_stats": {
        "name": "get_tls_stats",
        "description": "Get TLS verification statistics.",
        "inputSchema": {"type": "object", "properties": {}},
    },

    # ── Phase 31 — Event Bus Tools ──
    "event_bus_publish": {
        "name": "event_bus_publish",
        "description": "Publish a message to the in-memory event bus.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "subject": {"type": "string", "description": "Message subject"},
                "payload": {"type": "string", "description": "Message payload"},
                "publisher": {"type": "string", "description": "Publisher name"},
            },
            "required": ["subject"],
        },
    },
    "event_bus_get_history": {
        "name": "event_bus_get_history",
        "description": "Get recent messages from the event bus.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "subject": {"type": "string", "description": "Filter by subject"},
                "limit": {"type": "integer", "description": "Max messages", "default": 50},
            },
        },
    },
    "event_bus_get_subscriptions": {
        "name": "event_bus_get_subscriptions",
        "description": "List all active subscriptions.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    "get_event_bus_stats": {
        "name": "get_event_bus_stats",
        "description": "Get event bus statistics.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    "emit_event": {
        "name": "emit_event",
        "description": "Emit a kernel event.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "event_type": {"type": "string", "description": "Event type"},
                "data": {"type": "string", "description": "Event data"},
                "source": {"type": "string", "description": "Event source"},
            },
            "required": ["event_type"],
        },
    },
    "get_event_kernel_stats": {
        "name": "get_event_kernel_stats",
        "description": "Get event-driven kernel statistics.",
        "inputSchema": {"type": "object", "properties": {}},
    },

    # ── Phase 32 — OpenTelemetry Export Tools ──
    "otel_start": {
        "name": "otel_start",
        "description": "Start the OTLP exporter background task.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    "otel_stop": {
        "name": "otel_stop",
        "description": "Stop the OTLP exporter.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    "otel_export_all": {
        "name": "otel_export_all",
        "description": "Export all signals (metrics, traces, logs) to OTLP endpoint.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    "get_otel_stats": {
        "name": "get_otel_stats",
        "description": "Get OTLP exporter statistics.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    "get_otel_history": {
        "name": "get_otel_history",
        "description": "Get OTLP export history.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "description": "Max entries", "default": 50},
            },
        },
    },
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
            "edit_video": self._handle_edit_video,
            "trim_video": self._handle_trim_video,
            "concat_videos": self._handle_concat_videos,
            "interpolate_video_frames": self._handle_interpolate_frames,
            "upscale_video": self._handle_upscale_video,
            "enhance_video": self._handle_enhance_video,
            "get_video_edit_profiles": self._handle_video_edit_profiles,
            "clone_voice": self._handle_clone_voice,
            "get_voice_clone_profiles": self._handle_voice_clone_profiles,
            "generate_music": self._handle_generate_music,
            "generate_sfx": self._handle_generate_sfx,
            "generate_melody": self._handle_generate_melody,
            "enhance_audio": self._handle_enhance_audio,
            "denoise_audio": self._handle_denoise_audio,
            "normalize_audio": self._handle_normalize_audio,
            "convert_audio": self._handle_convert_audio,
            "mix_audio": self._handle_mix_audio,
            "parse_document": self._handle_parse_document,
            "extract_tables": self._handle_extract_tables,
            "analyze_layout": self._handle_analyze_layout,
            "get_doc_intelligence_profiles": self._handle_doc_intelligence_profiles,
            "concat_audio": self._handle_concat_audio,
            "get_music_profiles": self._handle_music_profiles,
            "probe_video": self._handle_probe_video,
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
            "aigos_evolve": self._handle_aigos_evolve,
            "text_to_speech": self._handle_text_to_speech,
            "transcribe": self._handle_transcribe,
            "list_audio_providers": self._handle_list_audio_providers,
            "get_audio_stats": self._handle_get_audio_stats,
            "list_browser_runtimes": self._handle_list_browser_runtimes,
            "list_browser_models": self._handle_list_browser_models,
            "find_browser_models": self._handle_find_browser_models,
            "select_browser_runtime": self._handle_select_browser_runtime,
            "generate_browser_template": self._handle_generate_browser_template,
            "get_browser_ai_stats": self._handle_get_browser_ai_stats,
            "detect_edge_hardware": self._handle_detect_edge_hardware,
            "list_edge_profiles": self._handle_list_edge_profiles,
            "find_edge_profile": self._handle_find_edge_profile,
            "generate_edge_template": self._handle_generate_edge_template,
            "get_edge_ai_stats": self._handle_get_edge_ai_stats,
            "list_plugins": self._handle_list_plugins,
            "get_plugin": self._handle_get_plugin,
            "list_plugin_tools": self._handle_list_plugin_tools,
            "get_plugin_stats": self._handle_get_plugin_stats,
            "get_observability_metrics": self._handle_get_observability_metrics,
            "get_observability_traces": self._handle_get_observability_traces,
            "get_observability_logs": self._handle_get_observability_logs,
            "get_observability_stats": self._handle_get_observability_stats,
            "search_index": self._handle_search_index,
            "search_providers": self._handle_search_providers,
            "search_models": self._handle_search_models,
            "list_search_indexes": self._handle_list_search_indexes,
            "get_search_stats": self._handle_get_search_stats,
            "list_ocr_providers": self._handle_list_ocr_providers,
            "select_ocr_backend": self._handle_select_ocr_backend,
            "process_ocr": self._handle_process_ocr,
            "get_ocr_stats": self._handle_get_ocr_stats,
            "list_3d_models": self._handle_list_3d_models,
            "select_3d_model": self._handle_select_3d_model,
            "get_3d_output_formats": self._handle_get_3d_output_formats,
            "get_3d_stats": self._handle_get_3d_stats,
            "detect_regression": self._handle_detect_regression,
            "get_regression_alerts": self._handle_get_regression_alerts,
            "get_regression_stats": self._handle_get_regression_stats,
            "find_capability_path": self._handle_find_capability_path,
            "find_fallback_chain": self._handle_find_fallback_chain,
            "estimate_execution_cost": self._handle_estimate_execution_cost,
            "get_capability_graph_stats": self._handle_get_capability_graph_stats,
            "list_security_users": self._handle_list_security_users,
            "authorize_user": self._handle_authorize_user,
            "get_security_stats": self._handle_get_security_stats,
            "attempt_recovery": self._handle_attempt_recovery,
            "recover_gpu_oom": self._handle_recover_gpu_oom,
            "recover_runtime_crash": self._handle_recover_runtime_crash,
            "recover_gpu_crash": self._handle_recover_gpu_crash,
            "recover_nan_inf": self._handle_recover_nan_inf,
            "get_failure_events": self._handle_get_failure_events,
            "get_failure_recovery_stats": self._handle_get_failure_recovery_stats,
            "dynamic_graph_add_node": self._handle_dynamic_add_node,
            "dynamic_graph_add_edge": self._handle_dynamic_add_edge,
            "dynamic_graph_update_node": self._handle_dynamic_update_node,
            "dynamic_graph_remove_node": self._handle_dynamic_remove_node,
            "dynamic_graph_batch_benchmark": self._handle_dynamic_batch_benchmark,
            "dynamic_graph_batch_health": self._handle_dynamic_batch_health,
            "dynamic_graph_get_history": self._handle_dynamic_get_history,
            "dynamic_graph_get_stats": self._handle_dynamic_get_stats,
            "discover_local_runtimes": self._handle_discover_local_runtimes,
            "configure_local_runtime": self._handle_configure_local_runtime,
            "get_local_runtime_stats": self._handle_get_local_runtime_stats,
            "get_local_runtime_profile": self._handle_get_local_runtime_profile,
            "generate_local": self._handle_generate_local,
            "generate_encryption_key": self._handle_generate_encryption_key,
            "encrypt_data": self._handle_encrypt_data,
            "get_encryption_stats": self._handle_get_encryption_stats,
            "compute_file_checksum": self._handle_compute_file_checksum,
            "verify_file_checksum": self._handle_verify_file_checksum,
            "get_model_security_stats": self._handle_get_model_security_stats,
            "get_tls_stats": self._handle_get_tls_stats,
            "event_bus_publish": self._handle_event_bus_publish,
            "event_bus_get_history": self._handle_event_bus_get_history,
            "event_bus_get_subscriptions": self._handle_event_bus_get_subscriptions,
            "get_event_bus_stats": self._handle_get_event_bus_stats,
            "emit_event": self._handle_emit_event,
            "get_event_kernel_stats": self._handle_get_event_kernel_stats,
            "otel_start": self._handle_otel_start,
            "otel_stop": self._handle_otel_stop,
            "otel_export_all": self._handle_otel_export_all,
            "get_otel_stats": self._handle_get_otel_stats,
            "get_otel_history": self._handle_get_otel_history,
        }
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
    async def _handle_edit_video(self, args):
        from ai_generation.video_editing import VideoEditOperation
        op_str = args.get("operation", "trim")
        op = VideoEditOperation(op_str)
        result = await self.sdk.video_editing.execute(
            op, input_path=args.get("input_path", ""),
            input_paths=args.get("input_paths", []),
            output_path=args.get("output_path", ""),
            **{k: v for k, v in args.items() if k not in ("operation", "input_path", "input_paths", "output_path")},
        )
        return result.to_dict()

    async def _handle_trim_video(self, args):
        result = await self.sdk.video_editing.trim(
            args["input_path"], output_path=args.get("output_path", ""),
            start=args.get("start", 0.0), end=args.get("end", 0.0),
        )
        return result.to_dict()

    async def _handle_concat_videos(self, args):
        result = await self.sdk.video_editing.concat(
            args["input_paths"], output_path=args.get("output_path", ""),
        )
        return result.to_dict()

    async def _handle_interpolate_frames(self, args):
        result = await self.sdk.video_editing.interpolate_frames(
            args["input_path"], output_path=args.get("output_path", ""),
            target_fps=args.get("target_fps", 60.0),
        )
        return result.to_dict()

    async def _handle_upscale_video(self, args):
        result = await self.sdk.video_editing.upscale(
            args["input_path"], output_path=args.get("output_path", ""),
            scale_factor=args.get("scale_factor", 2),
        )
        return result.to_dict()

    async def _handle_enhance_video(self, args):
        result = await self.sdk.video_editing.enhance(
            args["input_path"], output_path=args.get("output_path", ""),
            denoise=args.get("denoise", True), sharpen=args.get("sharpen", True),
        )
        return result.to_dict()

    async def _handle_video_edit_profiles(self, args):
        return {"profiles": self.sdk.video_editing.get_profiles(), "available": self.sdk.video_editing.get_available_operations()}


    async def _handle_clone_voice(self, args):
        result = await self.sdk.clone_voice(
            args["reference_audio_path"], args["text"],
            language=args.get("language", "en"),
            provider=args.get("provider"),
            output_path=args.get("output_path", ""),
        )
        return result.to_dict()

    async def _handle_voice_clone_profiles(self, args):
        return {"profiles": self.sdk.voice_cloning.get_profiles(), "providers": self.sdk.voice_cloning.get_provider_names()}

    async def _handle_generate_music(self, args):
        result = await self.sdk.generate_music(
            args["prompt"],
            duration_secs=args.get("duration_secs", 10.0),
            model=args.get("model", ""),
            output_path=args.get("output_path", ""),
        )
        return result.to_dict()

    async def _handle_generate_sfx(self, args):
        result = await self.sdk.generate_sfx(
            args["prompt"],
            duration_secs=args.get("duration_secs", 5.0),
            output_path=args.get("output_path", ""),
        )
        return result.to_dict()

    async def _handle_generate_melody(self, args):
        result = await self.sdk.generate_melody(
            args["prompt"], args["melody_path"],
            duration_secs=args.get("duration_secs", 10.0),
            output_path=args.get("output_path", ""),
        )
        return result.to_dict()


    async def _handle_enhance_audio(self, args):
        from ai_generation.audio_enhancement import AudioEnhanceOperation
        op_str = args.get("operation", "denoise")
        op = AudioEnhanceOperation(op_str)
        result = await self.sdk.audio_enhancement.execute(
            op, input_path=args.get("input_path", ""),
            input_paths=args.get("input_paths", []),
            output_path=args.get("output_path", ""),
            **{k: v for k, v in args.items() if k not in ("operation", "input_path", "input_paths", "output_path")},
        )
        return result.to_dict()

    async def _handle_denoise_audio(self, args):
        result = await self.sdk.audio_enhancement.denoise(
            args["input_path"], output_path=args.get("output_path", ""),
            strength=args.get("strength", "medium"),
        )
        return result.to_dict()

    async def _handle_normalize_audio(self, args):
        result = await self.sdk.audio_enhancement.normalize(
            args["input_path"], output_path=args.get("output_path", ""),
            target_level=args.get("target_level", -16),
        )
        return result.to_dict()

    async def _handle_convert_audio(self, args):
        result = await self.sdk.audio_enhancement.convert_format(
            args["input_path"], output_path=args.get("output_path", ""),
            format=args.get("format", "wav"),
        )
        return result.to_dict()

    async def _handle_mix_audio(self, args):
        from ai_generation.audio_enhancement import AudioEnhanceOperation
        result = await self.sdk.audio_enhancement.execute(
            AudioEnhanceOperation.MIX, input_paths=args["input_paths"],
            output_path=args.get("output_path", ""),
            weights=args.get("weights"),
        )
        return result.to_dict()

    async def _handle_parse_document(self, args):
        result = await self.sdk.document_intelligence.parse_document(
            args["input_path"], output_path=args.get("output_path", ""),
            backend=args.get("backend", "auto"),
        )
        return result.to_dict()

    async def _handle_extract_tables(self, args):
        result = await self.sdk.document_intelligence.extract_tables(
            args["input_path"], backend=args.get("backend", "auto"),
            pages=args.get("pages", "all"),
        )
        return result.to_dict()

    async def _handle_analyze_layout(self, args):
        result = await self.sdk.document_intelligence.analyze_layout(
            args["input_path"], backend=args.get("backend", "auto"),
        )
        return result.to_dict()

    async def _handle_doc_intelligence_profiles(self, args):
        return {
            "parsing": self.sdk.document_intelligence.get_parsing_profiles(),
            "table_extraction": self.sdk.document_intelligence.get_table_profiles(),
            "layout": self.sdk.document_intelligence.get_layout_profiles(),
            "available": self.sdk.document_intelligence.get_available_backends(),
        }
    async def _handle_concat_audio(self, args):
        from ai_generation.audio_enhancement import AudioEnhanceOperation
        result = await self.sdk.audio_enhancement.execute(
            AudioEnhanceOperation.CONCAT, input_paths=args["input_paths"],
            output_path=args.get("output_path", ""),
        )
        return result.to_dict()
    async def _handle_music_profiles(self, args):
        task = args.get("task", "")
        if task:
            from ai_generation.music_generation import MusicTask
            return {"profiles": self.sdk.music_generation.get_models_for_task(MusicTask(task))}
        return {"profiles": self.sdk.music_generation.get_profiles()}
    async def _handle_probe_video(self, args):
        return self.sdk.video_editing.probe(args["input_path"])


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

    # ── Audio Handlers ──

    async def _handle_text_to_speech(self, args):
        result = await self.sdk.text_to_speech(
            text=args["text"],
            voice=args.get("voice", "default"),
            provider=args.get("provider", ""),
            output_path=args.get("output_path", ""),
            speed=args.get("speed", 1.0),
        )
        return result

    async def _handle_transcribe(self, args):
        audio_path = args["audio_path"]
        with open(audio_path, "rb") as f:
            audio_data = f.read()
        result = await self.sdk.transcribe(
            audio_data=audio_data,
            language=args.get("language", "en"),
            provider=args.get("provider", ""),
        )
        return result

    async def _handle_list_audio_providers(self, args):
        return self.sdk.list_audio_providers()

    async def _handle_get_audio_stats(self, args):
        return self.sdk.get_audio_stats()

    # ── Browser AI Handlers ──

    async def _handle_list_browser_runtimes(self, args):
        return self.sdk.list_browser_runtimes()

    async def _handle_list_browser_models(self, args):
        return self.sdk.list_browser_models(
            category=args.get("category", ""),
            runtime=args.get("runtime", ""),
        )

    async def _handle_find_browser_models(self, args):
        return self.sdk.find_browser_models(
            task_type=args["task_type"],
            max_memory_mb=args.get("max_memory_mb", 4000),
        )

    async def _handle_select_browser_runtime(self, args):
        runtime = self.sdk.select_browser_runtime(
            task_type=args["task_type"],
            needs_offline=args.get("needs_offline", False),
            needs_mobile=args.get("needs_mobile", False),
        )
        return {"selected_runtime": runtime}

    async def _handle_generate_browser_template(self, args):
        return self.sdk.generate_browser_template(
            runtime=args["runtime"],
            task_type=args["task_type"],
            model_id=args.get("model_id", ""),
        )

    async def _handle_get_browser_ai_stats(self, args):
        return self.sdk.get_browser_ai_stats()

    # ── Edge AI Handlers ──

    async def _handle_detect_edge_hardware(self, args):
        return self.sdk.detect_edge_hardware()

    async def _handle_list_edge_profiles(self, args):
        return self.sdk.list_edge_profiles(
            hardware=args.get("hardware", ""),
            platform=args.get("platform", ""),
        )

    async def _handle_find_edge_profile(self, args):
        result = self.sdk.find_optimal_edge_profile(
            task_type=args["task_type"],
            max_power_watts=args.get("max_power_watts", 100),
            min_memory_gb=args.get("min_memory_gb", 0),
        )
        return result or {"error": "No suitable edge profile found"}

    async def _handle_generate_edge_template(self, args):
        return self.sdk.generate_edge_template(
            hardware=args["hardware"],
            task_type=args["task_type"],
        )

    async def _handle_get_edge_ai_stats(self, args):
        return self.sdk.get_edge_ai_stats()

    # ── Edge AI Handlers ──

    async def _handle_detect_edge_hardware(self, args):
        return self.sdk.detect_edge_hardware()

    async def _handle_list_edge_profiles(self, args):
        return self.sdk.list_edge_profiles(
            hardware=args.get("hardware", ""),
            platform=args.get("platform", ""),
        )

    async def _handle_find_edge_profile(self, args):
        result = self.sdk.find_optimal_edge_profile(
            task_type=args["task_type"],
            max_power_watts=args.get("max_power_watts", 100),
            min_memory_gb=args.get("min_memory_gb", 0),
        )
        return result or {"error": "No suitable edge profile found"}

    async def _handle_generate_edge_template(self, args):
        return self.sdk.generate_edge_template(
            hardware=args["hardware"],
            task_type=args["task_type"],
        )

    async def _handle_get_edge_ai_stats(self, args):
        return self.sdk.get_edge_ai_stats()

    # ── Plugin System Handlers ──

    async def _handle_list_plugins(self, args):
        return self.sdk.list_plugins(
            plugin_type=args.get("plugin_type", ""),
            state=args.get("state", ""),
        )

    async def _handle_get_plugin(self, args):
        return self.sdk.get_plugin(args["plugin_id"])

    async def _handle_list_plugin_tools(self, args):
        return self.sdk.list_plugin_tools()

    async def _handle_get_plugin_stats(self, args):
        return self.sdk.get_plugin_stats()


    # ── Observability Handlers ──

    async def _handle_get_observability_metrics(self, args):
        return self.sdk.get_observability_metrics()

    async def _handle_get_observability_traces(self, args):
        return self.sdk.get_observability_traces(limit=args.get("limit", 50))

    async def _handle_get_observability_logs(self, args):
        return self.sdk.get_observability_logs(
            level=args.get("level", ""),
            source=args.get("source", ""),
            limit=args.get("limit", 100),
        )

    async def _handle_get_observability_stats(self, args):
        return self.sdk.get_observability_stats()


    # ── Search Systems Handlers ──

    async def _handle_search_index(self, args):
        return self.sdk.search_index(
            index_name=args["index_name"],
            query=args["query"],
            filter_expr=args.get("filter"),
            page=args.get("page", 1),
            hits_per_page=args.get("hits_per_page", 20),
        )

    async def _handle_search_providers(self, args):
        return self.sdk.search_providers(
            query=args["query"],
            provider_type=args.get("provider_type", ""),
            tier=args.get("tier", ""),
        )

    async def _handle_search_models(self, args):
        return self.sdk.search_models(
            query=args["query"],
            category=args.get("category", ""),
            runtime=args.get("runtime", ""),
        )

    async def _handle_list_search_indexes(self, args):
        return self.sdk.list_search_indexes()

    async def _handle_get_search_stats(self, args):
        return self.sdk.get_search_stats()


    # ── OCR Handlers ──

    async def _handle_list_ocr_providers(self, args):
        return self.sdk.list_ocr_providers()

    async def _handle_select_ocr_backend(self, args):
        return {"selected_backend": self.sdk.select_ocr_backend(
            document_type=args.get("document_type", "image"),
            language=args.get("language", "en"),
            needs_gpu=args.get("needs_gpu", False),
        )}

    async def _handle_process_ocr(self, args):
        return self.sdk.process_ocr(
            document_type=args.get("document_type", "image"),
            language=args.get("language", "en"),
            backend=args.get("backend", ""),
        )

    async def _handle_get_ocr_stats(self, args):
        return self.sdk.get_ocr_stats()


    # ── 3D Generation Handlers ──

    async def _handle_list_3d_models(self, args):
        return self.sdk.list_3d_models(mode=args.get("mode", ""))

    async def _handle_select_3d_model(self, args):
        model = self.sdk.select_3d_model(
            mode=args.get("mode", "text_to_3d"),
            max_vram_gb=args.get("max_vram_gb", 32),
        )
        return {"selected_model": model}

    async def _handle_get_3d_output_formats(self, args):
        return {"formats": self.sdk.get_3d_output_formats(args["model_id"])}

    async def _handle_get_3d_stats(self, args):
        return self.sdk.get_3d_stats()


    # ── Regression Detection Handlers ──

    async def _handle_detect_regression(self, args):
        return self.sdk.detect_regression(args["provider"], args["metrics"])

    async def _handle_get_regression_alerts(self, args):
        return self.sdk.get_regression_alerts(
            severity=args.get("severity", ""),
            provider=args.get("provider", ""),
            limit=args.get("limit", 100),
        )

    async def _handle_get_regression_stats(self, args):
        return self.sdk.get_regression_stats()


    # ── Capability Graph Handlers ──

    async def _handle_find_capability_path(self, args):
        return self.sdk.find_capability_path(
            capability=args["capability"],
            preferred_provider=args.get("preferred_provider", ""),
        )

    async def _handle_find_fallback_chain(self, args):
        return self.sdk.find_fallback_chain(
            capability=args["capability"],
            failed_provider=args.get("failed_provider", ""),
        )

    async def _handle_estimate_execution_cost(self, args):
        return self.sdk.estimate_execution_cost(args["provider"], args["capability"])

    async def _handle_get_capability_graph_stats(self, args):
        return self.sdk.get_capability_graph_stats()


    # ── Security Handlers ──

    async def _handle_list_security_users(self, args):
        return self.sdk.list_security_users()

    async def _handle_authorize_user(self, args):
        return self.sdk.authorize(args["user_id"], args["permission"])

    async def _handle_get_security_stats(self, args):
        return self.sdk.get_security_stats()

    # ── Phase 28 — Failure Recovery Handlers ──

    async def _handle_attempt_recovery(self, args):
        return self.sdk.attempt_recovery(args["error"], args["task_context"])

    async def _handle_recover_gpu_oom(self, args):
        return self.sdk.recover_gpu_oom(args["task_context"])

    async def _handle_recover_runtime_crash(self, args):
        return self.sdk.recover_runtime_crash(args["task_context"])

    async def _handle_recover_gpu_crash(self, args):
        return self.sdk.recover_gpu_crash(args["task_context"])

    async def _handle_recover_nan_inf(self, args):
        return self.sdk.recover_nan_inf(args["task_context"])

    async def _handle_get_failure_events(self, args):
        return self.sdk.get_failure_events(
            args.get("limit", 50),
            args.get("failure_type", ""),
        )

    async def _handle_get_failure_recovery_stats(self, args):
        return self.sdk.get_failure_recovery_stats()

    # ── Phase 28b — Dynamic Graph Update Handlers ──

    async def _handle_dynamic_add_node(self, args):
        return self.sdk.dynamic_graph_add_node(
            args["node_id"],
            args.get("node_type", "capability"),
            args.get("name", ""),
            args.get("attributes", {}),
        )

    async def _handle_dynamic_add_edge(self, args):
        return self.sdk.dynamic_graph_add_edge(
            args["source_id"],
            args["target_id"],
            args.get("edge_type", "supports"),
            args.get("weight", 1.0),
            args.get("attributes", {}),
        )

    async def _handle_dynamic_update_node(self, args):
        return self.sdk.dynamic_graph_update_node(args["node_id"], args["attributes"])

    async def _handle_dynamic_remove_node(self, args):
        return self.sdk.dynamic_graph_remove_node(args["node_id"])

    async def _handle_dynamic_batch_benchmark(self, args):
        return self.sdk.dynamic_graph_batch_benchmark(args["updates"])

    async def _handle_dynamic_batch_health(self, args):
        return self.sdk.dynamic_graph_batch_health(args["updates"])

    async def _handle_dynamic_get_history(self, args):
        return self.sdk.dynamic_graph_get_history(args.get("limit", 50))

    async def _handle_dynamic_get_stats(self, args):
        return self.sdk.dynamic_graph_get_stats()



    # ── Phase 29 — Local Runtime Handlers ──

    async def _handle_discover_local_runtimes(self, args):
        return await self.sdk.discover_local_runtimes()

    async def _handle_configure_local_runtime(self, args):
        return self.sdk.configure_local_runtime(args["runtime_type"], args["url"])

    async def _handle_get_local_runtime_stats(self, args):
        return self.sdk.get_local_runtime_stats()

    async def _handle_get_local_runtime_profile(self, args):
        return self.sdk.get_local_runtime_profile(args["runtime_type"])

    async def _handle_generate_local(self, args):
        return await self.sdk.generate_local(
            args["model"], args["prompt"],
            runtime=args.get("runtime", ""),
            max_tokens=args.get("max_tokens", 512),
            temperature=args.get("temperature", 0.7),
        )


    # ── Phase 30 — Security Crypto Handlers ──

    async def _handle_generate_encryption_key(self, args):
        return self.sdk.generate_encryption_key(algorithm=args.get("algorithm", "aes-256-gcm"))

    async def _handle_encrypt_data(self, args):
        return self.sdk.encrypt_data(args["data"].encode(), args.get("key_id"))

    async def _handle_get_encryption_stats(self, args):
        return self.sdk.get_encryption_stats()

    async def _handle_compute_file_checksum(self, args):
        return self.sdk.compute_file_checksum(args["file_path"], args.get("algorithm", "sha256"))

    async def _handle_verify_file_checksum(self, args):
        return self.sdk.verify_file_checksum(args["file_path"], args.get("expected"), args.get("algorithm", "sha256"))

    async def _handle_get_model_security_stats(self, args):
        return self.sdk.get_model_security_stats()

    async def _handle_get_tls_stats(self, args):
        return self.sdk.get_tls_stats()


    # ── Phase 31 — Event Bus Handlers ──

    async def _handle_event_bus_publish(self, args):
        return self.sdk.event_bus_publish_sync(
            args["subject"],
            payload=args.get("payload"),
            publisher=args.get("publisher", ""),
        )

    async def _handle_event_bus_get_history(self, args):
        return self.sdk.event_bus_get_history(
            args.get("subject"),
            args.get("limit", 50),
        )

    async def _handle_event_bus_get_subscriptions(self, args):
        return self.sdk.event_bus_get_subscriptions()

    async def _handle_get_event_bus_stats(self, args):
        return self.sdk.get_event_bus_stats()

    async def _handle_emit_event(self, args):
        return self.sdk.emit_event(args["event_type"], args.get("data"), args.get("source", ""))

    async def _handle_get_event_kernel_stats(self, args):
        return self.sdk.get_event_kernel_stats()


    # ── Phase 32 — OpenTelemetry Export Handlers ──

    async def _handle_otel_start(self, args):
        await self.sdk.otel_start()
        return {"success": True, "message": "OTLP exporter started"}

    async def _handle_otel_stop(self, args):
        await self.sdk.otel_stop()
        return {"success": True, "message": "OTLP exporter stopped"}

    async def _handle_otel_export_all(self, args):
        return await self.sdk.otel_export_all()

    async def _handle_get_otel_stats(self, args):
        return self.sdk.get_otel_stats()

    async def _handle_get_otel_history(self, args):
        return self.sdk.get_otel_history(args.get("limit", 50))

def get_mcp_generation_tools():
    return MCP_GENERATION_TOOLS
