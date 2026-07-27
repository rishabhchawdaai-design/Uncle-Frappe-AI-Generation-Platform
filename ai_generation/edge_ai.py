"""
Edge AI Runtime Detection — detect and profile edge AI hardware and runtimes.

Based on ACOS Research: Edge AI Research, Technology Atlas §10
Provides hardware detection, capability profiling, deployment template generation,
and negotiation engine integration as Tier 3 (edge) fallback.

Supported edge hardware:
- Apple Neural Engine (ANE) — M1/M2/M3/M4 series
- Qualcomm Hexagon NPU — Snapdragon 8 Gen 3/Elite
- Intel NPU — Meteor Lake/Arrow Lake
- NVIDIA Jetson — Orin Nano/NX/AGX
- Google Coral Edge TPU — USB/Dev Board
- Generic CPU-only fallback

Key Finding: Edge AI is viable for models < 7B parameters with INT8/INT4 quantization.
Apple Silicon provides the best edge inference due to unified memory.
"""
import logging
import platform
import subprocess
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class EdgeHardware(str, Enum):
    APPLE_ANE = "apple_ane"
    QUALCOMM_NPU = "qualcomm_npu"
    INTEL_NPU = "intel_npu"
    NVIDIA_JETSON = "nvidia_jetson"
    GOOGLE_CORAL = "google_coral"
    CPU_ONLY = "cpu_only"


class EdgeRuntime(str, Enum):
    COREML = "coreml"
    MLX = "mlx"
    LLAMA_CPP_METAL = "llama_cpp_metal"
    QNN = "qualcomm_qnn"
    OPENVINO = "openvino"
    TENSORRT = "tensorrt"
    LLAMA_CPP_CUDA = "llama_cpp_cuda"
    TFLITE = "tflite"
    ONNX_RUNTIME = "onnx_runtime"
    LLAMA_CPP_CPU = "llama_cpp_cpu"


class EdgeDetectionMethod(str, Enum):
    PLATFORM_SYSCTL = "platform_sysctl"
    GPU_QUERY = "gpu_query"
    LSPCI = "lspci"
    PROC_CPUINFO = "proc_cpuinfo"
    NPYTOP = "npytop"
    FALLBACK = "fallback"


@dataclass
class EdgeHardwareProfile:
    """Profile for an edge AI hardware platform."""
    hardware: EdgeHardware = EdgeHardware.CPU_ONLY
    name: str = ""
    compute_tops: float = 0.0
    memory_gb: float = 0.0
    power_watts: float = 0.0
    supported_runtimes: List[EdgeRuntime] = field(default_factory=list)
    supported_precisions: List[str] = field(default_factory=list)
    max_model_params_b: float = 0.0
    supports_llm: bool = False
    supports_diffusion: bool = False
    supports_classification: bool = False
    platform: str = ""  # macos, linux, android, windows
    maturity: str = "production"  # production, emerging, experimental
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)
    detection_method: EdgeDetectionMethod = EdgeDetectionMethod.FALLBACK

    def to_dict(self) -> Dict[str, Any]:
        return {
            "hardware": self.hardware.value,
            "name": self.name,
            "compute_tops": self.compute_tops,
            "memory_gb": self.memory_gb,
            "power_watts": self.power_watts,
            "supported_runtimes": [r.value for r in self.supported_runtimes],
            "supported_precisions": self.supported_precisions,
            "max_model_params_b": self.max_model_params_b,
            "supports_llm": self.supports_llm,
            "supports_diffusion": self.supports_diffusion,
            "supports_classification": self.supports_classification,
            "platform": self.platform,
            "maturity": self.maturity,
            "strengths": self.strengths,
            "weaknesses": self.weaknesses,
            "detection_method": self.detection_method.value,
        }


# ── Built-in Edge Hardware Profiles ──────────────────────────

APPLE_ANE_M4_PROFILE = EdgeHardwareProfile(
    hardware=EdgeHardware.APPLE_ANE,
    name="Apple Neural Engine (M4 Max)",
    compute_tops=38.0,
    memory_gb=128.0,
    power_watts=60.0,
    supported_runtimes=[EdgeRuntime.COREML, EdgeRuntime.MLX, EdgeRuntime.LLAMA_CPP_METAL],
    supported_precisions=["fp16", "int8", "int4"],
    max_model_params_b=7.0,
    supports_llm=True,
    supports_diffusion=True,
    supports_classification=True,
    platform="macos",
    maturity="production",
    strengths=["Unified memory", "Excellent MLX support", "Low power"],
    weaknesses=["Apple-only", "Proprietary", "Limited to Apple ecosystem"],
)

