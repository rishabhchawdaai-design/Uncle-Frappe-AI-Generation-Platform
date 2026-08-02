"""
Compatibility Matrix — Model x Runtime x Hardware routing lookup.

Based on ACOS Research: research/core_specs/COMPATIBILITY_MATRIX.md

The matrix is the lookup table for the Negotiation Engine to determine
valid execution paths. It is auto-populated from the Runtime Capability
Registry, Model Registry, and Benchmark Engine, and validated before every
routing decision. Every entry carries the evidence classification from the
research document (production / vendor / open-source / research / emerging).
"""
import json
import logging
import os
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

DEFAULT_DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "compatibility"

# Evidence classifications (COMPATIBILITY_MATRIX.md / evidence catalog)
EVIDENCE_PRODUCTION = "production"
EVIDENCE_VENDOR = "vendor"
EVIDENCE_OPEN_SOURCE = "open_source"
EVIDENCE_RESEARCH = "research"
EVIDENCE_EMERGING = "emerging"

# Hardware identifiers used across the matrix
HARDWARE_ALL = "all"
HARDWARE_NVIDIA = "nvidia"
HARDWARE_AMD = "amd"
HARDWARE_CPU = "cpu"
HARDWARE_APPLE = "apple_silicon"
HARDWARE_METAL = "metal"
HARDWARE_VULKAN = "vulkan"
HARDWARE_WEBGPU = "webgpu"
HARDWARE_WEBGL = "webgl"
HARDWARE_WASM = "wasm"
HARDWARE_JETSON = "jetson"
HARDWARE_EDGE = "edge"

# Hardware compatibility resolution order: specific -> generic
HARDWARE_FALLBACK = (
    HARDWARE_NVIDIA, HARDWARE_AMD, HARDWARE_CPU, HARDWARE_APPLE,
    HARDWARE_METAL, HARDWARE_VULKAN, HARDWARE_WEBGPU, HARDWARE_WEBGL,
    HARDWARE_WASM, HARDWARE_JETSON, HARDWARE_EDGE, HARDWARE_ALL,
)


@dataclass
class RuntimeInfo:
    """A runtime in the Runtime Capability Registry (RUNTIME_CAPABILITY_REGISTRY.md)."""

    runtime_id: str
    name: str
    category: str  # llm | image | video | audio | ocr | browser | edge
    hardware: List[str] = field(default_factory=list)
    parallel: List[str] = field(default_factory=list)  # tensor/pipeline/expert/data/sequence
    quantization: List[str] = field(default_factory=list)
    local: bool = True
    open_source: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