APPLE_ANE_M2_PROFILE = EdgeHardwareProfile(
    hardware=EdgeHardware.APPLE_ANE,
    name="Apple Neural Engine (M2 Max)",
    compute_tops=31.0,
    memory_gb=96.0,
    power_watts=50.0,
    supported_runtimes=[EdgeRuntime.COREML, EdgeRuntime.MLX, EdgeRuntime.LLAMA_CPP_METAL],
    supported_precisions=["fp16", "int8", "int4"],
    max_model_params_b=7.0,
    supports_llm=True,
    supports_diffusion=True,
    supports_classification=True,
    platform="macos",
    maturity="production",
    strengths=["Unified memory", "Excellent MLX support"],
    weaknesses=["Apple-only", "Proprietary"],
)

QUALCOMM_8_ELITE_PROFILE = EdgeHardwareProfile(
    hardware=EdgeHardware.QUALCOMM_NPU,
    name="Qualcomm Snapdragon 8 Elite NPU",
    compute_tops=75.0,
    memory_gb=16.0,
    power_watts=10.0,
    supported_runtimes=[EdgeRuntime.QNN, EdgeRuntime.ONNX_RUNTIME],
    supported_precisions=["fp16", "int8", "int4"],
    max_model_params_b=7.0,
    supports_llm=True,
    supports_diffusion=False,
    supports_classification=True,
    platform="android",
    maturity="production",
    strengths=["Best Android NPU", "Wide device availability"],
    weaknesses=["Qualcomm-only", "Android fragmentation"],
)

INTEL_NPU_PROFILE = EdgeHardwareProfile(
    hardware=EdgeHardware.INTEL_NPU,
    name="Intel Core Ultra NPU (Meteor Lake)",
    compute_tops=11.0,
    memory_gb=32.0,
    power_watts=10.0,
    supported_runtimes=[EdgeRuntime.OPENVINO, EdgeRuntime.ONNX_RUNTIME],
    supported_precisions=["fp16", "int8"],
    max_model_params_b=1.0,
    supports_llm=False,
    supports_diffusion=False,
    supports_classification=True,
    platform="windows",
    maturity="emerging",
    strengths=["x86 compatibility", "OpenVINO ecosystem"],
    weaknesses=["Low TOPS", "Limited LLM support"],
)

JETSON_AGX_PROFILE = EdgeHardwareProfile(
    hardware=EdgeHardware.NVIDIA_JETSON,
    name="NVIDIA Jetson AGX Orin 64GB",
    compute_tops=275.0,
    memory_gb=64.0,
    power_watts=60.0,
    supported_runtimes=[EdgeRuntime.TENSORRT, EdgeRuntime.LLAMA_CPP_CUDA, EdgeRuntime.ONNX_RUNTIME],
    supported_precisions=["fp32", "fp16", "int8", "int4"],
    max_model_params_b=7.0,
    supports_llm=True,
    supports_diffusion=True,
    supports_classification=True,
    platform="linux",
    maturity="production",
    strengths=["Best edge GPU", "CUDA/TensorRT ecosystem"],
    weaknesses=["Higher power", "NVIDIA-only", "Expensive"],
)

JETSON_NANO_PROFILE = EdgeHardwareProfile(
    hardware=EdgeHardware.NVIDIA_JETSON,
    name="NVIDIA Jetson Orin Nano 8GB",
    compute_tops=40.0,
    memory_gb=8.0,
    power_watts=15.0,
    supported_runtimes=[EdgeRuntime.TENSORRT, EdgeRuntime.LLAMA_CPP_CUDA, EdgeRuntime.ONNX_RUNTIME],
    supported_precisions=["fp16", "int8", "int4"],
    max_model_params_b=3.0,
    supports_llm=True,
    supports_diffusion=False,
    supports_classification=True,
    platform="linux",
    maturity="production",
    strengths=["Low power", "CUDA ecosystem"],
    weaknesses=["Limited memory", "NVIDIA-only"],
)

CORAL_USB_PROFILE = EdgeHardwareProfile(
    hardware=EdgeHardware.GOOGLE_CORAL,
    name="Google Coral Edge TPU (USB)",
    compute_tops=4.0,
    memory_gb=1.0,
    power_watts=2.0,
    supported_runtimes=[EdgeRuntime.TFLITE],
    supported_precisions=["int8"],
    max_model_params_b=0.01,
    supports_llm=False,
    supports_diffusion=False,
    supports_classification=True,
    platform="linux",
    maturity="production",
    strengths=["Very low power", "USB form factor"],
    weaknesses=["INT8 only", "4 TOPS", "Classification only"],
)

CPU_ONLY_PROFILE = EdgeHardwareProfile(
    hardware=EdgeHardware.CPU_ONLY,
    name="CPU-only Fallback",
    compute_tops=0.0,
    memory_gb=8.0,
    power_watts=65.0,
    supported_runtimes=[EdgeRuntime.LLAMA_CPP_CPU, EdgeRuntime.ONNX_RUNTIME],
    supported_precisions=["fp32", "fp16", "int8", "int4"],
    max_model_params_b=3.0,
    supports_llm=True,
    supports_diffusion=False,
    supports_classification=True,
    platform="any",
    maturity="production",
    strengths=["Universal availability", "No special hardware"],
    weaknesses=["Slow inference", "High power per TOPS"],
)

BUILTIN_EDGE_PROFILES = [
    APPLE_ANE_M4_PROFILE,
    APPLE_ANE_M2_PROFILE,
    QUALCOMM_8_ELITE_PROFILE,
    INTEL_NPU_PROFILE,
    JETSON_AGX_PROFILE,
    JETSON_NANO_PROFILE,
    CORAL_USB_PROFILE,
    CPU_ONLY_PROFILE,
]


# ── Hardware Detection ────────────────────────────────────────

def _detect_apple_silicon() -> Optional[Dict[str, Any]]:
    """Detect Apple Silicon hardware."""
    if platform.system() != "Darwin":
        return None
    try:
        result = subprocess.run(
            ["sysctl", "-n", "machdep.cpu.brand_string"],
            capture_output=True, text=True, timeout=5
        )
        brand = result.stdout.strip()
        if "Apple" in brand:
            mem_result = subprocess.run(
                ["sysctl", "-n", "hw.memsize"],
                capture_output=True, text=True, timeout=5
            )
            mem_bytes = int(mem_result.stdout.strip()) if mem_result.returncode == 0 else 0
            return {
                "detected": True,
                "hardware": "apple_ane",
                "chip": brand,
                "memory_gb": round(mem_bytes / (1024**3), 1),
                "platform": "macos",
            }
    except Exception:
        pass
    return None


def _detect_nvidia_gpu() -> Optional[Dict[str, Any]]:
    """Detect NVIDIA GPU (including Jetson)."""
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total,driver_version",
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0 and result.stdout.strip():
            parts = result.stdout.strip().split(", ")
            if len(parts) >= 2:
                name = parts[0].strip()
                memory_mb = float(parts[1].strip()) if parts[1].strip().replace(".", "").isdigit() else 0
                is_jetson = "Orin" in name or "Jetson" in name or "Xavier" in name
                return {
                    "detected": True,
                    "hardware": "nvidia_jetson" if is_jetson else "nvidia_gpu",
                    "name": name,
                    "memory_gb": round(memory_mb / 1024, 1),
                    "is_jetson": is_jetson,
                    "platform": "linux",
                }
    except Exception:
        pass
    return None