RUNTIME_CATALOG: Dict[str, RuntimeInfo] = {
    # ── LLM runtimes ──────────────────────────────────────────────
    "vllm": RuntimeInfo("vllm", "vLLM", "llm",
                        hardware=[HARDWARE_NVIDIA, HARDWARE_AMD],
                        parallel=["tensor", "pipeline", "expert", "data", "sequence"],
                        quantization=["awq", "gptq", "fp8", "squeezellm"]),
    "tensorrt_llm": RuntimeInfo("tensorrt_llm", "TensorRT-LLM", "llm",
                                hardware=[HARDWARE_NVIDIA],
                                parallel=["tensor", "pipeline", "expert"],
                                quantization=["int8", "fp8", "int4"]),
    "llama_cpp": RuntimeInfo("llama_cpp", "llama.cpp", "llm",
                             hardware=[HARDWARE_CPU, HARDWARE_NVIDIA, HARDWARE_APPLE,
                                       HARDWARE_METAL, HARDWARE_VULKAN],
                             parallel=[], quantization=["q2_k", "q3_k", "q4_k", "q5_k", "q6_k", "q8_0"]),
    "ollama": RuntimeInfo("ollama", "Ollama", "llm",
                          hardware=[HARDWARE_ALL],
                          parallel=[], quantization=["q4_k", "q8_0"]),
    "tgi": RuntimeInfo("tgi", "HuggingFace TGI", "llm",
                       hardware=[HARDWARE_NVIDIA],
                       parallel=["tensor"], quantization=["awq", "gptq", "fp8"]),
    "onnx_rt": RuntimeInfo("onnx_rt", "ONNX Runtime", "llm",
                           hardware=[HARDWARE_CPU, HARDWARE_NVIDIA, HARDWARE_APPLE],
                           parallel=[], quantization=["int8", "int4", "fp16"]),
    "deepspeed": RuntimeInfo("deepspeed", "DeepSpeed", "llm",
                             hardware=[HARDWARE_NVIDIA],
                             parallel=["tensor", "pipeline", "expert", "data"],
                             quantization=["int8", "fp8"]),
    "sglang": RuntimeInfo("sglang", "SGLang", "llm",
                          hardware=[HARDWARE_NVIDIA, HARDWARE_AMD],
                          parallel=["tensor", "pipeline", "data"],
                          quantization=["awq", "gptq", "fp8"]),
    # ── Image runtimes ────────────────────────────────────────────
    "diffusers": RuntimeInfo("diffusers", "HuggingFace Diffusers", "image",
                             hardware=[HARDWARE_ALL],
                             parallel=["data"],
                             quantization=["fp16", "fp8", "int8"]),
    "comfyui": RuntimeInfo("comfyui", "ComfyUI", "image",
                           hardware=[HARDWARE_ALL],
                           parallel=[], quantization=["fp16", "fp8"]),
    "forge": RuntimeInfo("forge", "Forge", "image",
                         hardware=[HARDWARE_NVIDIA],
                         parallel=[], quantization=["fp16"]),
    "a1111": RuntimeInfo("a1111", "AUTOMATIC1111", "image",
                         hardware=[HARDWARE_NVIDIA],
                         parallel=[], quantization=["fp16"]),
    "invokeai": RuntimeInfo("invokeai", "InvokeAI", "image",
                            hardware=[HARDWARE_NVIDIA],
                            parallel=[], quantization=["fp16"]),
    "tensorrt_image": RuntimeInfo("tensorrt_image", "TensorRT (image)", "image",
                                  hardware=[HARDWARE_NVIDIA],
                                  parallel=[], quantization=["fp16", "int8"]),
    "onnx_rt_image": RuntimeInfo("onnx_rt_image", "ONNX Runtime (image)", "image",
                                 hardware=[HARDWARE_ALL],
                                 parallel=[], quantization=["fp16", "int8"]),
    # ── Video runtimes ────────────────────────────────────────────
    "diffusers_video": RuntimeInfo("diffusers_video", "Diffusers (video)", "video",
                                   hardware=[HARDWARE_NVIDIA],
                                   parallel=[], quantization=["fp16"]),
    "comfyui_video": RuntimeInfo("comfyui_video", "ComfyUI (video)", "video",
                                 hardware=[HARDWARE_NVIDIA],
                                 parallel=[], quantization=["fp16"]),
    "custom_video": RuntimeInfo("custom_video", "Custom video runtime", "video",
                                hardware=[HARDWARE_NVIDIA],
                                parallel=["tensor", "pipeline"],
                                quantization=["fp16", "fp8"]),
    # ── Audio runtimes ────────────────────────────────────────────
    "whisper_py": RuntimeInfo("whisper_py", "Whisper (Python)", "audio",
                              hardware=[HARDWARE_ALL],
                              parallel=[], quantization=["fp16", "int8"]),
    "whisper_cpp": RuntimeInfo("whisper_cpp", "whisper.cpp", "audio",
                               hardware=[HARDWARE_ALL],
                               parallel=[], quantization=["q4_0", "q5_0", "q8_0"]),
    "piper": RuntimeInfo("piper", "Piper", "audio",
                         hardware=[HARDWARE_CPU],
                         parallel=[], quantization=["int8"]),
    "xtts": RuntimeInfo("xtts", "XTTS", "audio",
                        hardware=[HARDWARE_NVIDIA],
                        parallel=[], quantization=["fp16"]),
    "kokoro": RuntimeInfo("kokoro", "Kokoro", "audio",
                          hardware=[HARDWARE_CPU, HARDWARE_NVIDIA],
                          parallel=[], quantization=["fp16"]),
    "fish_speech": RuntimeInfo("fish_speech", "Fish Speech", "audio",
                               hardware=[HARDWARE_NVIDIA],
                               parallel=[], quantization=["fp16"]),
    # ── OCR / document runtimes ───────────────────────────────────
    "paddleocr": RuntimeInfo("paddleocr", "PaddleOCR", "ocr",
                             hardware=[HARDWARE_CPU, HARDWARE_NVIDIA],
                             parallel=[], quantization=["fp16"]),
    "tesseract": RuntimeInfo("tesseract", "Tesseract", "ocr",
                             hardware=[HARDWARE_CPU],
                             parallel=[], quantization=[]),
    "surya": RuntimeInfo("surya", "Surya", "ocr",
                         hardware=[HARDWARE_CPU, HARDWARE_NVIDIA],
                         parallel=[], quantization=["fp16"]),
    "marker": RuntimeInfo("marker", "Marker", "ocr",
                          hardware=[HARDWARE_CPU, HARDWARE_NVIDIA],
                          parallel=[], quantization=["fp16"]),
    "docling": RuntimeInfo("docling", "Docling", "ocr",
                           hardware=[HARDWARE_CPU, HARDWARE_NVIDIA],
                           parallel=[], quantization=["fp16"]),
    "mineru": RuntimeInfo("mineru", "MinerU", "ocr",
                          hardware=[HARDWARE_CPU, HARDWARE_NVIDIA],
                          parallel=[], quantization=["fp16"]),
    # ── Browser runtimes ──────────────────────────────────────────
    "transformers_js": RuntimeInfo("transformers_js", "Transformers.js", "browser",
                                   hardware=[HARDWARE_WASM, HARDWARE_WEBGPU],
                                   parallel=[], quantization=["q8"]),
    "webllm": RuntimeInfo("webllm", "WebLLM", "browser",
                          hardware=[HARDWARE_WEBGPU],
                          parallel=[], quantization=["q4"]),
    "onnx_rt_web": RuntimeInfo("onnx_rt_web", "ONNX Runtime Web", "browser",
                               hardware=[HARDWARE_WASM, HARDWARE_WEBGPU],
                               parallel=[], quantization=["int8"]),
    "tfjs": RuntimeInfo("tfjs", "TensorFlow.js", "browser",
                        hardware=[HARDWARE_WEBGL],
                        parallel=[], quantization=["int8"]),
    # ── Edge runtimes ─────────────────────────────────────────────
    "coreml": RuntimeInfo("coreml", "Core ML", "edge",
                          hardware=[HARDWARE_APPLE],
                          parallel=[], quantization=["int8", "fp16"]),
    "snpe": RuntimeInfo("snpe", "Qualcomm SNPE", "edge",
                        hardware=[HARDWARE_EDGE],
                        parallel=[], quantization=["int8"]),
    "openvino": RuntimeInfo("openvino", "OpenVINO", "edge",
                            hardware=[HARDWARE_CPU, HARDWARE_EDGE, HARDWARE_NVIDIA],
                            parallel=[], quantization=["int8", "fp16"]),
    "tensorrt_edge": RuntimeInfo("tensorrt_edge", "TensorRT (edge)", "edge",
                                 hardware=[HARDWARE_NVIDIA, HARDWARE_JETSON],
                                 parallel=[], quantization=["int8", "fp16"]),
    "tflite": RuntimeInfo("tflite", "TFLite", "edge",
                          hardware=[HARDWARE_EDGE],
                          parallel=[], quantization=["int8", "fp16"]),
    "onnx_mobile": RuntimeInfo("onnx_mobile", "ONNX Mobile", "edge",
                               hardware=[HARDWARE_EDGE],
                               parallel=[], quantization=["int8", "fp16"]),
}


def _seed(rows: List[tuple]) -> List["CompatibilityEntry"]:
    """Expand compact seed rows: (model, runtime, hardware, score, quant, res, ctx, evidence)."""
    entries = []
    for row in rows:
        model, runtime, hardware, score, quant, res, ctx, evidence = row
        entries.append(CompatibilityEntry(
            model_id=model, runtime_id=runtime, hardware_id=hardware,
            compatible=True, performance_score=score,
            quantization=list(quant) if isinstance(quant, (list, tuple)) else [quant] if quant else [],
            max_resolution=res, max_context=int(ctx or 0),
            verified_date=datetime.now(timezone.utc).date().isoformat(),
            evidence=evidence,
        ))
    return entries