def _detect_intel_npu() -> Optional[Dict[str, Any]]:
    """Detect Intel NPU (Meteor Lake+)."""
    try:
        result = subprocess.run(
            ["lscpu"], capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            output = result.stdout
            if "Intel" in output and ("Core Ultra" in output or "Meteor Lake" in output):
                return {
                    "detected": True,
                    "hardware": "intel_npu",
                    "platform": "linux",
                }
    except Exception:
        pass
    return None


def detect_edge_hardware() -> Dict[str, Any]:
    """Detect available edge AI hardware on this system."""
    detections = []

    apple = _detect_apple_silicon()
    if apple:
        detections.append(apple)

    nvidia = _detect_nvidia_gpu()
    if nvidia:
        detections.append(nvidia)

    intel = _detect_intel_npu()
    if intel:
        detections.append(intel)

    if not detections:
        detections.append({
            "detected": False,
            "hardware": "cpu_only",
            "platform": platform.system().lower(),
        })

    return {
        "detections": detections,
        "platform": platform.system().lower(),
        "architecture": platform.machine(),
        "python_version": platform.python_version(),
    }


# ── Edge AI Manager ──────────────────────────────────────────

class EdgeAIManager:
    """
    Manages edge AI hardware detection, capability profiling,
    and deployment template generation.

    Integrates with negotiation engine as Tier 3 (edge) fallback.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._profiles: Dict[str, EdgeHardwareProfile] = {}
        self._detected: Optional[Dict[str, Any]] = None
        self._init_builtin_profiles()

    def _init_builtin_profiles(self):
        """Register built-in edge hardware profiles."""
        for profile in BUILTIN_EDGE_PROFILES:
            key = f"{profile.hardware.value}_{profile.name}"
            self._profiles[key] = profile

    def detect_hardware(self) -> Dict[str, Any]:
        """Detect edge hardware on this system."""
        if self._detected is None:
            self._detected = detect_edge_hardware()
        return self._detected

    def list_profiles(self, hardware: Optional[str] = None,
                      platform_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """List edge hardware profiles with optional filtering."""
        profiles = list(self._profiles.values())
        if hardware:
            profiles = [p for p in profiles if p.hardware.value == hardware]
        if platform_filter:
            profiles = [p for p in profiles if p.platform == platform_filter or p.platform == "any"]
        return [p.to_dict() for p in profiles]

    def get_profile(self, hardware: str, name: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get a specific edge hardware profile."""
        for key, profile in self._profiles.items():
            if profile.hardware.value == hardware:
                if name is None or name in profile.name:
                    return profile.to_dict()
        return None

    def find_optimal_profile(self, task_type: str,
                              max_power_watts: float = 100.0,
                              min_memory_gb: float = 0.0,
                              platform_filter: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Find the best edge profile for a task within constraints."""
        candidates = []
        for profile in self._profiles.values():
            score = 0

            # Task fit
            if task_type == "text_generation" and profile.supports_llm:
                score += 10
            elif task_type == "image_classification" and profile.supports_classification:
                score += 10
            elif task_type == "image_generation" and profile.supports_diffusion:
                score += 10
            else:
                continue

            # Power constraint
            if profile.power_watts > max_power_watts:
                continue

            # Memory constraint
            if profile.memory_gb < min_memory_gb:
                continue

            # Platform constraint
            if platform_filter and profile.platform != platform_filter and profile.platform != "any":
                continue

            # Prefer higher TOPS
            score += min(profile.compute_tops / 10, 10)

            # Prefer production maturity
            if profile.maturity == "production":
                score += 5

            candidates.append((profile, score))

        if not candidates:
            return None
        candidates.sort(key=lambda x: -x[1])
        return candidates[0][0].to_dict()

    def generate_deployment_template(self, hardware: str,
                                      task_type: str) -> Dict[str, Any]:
        """Generate a deployment template for edge AI."""
        profile = None
        for p in self._profiles.values():
            if p.hardware.value == hardware:
                profile = p
                break

        if not profile:
            return {"error": f"Unknown hardware: {hardware}"}

        if hardware == "apple_ane":
            return self._gen_apple_template(profile, task_type)
        elif hardware == "nvidia_jetson":
            return self._gen_jetson_template(profile, task_type)
        elif hardware == "qualcomm_npu":
            return self._gen_qualcomm_template(profile, task_type)
        elif hardware == "intel_npu":
            return self._gen_intel_template(profile, task_type)
        elif hardware == "google_coral":
            return self._gen_coral_template(profile, task_type)
        else:
            return self._gen_cpu_template(profile, task_type)

    def _gen_apple_template(self, profile: EdgeHardwareProfile,
                             task_type: str) -> Dict[str, Any]:
        if task_type == "text_generation":
            return {
                "hardware": "apple_ane",
                "task_type": task_type,
                "runtime": "llama_cpp_metal",
                "script": f"""# Apple Silicon LLM Inference via llama.cpp + Metal
# Requires: brew install llama.cpp
# Profile: {profile.name} ({profile.compute_tops} TOPS, {profile.memory_gb}GB)

import subprocess
import json

def run_inference(prompt: str, model_path: str = "models/llama-3-8b-q4.gguf",
                  n_gpu_layers: int = 99, max_tokens: int = 512) -> str:
    cmd = [
        "llama-cli",
        "-m", model_path,
        "-p", prompt,
        "-n", str(max_tokens),
        "--n-gpu-layers", str(n_gpu_layers),
        "-t", "8",
        "--ctx-size", "4096",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout.strip()

if __name__ == "__main__":
    output = run_inference("Explain quantum computing in simple terms.")
    print(output)
""",
            }
        elif task_type == "image_generation":
            return {
                "hardware": "apple_ane",
                "task_type": task_type,
                "runtime": "mlx",
                "script": f"""# Apple Silicon Diffusion via MLX
# Profile: {profile.name} ({profile.memory_gb}GB unified memory)

# pip install mlx-stable-diffusion
from mlx_lm import load, generate

model, tokenizer = load("mlx-community/stable-diffusion-xl-base-1.0-4bit")
# Use MLX-optimized SDXL pipeline for image generation
""",
            }
        else:
            return {"hardware": "apple_ane", "task_type": task_type, "runtime": "coreml", "script": "# CoreML template"}

    def _gen_jetson_template(self, profile: EdgeHardwareProfile,
                              task_type: str) -> Dict[str, Any]:
        return {
            "hardware": "nvidia_jetson",
            "task_type": task_type,
            "runtime": "tensorrt",
            "script": f"""# NVIDIA Jetson LLM Inference via TensorRT-LLM
# Profile: {profile.name} ({profile.compute_tops} TOPS)
# Requires: JetPack SDK with TensorRT-LLM

# sudo apt install tensorrt-llm
# Use trtllm-run for inference:
# trtllm-run --model_dir models/llama-3-8b-trt/ --prompt "Hello"
""",
        }

    def _gen_qualcomm_template(self, profile: EdgeHardwareProfile,
                                 task_type: str) -> Dict[str, Any]:
        return {
            "hardware": "qualcomm_npu",
            "task_type": task_type,
            "runtime": "qualcomm_qnn",
            "script": f"""# Qualcomm NPU Inference via QNN
# Profile: {profile.name} ({profile.compute_tops} TOPS)
# Requires: Qualcomm AI Engine Direct SDK

# Use QNN context binary for inference
# Supports INT8/INT4 quantized models
""",
        }

    def _gen_intel_template(self, profile: EdgeHardwareProfile,
                             task_type: str) -> Dict[str, Any]:
        return {
            "hardware": "intel_npu",
            "task_type": task_type,
            "runtime": "openvino",
            "script": f"""# Intel NPU Inference via OpenVINO
# Profile: {profile.name} ({profile.compute_tops} TOPS)
# Requires: OpenVINO toolkit

# pip install openvino
from openvino.runtime import Core
core = Core()
model = core.read_model("model.xml")
compiled = core.compile_model(model, "NPU")
""",
        }

    def _gen_coral_template(self, profile: EdgeHardwareProfile,
                             task_type: str) -> Dict[str, Any]:
        return {
            "hardware": "google_coral",
            "task_type": task_type,
            "runtime": "tflite",
            "script": f"""# Google Coral Edge TPU Inference via TFLite
# Profile: {profile.name} ({profile.compute_tops} TOPS)
# Requires: pycoral + libedgetpu

# pip install pycoral
from pycoral.utils.edgetpu import run_inference
result = run_inference("model.tflite_edgetpu", input_data)
""",
        }

    def _gen_cpu_template(self, profile: EdgeHardwareProfile,
                           task_type: str) -> Dict[str, Any]:
        return {
            "hardware": "cpu_only",
            "task_type": task_type,
            "runtime": "llama_cpp_cpu",
            "script": f"""# CPU-only Inference via llama.cpp
# Profile: {profile.name}
# Requires: llama.cpp compiled for CPU

# llama-cli -m model.gguf -p "prompt" -n 256 -t 8
""",
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get edge AI statistics."""
        detected = self.detect_hardware()
        hardware_types = {}
        for p in self._profiles.values():
            hw = p.hardware.value
            hardware_types[hw] = hardware_types.get(hw, 0) + 1

        return {
            "profile_count": len(self._profiles),
            "hardware_types": hardware_types,
            "detected_hardware": detected["detections"],
            "platform": detected["platform"],
            "architecture": detected["architecture"],
            "tier": 3,
            "tier_description": "Edge AI — Tier 3 fallback for on-device inference",
        }

    def to_negotiation_candidates(self, task_type: str) -> List[Dict[str, Any]]:
        """Generate negotiation engine candidates for edge AI fallback."""
        detected = self.detect_hardware()
        candidates = []

        for detection in detected["detections"]:
            hw = detection.get("hardware", "cpu_only")
            for profile in self._profiles.values():
                if profile.hardware.value == hw:
                    fits_task = (
                        (task_type == "text_generation" and profile.supports_llm) or
                        (task_type == "image_classification" and profile.supports_classification) or
                        (task_type == "image_generation" and profile.supports_diffusion)
                    )
                    if fits_task:
                        candidates.append({
                            "provider": f"edge_{profile.hardware.value}",
                            "model": f"auto_{task_type}",
                            "layer": "edge",
                            "tier": 3,
                            "cost_usd": 0.0,
                            "latency_estimate_ms": 1000 if profile.compute_tops > 10 else 5000,
                            "quality_estimate": 0.7,
                            "requires_network": False,
                            "metadata": {
                                "hardware": profile.hardware.value,
                                "compute_tops": profile.compute_tops,
                                "memory_gb": profile.memory_gb,
                                "power_watts": profile.power_watts,
                            },
                        })
        return candidates