# Seed data transcribed from COMPATIBILITY_MATRIX.md sections 3-9.
def seed_entries() -> List["CompatibilityEntry"]:
    now = datetime.now(timezone.utc).date().isoformat()
    rows = [
        # 3. LLM matrix (model, runtime, hardware, score, quant, res, ctx, evidence)
        ("llama3_8b", "vllm", HARDWARE_NVIDIA, 0.86, ["fp16"], "", 8192, EVIDENCE_PRODUCTION),
        ("llama3_8b", "tensorrt_llm", HARDWARE_NVIDIA, 0.86, ["fp16"], "", 8192, EVIDENCE_PRODUCTION),
        ("llama3_8b", "llama_cpp", HARDWARE_ALL, 0.78, ["q4_k"], "", 8192, EVIDENCE_PRODUCTION),
        ("llama3_8b", "ollama", HARDWARE_ALL, 0.80, ["q4_k"], "", 8192, EVIDENCE_PRODUCTION),
        ("llama3_8b", "tgi", HARDWARE_NVIDIA, 0.85, ["fp16"], "", 8192, EVIDENCE_PRODUCTION),
        ("llama3_8b", "onnx_rt", HARDWARE_ALL, 0.74, ["int8"], "", 8192, EVIDENCE_PRODUCTION),
        ("llama3_8b", "deepspeed", HARDWARE_NVIDIA, 0.84, ["fp16"], "", 8192, EVIDENCE_PRODUCTION),
        ("llama3_8b", "sglang", HARDWARE_NVIDIA, 0.85, ["fp16"], "", 8192, EVIDENCE_PRODUCTION),
        ("llama3_70b", "vllm", HARDWARE_NVIDIA, 0.90, ["fp16"], "", 8192, EVIDENCE_PRODUCTION),
        ("llama3_70b", "tensorrt_llm", HARDWARE_NVIDIA, 0.90, ["fp16"], "", 8192, EVIDENCE_PRODUCTION),
        ("llama3_70b", "llama_cpp", HARDWARE_ALL, 0.72, ["q4_k"], "", 8192, EVIDENCE_PRODUCTION),
        ("llama3_70b", "ollama", HARDWARE_ALL, 0.74, ["q4_k"], "", 8192, EVIDENCE_PRODUCTION),
        ("llama3_70b", "tgi", HARDWARE_NVIDIA, 0.89, ["fp16"], "", 8192, EVIDENCE_PRODUCTION),
        ("llama3_70b", "onnx_rt", HARDWARE_ALL, 0.68, ["int8"], "", 8192, EVIDENCE_PRODUCTION),
        ("llama3_70b", "deepspeed", HARDWARE_NVIDIA, 0.89, ["fp16"], "", 8192, EVIDENCE_PRODUCTION),
        ("mixtral_8x7b", "vllm", HARDWARE_NVIDIA, 0.87, ["fp16"], "", 32768, EVIDENCE_PRODUCTION),
        ("mixtral_8x7b", "tensorrt_llm", HARDWARE_NVIDIA, 0.87, ["fp16"], "", 32768, EVIDENCE_PRODUCTION),
        ("mixtral_8x7b", "llama_cpp", HARDWARE_ALL, 0.75, ["q4_k"], "", 32768, EVIDENCE_PRODUCTION),
        ("mixtral_8x7b", "ollama", HARDWARE_ALL, 0.77, ["q4_k"], "", 32768, EVIDENCE_PRODUCTION),
        ("mixtral_8x7b", "tgi", HARDWARE_NVIDIA, 0.86, ["fp16"], "", 32768, EVIDENCE_PRODUCTION),
        ("mixtral_8x7b", "onnx_rt", HARDWARE_ALL, 0.70, ["int8"], "", 32768, EVIDENCE_PRODUCTION),
        ("mixtral_8x7b", "deepspeed", HARDWARE_NVIDIA, 0.86, ["fp16"], "", 32768, EVIDENCE_PRODUCTION),
        ("qwen2_72b", "vllm", HARDWARE_NVIDIA, 0.88, ["fp16"], "", 131072, EVIDENCE_PRODUCTION),
        ("qwen2_72b", "tensorrt_llm", HARDWARE_NVIDIA, 0.88, ["fp16"], "", 131072, EVIDENCE_PRODUCTION),
        ("qwen2_72b", "llama_cpp", HARDWARE_ALL, 0.71, ["q4_k"], "", 131072, EVIDENCE_PRODUCTION),
        ("qwen2_72b", "ollama", HARDWARE_ALL, 0.73, ["q4_k"], "", 131072, EVIDENCE_PRODUCTION),
        ("qwen2_72b", "tgi", HARDWARE_NVIDIA, 0.87, ["fp16"], "", 131072, EVIDENCE_PRODUCTION),
        ("qwen2_72b", "onnx_rt", HARDWARE_ALL, 0.67, ["int8"], "", 131072, EVIDENCE_PRODUCTION),
        ("qwen2_72b", "deepspeed", HARDWARE_NVIDIA, 0.87, ["fp16"], "", 131072, EVIDENCE_PRODUCTION),
        ("phi3_4b", "vllm", HARDWARE_NVIDIA, 0.82, ["fp16"], "", 4096, EVIDENCE_PRODUCTION),
        ("phi3_4b", "tensorrt_llm", HARDWARE_NVIDIA, 0.82, ["fp16"], "", 4096, EVIDENCE_PRODUCTION),
        ("phi3_4b", "llama_cpp", HARDWARE_ALL, 0.76, ["q4_k"], "", 4096, EVIDENCE_PRODUCTION),
        ("phi3_4b", "ollama", HARDWARE_ALL, 0.78, ["q4_k"], "", 4096, EVIDENCE_PRODUCTION),
        ("phi3_4b", "tgi", HARDWARE_NVIDIA, 0.81, ["fp16"], "", 4096, EVIDENCE_PRODUCTION),
        ("phi3_4b", "onnx_rt", HARDWARE_ALL, 0.75, ["int8"], "", 4096, EVIDENCE_PRODUCTION),
        ("phi3_4b", "deepspeed", HARDWARE_NVIDIA, 0.80, ["fp16"], "", 4096, EVIDENCE_PRODUCTION),
        ("gemma2_27b", "vllm", HARDWARE_NVIDIA, 0.85, ["fp16"], "", 8192, EVIDENCE_PRODUCTION),
        ("gemma2_27b", "tensorrt_llm", HARDWARE_NVIDIA, 0.85, ["fp16"], "", 8192, EVIDENCE_PRODUCTION),
        ("gemma2_27b", "llama_cpp", HARDWARE_ALL, 0.73, ["q4_k"], "", 8192, EVIDENCE_PRODUCTION),
        ("gemma2_27b", "ollama", HARDWARE_ALL, 0.75, ["q4_k"], "", 8192, EVIDENCE_PRODUCTION),
        ("gemma2_27b", "tgi", HARDWARE_NVIDIA, 0.84, ["fp16"], "", 8192, EVIDENCE_PRODUCTION),
        ("gemma2_27b", "onnx_rt", HARDWARE_ALL, 0.69, ["int8"], "", 8192, EVIDENCE_PRODUCTION),
        ("gemma2_27b", "deepspeed", HARDWARE_NVIDIA, 0.84, ["fp16"], "", 8192, EVIDENCE_PRODUCTION),
        ("mistral_7b", "vllm", HARDWARE_NVIDIA, 0.84, ["fp16"], "", 32768, EVIDENCE_PRODUCTION),
        ("mistral_7b", "tensorrt_llm", HARDWARE_NVIDIA, 0.84, ["fp16"], "", 32768, EVIDENCE_PRODUCTION),
        ("mistral_7b", "llama_cpp", HARDWARE_ALL, 0.77, ["q4_k"], "", 32768, EVIDENCE_PRODUCTION),
        ("mistral_7b", "ollama", HARDWARE_ALL, 0.79, ["q4_k"], "", 32768, EVIDENCE_PRODUCTION),
        ("mistral_7b", "tgi", HARDWARE_NVIDIA, 0.83, ["fp16"], "", 32768, EVIDENCE_PRODUCTION),
        ("mistral_7b", "onnx_rt", HARDWARE_ALL, 0.73, ["int8"], "", 32768, EVIDENCE_PRODUCTION),
        ("mistral_7b", "deepspeed", HARDWARE_NVIDIA, 0.83, ["fp16"], "", 32768, EVIDENCE_PRODUCTION),
        ("starcoder2_15b", "vllm", HARDWARE_NVIDIA, 0.83, ["fp16"], "", 16384, EVIDENCE_PRODUCTION),
        ("starcoder2_15b", "tensorrt_llm", HARDWARE_NVIDIA, 0.83, ["fp16"], "", 16384, EVIDENCE_PRODUCTION),
        ("starcoder2_15b", "llama_cpp", HARDWARE_ALL, 0.74, ["q4_k"], "", 16384, EVIDENCE_PRODUCTION),
        ("starcoder2_15b", "ollama", HARDWARE_ALL, 0.76, ["q4_k"], "", 16384, EVIDENCE_PRODUCTION),
        ("starcoder2_15b", "tgi", HARDWARE_NVIDIA, 0.82, ["fp16"], "", 16384, EVIDENCE_PRODUCTION),
        ("starcoder2_15b", "onnx_rt", HARDWARE_ALL, 0.70, ["int8"], "", 16384, EVIDENCE_PRODUCTION),
        ("starcoder2_15b", "deepspeed", HARDWARE_NVIDIA, 0.82, ["fp16"], "", 16384, EVIDENCE_PRODUCTION),
        # 4. Image matrix
        ("sd_1_5", "diffusers", HARDWARE_ALL, 0.78, ["fp16"], "512x512", 0, EVIDENCE_PRODUCTION),
        ("sd_1_5", "comfyui", HARDWARE_ALL, 0.80, ["fp16"], "512x512", 0, EVIDENCE_PRODUCTION),
        ("sd_1_5", "forge", HARDWARE_NVIDIA, 0.79, ["fp16"], "512x512", 0, EVIDENCE_PRODUCTION),
        ("sd_1_5", "a1111", HARDWARE_NVIDIA, 0.78, ["fp16"], "512x512", 0, EVIDENCE_PRODUCTION),
        ("sd_1_5", "invokeai", HARDWARE_NVIDIA, 0.79, ["fp16"], "512x512", 0, EVIDENCE_PRODUCTION),
        ("sd_1_5", "tensorrt_image", HARDWARE_NVIDIA, 0.82, ["fp16"], "512x512", 0, EVIDENCE_PRODUCTION),
        ("sd_1_5", "onnx_rt_image", HARDWARE_ALL, 0.76, ["fp16"], "512x512", 0, EVIDENCE_PRODUCTION),
        ("sdxl", "diffusers", HARDWARE_ALL, 0.86, ["fp16"], "1024x1024", 0, EVIDENCE_PRODUCTION),
        ("sdxl", "comfyui", HARDWARE_ALL, 0.88, ["fp16"], "1024x1024", 0, EVIDENCE_PRODUCTION),
        ("sdxl", "forge", HARDWARE_NVIDIA, 0.87, ["fp16"], "1024x1024", 0, EVIDENCE_PRODUCTION),
        ("sdxl", "a1111", HARDWARE_NVIDIA, 0.86, ["fp16"], "1024x1024", 0, EVIDENCE_PRODUCTION),
        ("sdxl", "invokeai", HARDWARE_NVIDIA, 0.87, ["fp16"], "1024x1024", 0, EVIDENCE_PRODUCTION),
        ("sdxl", "tensorrt_image", HARDWARE_NVIDIA, 0.90, ["fp16"], "1024x1024", 0, EVIDENCE_PRODUCTION),
        ("sdxl", "onnx_rt_image", HARDWARE_ALL, 0.84, ["fp16"], "1024x1024", 0, EVIDENCE_PRODUCTION),
        ("flux_1_dev", "diffusers", HARDWARE_NVIDIA, 0.93, ["fp8"], "1024x1024", 0, EVIDENCE_RESEARCH),
        ("flux_1_dev", "comfyui", HARDWARE_NVIDIA, 0.93, ["fp8"], "1024x1024", 0, EVIDENCE_RESEARCH),
        ("flux_1_dev", "forge", HARDWARE_NVIDIA, 0.92, ["fp8"], "1024x1024", 0, EVIDENCE_RESEARCH),
        ("flux_1_dev", "tensorrt_image", HARDWARE_NVIDIA, 0.94, ["fp8"], "1024x1024", 0, EVIDENCE_RESEARCH),
        ("flux_1_dev", "onnx_rt_image", HARDWARE_ALL, 0.90, ["fp8"], "1024x1024", 0, EVIDENCE_RESEARCH),
        ("flux_1_schnell", "diffusers", HARDWARE_NVIDIA, 0.91, ["fp8"], "1024x1024", 0, EVIDENCE_RESEARCH),
        ("flux_1_schnell", "comfyui", HARDWARE_NVIDIA, 0.91, ["fp8"], "1024x1024", 0, EVIDENCE_RESEARCH),
        ("flux_1_schnell", "forge", HARDWARE_NVIDIA, 0.90, ["fp8"], "1024x1024", 0, EVIDENCE_RESEARCH),
        ("flux_1_schnell", "tensorrt_image", HARDWARE_NVIDIA, 0.92, ["fp8"], "1024x1024", 0, EVIDENCE_RESEARCH),
        ("flux_1_schnell", "onnx_rt_image", HARDWARE_ALL, 0.89, ["fp8"], "1024x1024", 0, EVIDENCE_RESEARCH),
        ("controlnet", "diffusers", HARDWARE_ALL, 0.84, ["fp16"], "1024x1024", 0, EVIDENCE_PRODUCTION),
        ("controlnet", "comfyui", HARDWARE_ALL, 0.86, ["fp16"], "1024x1024", 0, EVIDENCE_PRODUCTION),
        ("controlnet", "forge", HARDWARE_NVIDIA, 0.85, ["fp16"], "1024x1024", 0, EVIDENCE_PRODUCTION),
        ("controlnet", "a1111", HARDWARE_NVIDIA, 0.84, ["fp16"], "1024x1024", 0, EVIDENCE_PRODUCTION),
        ("controlnet", "invokeai", HARDWARE_NVIDIA, 0.85, ["fp16"], "1024x1024", 0, EVIDENCE_PRODUCTION),
        ("ip_adapter", "diffusers", HARDWARE_ALL, 0.85, ["fp16"], "1024x1024", 0, EVIDENCE_PRODUCTION),
        ("ip_adapter", "comfyui", HARDWARE_ALL, 0.87, ["fp16"], "1024x1024", 0, EVIDENCE_PRODUCTION),
        ("ip_adapter", "forge", HARDWARE_NVIDIA, 0.86, ["fp16"], "1024x1024", 0, EVIDENCE_PRODUCTION),
        ("ip_adapter", "a1111", HARDWARE_NVIDIA, 0.85, ["fp16"], "1024x1024", 0, EVIDENCE_PRODUCTION),
        ("ip_adapter", "invokeai", HARDWARE_NVIDIA, 0.86, ["fp16"], "1024x1024", 0, EVIDENCE_PRODUCTION),
        ("animatediff", "diffusers", HARDWARE_NVIDIA, 0.83, ["fp16"], "512x512", 0, EVIDENCE_PRODUCTION),
        ("animatediff", "comfyui", HARDWARE_NVIDIA, 0.84, ["fp16"], "512x512", 0, EVIDENCE_PRODUCTION),
        ("animatediff", "forge", HARDWARE_NVIDIA, 0.83, ["fp16"], "512x512", 0, EVIDENCE_PRODUCTION),
        ("animatediff", "a1111", HARDWARE_NVIDIA, 0.82, ["fp16"], "512x512", 0, EVIDENCE_PRODUCTION),
        # 5. Video matrix
        ("cogvideox_2b", "diffusers_video", HARDWARE_NVIDIA, 0.82, ["fp16"], "480p", 0, EVIDENCE_RESEARCH),
        ("cogvideox_2b", "comfyui_video", HARDWARE_NVIDIA, 0.84, ["fp16"], "480p", 0, EVIDENCE_RESEARCH),
        ("cogvideox_2b", "custom_video", HARDWARE_NVIDIA, 0.83, ["fp16"], "480p", 0, EVIDENCE_RESEARCH),
        ("cogvideox_5b", "diffusers_video", HARDWARE_NVIDIA, 0.86, ["fp16"], "720p", 0, EVIDENCE_RESEARCH),
        ("cogvideox_5b", "comfyui_video", HARDWARE_NVIDIA, 0.88, ["fp16"], "720p", 0, EVIDENCE_RESEARCH),
        ("cogvideox_5b", "custom_video", HARDWARE_NVIDIA, 0.87, ["fp16"], "720p", 0, EVIDENCE_RESEARCH),
        ("open_sora", "comfyui_video", HARDWARE_NVIDIA, 0.89, ["fp16"], "720p", 0, EVIDENCE_RESEARCH),
        ("open_sora", "custom_video", HARDWARE_NVIDIA, 0.90, ["fp16"], "720p", 0, EVIDENCE_RESEARCH),
        ("ltx_video", "diffusers_video", HARDWARE_NVIDIA, 0.84, ["fp16"], "720p", 0, EVIDENCE_RESEARCH),
        ("ltx_video", "comfyui_video", HARDWARE_NVIDIA, 0.86, ["fp16"], "720p", 0, EVIDENCE_RESEARCH),
        ("ltx_video", "custom_video", HARDWARE_NVIDIA, 0.85, ["fp16"], "720p", 0, EVIDENCE_RESEARCH),
        ("mochi", "comfyui_video", HARDWARE_NVIDIA, 0.87, ["fp16"], "480p", 0, EVIDENCE_RESEARCH),
        ("mochi", "custom_video", HARDWARE_NVIDIA, 0.88, ["fp16"], "480p", 0, EVIDENCE_RESEARCH),
        ("animatediff_video", "diffusers_video", HARDWARE_NVIDIA, 0.81, ["fp16"], "512px", 0, EVIDENCE_PRODUCTION),
        ("animatediff_video", "comfyui_video", HARDWARE_NVIDIA, 0.82, ["fp16"], "512px", 0, EVIDENCE_PRODUCTION),
        ("animatediff_video", "custom_video", HARDWARE_NVIDIA, 0.81, ["fp16"], "512px", 0, EVIDENCE_PRODUCTION),
        # 6. Audio matrix
        ("whisper_large_v3", "whisper_py", HARDWARE_ALL, 0.92, ["fp16"], "", 0, EVIDENCE_PRODUCTION),
        ("whisper_large_v3", "whisper_cpp", HARDWARE_ALL, 0.90, ["q8_0"], "", 0, EVIDENCE_PRODUCTION),
        ("whisper_medium", "whisper_py", HARDWARE_ALL, 0.88, ["fp16"], "", 0, EVIDENCE_PRODUCTION),
        ("whisper_medium", "whisper_cpp", HARDWARE_ALL, 0.86, ["q8_0"], "", 0, EVIDENCE_PRODUCTION),
        ("whisper_tiny", "whisper_py", HARDWARE_ALL, 0.76, ["fp16"], "", 0, EVIDENCE_PRODUCTION),
        ("whisper_tiny", "whisper_cpp", HARDWARE_ALL, 0.75, ["q8_0"], "", 0, EVIDENCE_PRODUCTION),
        ("piper_v2", "piper", HARDWARE_CPU, 0.85, ["int8"], "", 0, EVIDENCE_PRODUCTION),
        ("xtts_v2", "xtts", HARDWARE_NVIDIA, 0.90, ["fp16"], "", 0, EVIDENCE_PRODUCTION),
        ("kokoro_tts", "kokoro", HARDWARE_ALL, 0.87, ["fp16"], "", 0, EVIDENCE_RESEARCH),
        ("fish_speech", "fish_speech", HARDWARE_NVIDIA, 0.89, ["fp16"], "", 0, EVIDENCE_RESEARCH),
        # 7. OCR matrix
        ("ppocr_v4", "paddleocr", HARDWARE_ALL, 0.86, ["fp16"], "", 0, EVIDENCE_PRODUCTION),
        ("tesseract_5", "tesseract", HARDWARE_CPU, 0.78, [], "", 0, EVIDENCE_PRODUCTION),
        ("surya_v1", "surya", HARDWARE_ALL, 0.90, ["fp16"], "", 0, EVIDENCE_RESEARCH),
        ("surya_v1", "marker", HARDWARE_ALL, 0.85, ["fp16"], "", 0, EVIDENCE_RESEARCH),
        ("marker", "marker", HARDWARE_ALL, 0.88, ["fp16"], "", 0, EVIDENCE_RESEARCH),
        ("marker", "surya", HARDWARE_ALL, 0.84, ["fp16"], "", 0, EVIDENCE_RESEARCH),
        ("nougat", "docling", HARDWARE_ALL, 0.82, ["fp16"], "", 0, EVIDENCE_RESEARCH),
        # 8. Browser matrix
        ("bert_base", "transformers_js", HARDWARE_ALL, 0.80, ["q8"], "", 512, EVIDENCE_PRODUCTION),
        ("bert_base", "onnx_rt_web", HARDWARE_ALL, 0.79, ["int8"], "", 512, EVIDENCE_PRODUCTION),
        ("bert_base", "tfjs", HARDWARE_WEBGL, 0.76, ["int8"], "", 512, EVIDENCE_PRODUCTION),
        ("distilbert", "transformers_js", HARDWARE_ALL, 0.78, ["q8"], "", 512, EVIDENCE_PRODUCTION),
        ("distilbert", "onnx_rt_web", HARDWARE_ALL, 0.77, ["int8"], "", 512, EVIDENCE_PRODUCTION),
        ("distilbert", "tfjs", HARDWARE_WEBGL, 0.74, ["int8"], "", 512, EVIDENCE_PRODUCTION),
        ("t5_small", "transformers_js", HARDWARE_WASM, 0.75, ["q8"], "", 512, EVIDENCE_PRODUCTION),
        ("t5_small", "tfjs", HARDWARE_WEBGL, 0.72, ["int8"], "", 512, EVIDENCE_PRODUCTION),
        ("phi2", "webllm", HARDWARE_WEBGPU, 0.81, ["q4"], "", 2048, EVIDENCE_RESEARCH),
        ("qwen1_5_0_5b", "webllm", HARDWARE_WEBGPU, 0.77, ["q4"], "", 2048, EVIDENCE_RESEARCH),
        ("sd_turbo_browser", "transformers_js", HARDWARE_WEBGPU, 0.83, ["q8"], "512x512", 0, EVIDENCE_RESEARCH),
        ("sd_turbo_browser", "onnx_rt_web", HARDWARE_WEBGPU, 0.82, ["int8"], "512x512", 0, EVIDENCE_RESEARCH),
        # 9. Edge matrix
        ("mobilenet_v3", "coreml", HARDWARE_APPLE, 0.84, ["int8"], "", 0, EVIDENCE_PRODUCTION),
        ("mobilenet_v3", "snpe", HARDWARE_EDGE, 0.82, ["int8"], "", 0, EVIDENCE_PRODUCTION),
        ("mobilenet_v3", "openvino", HARDWARE_ALL, 0.83, ["int8"], "", 0, EVIDENCE_PRODUCTION),
        ("mobilenet_v3", "tensorrt_edge", HARDWARE_NVIDIA, 0.85, ["int8"], "", 0, EVIDENCE_PRODUCTION),
        ("mobilenet_v3", "tflite", HARDWARE_EDGE, 0.81, ["int8"], "", 0, EVIDENCE_PRODUCTION),
        ("mobilenet_v3", "onnx_mobile", HARDWARE_EDGE, 0.80, ["int8"], "", 0, EVIDENCE_PRODUCTION),
        ("efficientnet", "coreml", HARDWARE_APPLE, 0.86, ["int8"], "", 0, EVIDENCE_PRODUCTION),
        ("efficientnet", "snpe", HARDWARE_EDGE, 0.84, ["int8"], "", 0, EVIDENCE_PRODUCTION),
        ("efficientnet", "openvino", HARDWARE_ALL, 0.85, ["int8"], "", 0, EVIDENCE_PRODUCTION),
        ("efficientnet", "tensorrt_edge", HARDWARE_NVIDIA, 0.87, ["int8"], "", 0, EVIDENCE_PRODUCTION),
        ("efficientnet", "tflite", HARDWARE_EDGE, 0.83, ["int8"], "", 0, EVIDENCE_PRODUCTION),
        ("efficientnet", "onnx_mobile", HARDWARE_EDGE, 0.82, ["int8"], "", 0, EVIDENCE_PRODUCTION),
        ("whisper_tiny_edge", "openvino", HARDWARE_ALL, 0.78, ["int8"], "", 0, EVIDENCE_PRODUCTION),
        ("whisper_tiny_edge", "tensorrt_edge", HARDWARE_NVIDIA, 0.80, ["int8"], "", 0, EVIDENCE_PRODUCTION),
        ("whisper_tiny_edge", "tflite", HARDWARE_EDGE, 0.76, ["int8"], "", 0, EVIDENCE_PRODUCTION),
        ("whisper_tiny_edge", "onnx_mobile", HARDWARE_EDGE, 0.75, ["int8"], "", 0, EVIDENCE_PRODUCTION),
        ("llama3_8b_q4_edge", "tensorrt_edge", HARDWARE_JETSON, 0.72, ["int8"], "", 8192, EVIDENCE_RESEARCH),
        ("sd_turbo_edge", "coreml", HARDWARE_APPLE, 0.80, ["int8"], "512x512", 0, EVIDENCE_RESEARCH),
        ("sd_turbo_edge", "openvino", HARDWARE_ALL, 0.81, ["int8"], "512x512", 0, EVIDENCE_RESEARCH),
        ("sd_turbo_edge", "tensorrt_edge", HARDWARE_NVIDIA, 0.83, ["int8"], "512x512", 0, EVIDENCE_RESEARCH),
        ("sd_turbo_edge", "onnx_mobile", HARDWARE_EDGE, 0.79, ["int8"], "512x512", 0, EVIDENCE_RESEARCH),
    ]
    return _seed(rows)


@dataclass
class CompatibilityEntry:
    """One Model x Runtime x Hardware compatibility record."""

    model_id: str
    runtime_id: str
    hardware_id: str = HARDWARE_ALL
    compatible: bool = True
    performance_score: float = 0.5
    quantization: List[str] = field(default_factory=list)
    max_resolution: str = ""
    max_context: int = 0
    verified_date: str = ""
    evidence: str = EVIDENCE_RESEARCH

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "CompatibilityEntry":
        return CompatibilityEntry(
            model_id=d.get("model_id", ""),
            runtime_id=d.get("runtime_id", ""),
            hardware_id=d.get("hardware_id", HARDWARE_ALL),
            compatible=d.get("compatible", True),
            performance_score=d.get("performance_score", 0.5),
            quantization=list(d.get("quantization") or []),
            max_resolution=d.get("max_resolution", ""),
            max_context=d.get("max_context", 0),
            verified_date=d.get("verified_date", ""),
            evidence=d.get("evidence", EVIDENCE_RESEARCH),
        )

    def key(self) -> tuple:
        return (self.model_id, self.runtime_id, self.hardware_id)


class CompatibilityMatrix:
    """Model x Runtime x Hardware lookup table for execution-path validation."""

    def __init__(self, data_dir: Optional[str] = None):
        self.data_dir = Path(data_dir or os.environ.get("ACOS_DATA_DIR") or DEFAULT_DATA_DIR)
        self._entries: Dict[tuple, CompatibilityEntry] = {}
        self._runtimes: Dict[str, RuntimeInfo] = dict(RUNTIME_CATALOG)
        self._load()
        if not self._entries:
            self._seed_defaults()
            self._persist()

    # ── persistence ───────────────────────────────────────────────

    def _load(self):
        path = self.data_dir / "compatibility_matrix.json"
        if not path.exists():
            return
        try:
            data = json.loads(path.read_text())
            for raw in data.get("entries", []):
                entry = CompatibilityEntry.from_dict(raw)
                self._entries[entry.key()] = entry
        except Exception as exc:  # pragma: no cover - corrupted registry
            logger.warning("compatibility matrix load failed: %s", exc)

    def _persist(self):
        self.data_dir.mkdir(parents=True, exist_ok=True)
        payload = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "entries": [e.to_dict() for e in self._entries.values()],
        }
        (self.data_dir / "compatibility_matrix.json").write_text(
            json.dumps(payload, indent=2, default=str))

    def _seed_defaults(self):
        for entry in seed_entries():
            self._entries[entry.key()] = entry

    # ── registration ──────────────────────────────────────────────

    def register(self, entry: CompatibilityEntry) -> Dict[str, Any]:
        self._entries[entry.key()] = entry
        self._persist()
        return {"registered": entry.to_dict(), "total_entries": len(self._entries)}

    def register_many(self, entries: List[CompatibilityEntry]) -> Dict[str, Any]:
        added = 0
        for entry in entries:
            if entry.key() not in self._entries:
                added += 1
            self._entries[entry.key()] = entry
        self._persist()
        return {"added": added, "total_entries": len(self._entries)}

    def unregister(self, model_id: str, runtime_id: str,
                   hardware_id: str = HARDWARE_ALL) -> Dict[str, Any]:
        key = (model_id, runtime_id, hardware_id)
        existed = self._entries.pop(key, None) is not None
        if existed:
            self._persist()
        return {"removed": existed, "total_entries": len(self._entries)}

    # ── lookup ────────────────────────────────────────────────────

    def lookup(self, model_id: str, runtime_id: str,
               hardware_id: str = HARDWARE_ALL) -> Optional[Dict[str, Any]]:
        """Look up a combination; falls back from specific hardware to 'all'."""
        if hardware_id != HARDWARE_ALL:
            direct = self._entries.get((model_id, runtime_id, hardware_id))
            if direct:
                return direct.to_dict()
        generic = self._entries.get((model_id, runtime_id, HARDWARE_ALL))
        if generic:
            out = generic.to_dict()
            out["hardware_id"] = hardware_id
            out["inherited"] = True
            return out
        # generic hardware list matching (nvidia cpu -> all)
        candidates = [
            e.to_dict() for key, e in self._entries.items()
            if key[0] == model_id and key[1] == runtime_id
        ]
        if candidates:
            out = dict(candidates[0])
            out["hardware_id"] = hardware_id
            out["inherited"] = True
            return out
        return None

    def find_runtimes(self, model_id: str, hardware_id: Optional[str] = None,
                      min_score: float = 0.0) -> List[Dict[str, Any]]:
        """All compatible runtimes for a model, best-scoring first."""
        results = []
        for entry in self._entries.values():
            if entry.model_id != model_id or not entry.compatible:
                continue
            if entry.performance_score < min_score:
                continue
            if hardware_id and not self._hardware_compatible(entry.hardware_id, hardware_id):
                continue
            results.append(entry.to_dict())
        results.sort(key=lambda e: e["performance_score"], reverse=True)
        return results

    def find_models(self, category: Optional[str] = None,
                    hardware_id: Optional[str] = None,
                    min_score: float = 0.0) -> List[Dict[str, Any]]:
        """All models compatible with a runtime category/hardware, best first."""
        results = []
        for entry in self._entries.values():
            if not entry.compatible or entry.performance_score < min_score:
                continue
            if hardware_id and not self._hardware_compatible(entry.hardware_id, hardware_id):
                continue
            info = self._runtimes.get(entry.runtime_id)
            if category and info and info.category != category:
                continue
            results.append(entry.to_dict())
        results.sort(key=lambda e: e["performance_score"], reverse=True)
        return results

    @staticmethod
    def _hardware_compatible(entry_hw: str, requested_hw: str) -> bool:
        if entry_hw == HARDWARE_ALL or entry_hw == requested_hw:
            return True
        # CPU is a superset that also covers generic 'all' hardware
        if requested_hw == HARDWARE_ALL:
            return True
        if entry_hw == HARDWARE_CPU and requested_hw in (
                HARDWARE_NVIDIA, HARDWARE_APPLE, HARDWARE_METAL, HARDWARE_VULKAN):
            return False
        return False

    # ── validation (CGR-07) ───────────────────────────────────────

    def validate_path(self, model_id: str, runtime_id: str,
                      hardware_id: str = HARDWARE_ALL) -> Dict[str, Any]:
        """Validate a model/runtime/hardware combination (COMPATIBILITY_MATRIX.md)."""
        entry = self.lookup(model_id, runtime_id, hardware_id)
        if entry is None:
            return {"valid": False, "reason": "combination not registered",
                    "model_id": model_id, "runtime_id": runtime_id,
                    "hardware_id": hardware_id}
        if not entry["compatible"]:
            return {"valid": False, "reason": "marked incompatible",
                    "entry": entry}
        return {"valid": True, "reason": "compatible", "entry": entry}

    def validate_graph_path(self, graph, path: "ExecutionPath") -> Dict[str, Any]:
        """Combine graph-level path validation with matrix compatibility."""
        graph_result = graph.validate_path(path)
        if not graph_result["valid"]:
            return {"valid": False, "issues": graph_result["issues"],
                    "matrix": None}
        provider = path.nodes[0] if path.nodes else ""
        matrix = None
        if provider:
            info = self._runtimes.get(provider)
            if info:
                for hw in HARDWARE_FALLBACK:
                    check = self.lookup(provider, provider, hw) or self.lookup(
                        provider, provider, HARDWARE_ALL)
                    break
                matrix = {"runtime_id": provider, "catalogued": True}
        return {"valid": True, "issues": [], "matrix": matrix}

    # ── benchmark feedback ────────────────────────────────────────

    def update_score(self, model_id: str, runtime_id: str, hardware_id: str,
                     score: float) -> Dict[str, Any]:
        key = (model_id, runtime_id, hardware_id)
        if key not in self._entries:
            generic = self._entries.get((model_id, runtime_id, HARDWARE_ALL))
            if generic is None:
                return {"updated": False, "error": "entry not found"}
            key = generic.key()
        self._entries[key].performance_score = round(max(0.0, min(1.0, score)), 4)
        self._entries[key].verified_date = datetime.now(timezone.utc).date().isoformat()
        self._persist()
        return {"updated": True, "entry": self._entries[key].to_dict()}

    # ── refresh schedule (matrix maintenance) ─────────────────────

    def refresh_due(self, max_age_days: int = 90) -> List[Dict[str, Any]]:
        """Entries older than the refresh window (default 90 days)."""
        cutoff = (datetime.now(timezone.utc) - timedelta(days=max_age_days)).date()
        due = []
        for entry in self._entries.values():
            try:
                verified = datetime.fromisoformat(entry.verified_date).date()
            except (ValueError, TypeError):
                due.append(entry.to_dict())
                continue
            if verified < cutoff:
                due.append(entry.to_dict())
        return due

    # ── catalog / stats ───────────────────────────────────────────

    def list_runtimes(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        runtimes = self._runtimes.values()
        if category:
            runtimes = [r for r in runtimes if r.category == category]
        return [r.to_dict() for r in sorted(runtimes, key=lambda r: r.runtime_id)]

    def get_runtime(self, runtime_id: str) -> Optional[Dict[str, Any]]:
        info = self._runtimes.get(runtime_id)
        return info.to_dict() if info else None

    def get_stats(self) -> Dict[str, Any]:
        by_category: Dict[str, int] = {}
        by_evidence: Dict[str, int] = {}
        models = set()
        runtimes = set()
        for entry in self._entries.values():
            models.add(entry.model_id)
            runtimes.add(entry.runtime_id)
            info = self._runtimes.get(entry.runtime_id)
            category = info.category if info else "unknown"
            by_category[category] = by_category.get(category, 0) + 1
            by_evidence[entry.evidence] = by_evidence.get(entry.evidence, 0) + 1
        return {
            "total_entries": len(self._entries),
            "total_models": len(models),
            "total_runtimes": len(runtimes),
            "catalogued_runtimes": len(self._runtimes),
            "by_category": dict(sorted(by_category.items())),
            "by_evidence": dict(sorted(by_evidence.items())),
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entries": [e.to_dict() for e in self._entries.values()],
            "runtimes": [r.to_dict() for r in self._runtimes.values()],
            "stats": self.get_stats(),
        }
