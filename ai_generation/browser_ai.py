"""
Browser AI Inference Layer — browser-based AI inference via Transformers.js, WebLLM, ONNX Runtime Web.

Based on ACOS Research: Browser AI Research, Technology Atlas §9
Provides Python-side interface for registering, configuring, and generating
browser-based inference code. Browser AI serves as Tier 4 fallback in the
execution hierarchy for edge deployments and privacy-sensitive use cases.

Capabilities:
- Register browser runtimes (Transformers.js, WebLLM, ONNX Web, TF.js)
- Generate browser inference HTML/JS templates
- Detect browser capabilities and suggest optimal runtime
- Integrate with negotiation engine as fallback tier
- Model size and memory limit enforcement

Limitations:
- Cannot run models > 7B parameters
- WASM heap ~2GB, WebGPU buffer ~4GB
- No distributed execution participation
"""
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class BrowserRuntime(str, Enum):
    TRANSFORMERS_JS = "transformers_js"
    WEBLLM = "webllm"
    ONNX_WEB = "onnx_web"
    TFJS = "tensorflow_js"
    WEBNN = "webnn"


class BrowserBackend(str, Enum):
    WASM = "wasm"
    WEBGPU = "webgpu"
    WEBGL = "webgl"


@dataclass
class BrowserModelProfile:
    """Profile for a model that can run in the browser."""
    model_id: str = ""
    name: str = ""
    runtime: BrowserRuntime = BrowserRuntime.TRANSFORMERS_JS
    backend: BrowserBackend = BrowserBackend.WASM
    model_format: str = "onnx"
    precision: str = "fp32"
    parameter_count_b: float = 0.0
    memory_mb: float = 0.0
    category: str = ""  # llm, diffusion, classification, embedding
    supports_streaming: bool = False
    supports_offline: bool = False
    min_browser_versions: Dict[str, str] = field(default_factory=dict)
    performance_estimate: Dict[str, Any] = field(default_factory=dict)
    license: str = ""
    source_url: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "model_id": self.model_id,
            "name": self.name,
            "runtime": self.runtime.value,
            "backend": self.backend.value,
            "model_format": self.model_format,
            "precision": self.precision,
            "parameter_count_b": self.parameter_count_b,
            "memory_mb": self.memory_mb,
            "category": self.category,
            "supports_streaming": self.supports_streaming,
            "supports_offline": self.supports_offline,
            "min_browser_versions": self.min_browser_versions,
            "performance_estimate": self.performance_estimate,
            "license": self.license,
            "source_url": self.source_url,
        }


@dataclass
class BrowserCapabilityProfile:
    """Profile for a browser runtime's capabilities."""
    runtime: BrowserRuntime = BrowserRuntime.TRANSFORMERS_JS
    version: str = ""
    license: str = ""
    supported_formats: List[str] = field(default_factory=list)
    supported_precisions: List[str] = field(default_factory=list)
    supports_text_generation: bool = False
    supports_image_generation: bool = False
    supports_image_classification: bool = False
    supports_text_classification: bool = False
    supports_embeddings: bool = False
    supports_speech_recognition: bool = False
    supports_text_to_speech: bool = False
    max_model_size_gb: float = 4.0
    requires_webgpu: bool = False
    mobile_support: bool = False
    offline_support: bool = False
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "runtime": self.runtime.value,
            "version": self.version,
            "license": self.license,
            "supported_formats": self.supported_formats,
            "supported_precisions": self.supported_precisions,
            "capabilities": {
                "text_generation": self.supports_text_generation,
                "image_generation": self.supports_image_generation,
                "image_classification": self.supports_image_classification,
                "text_classification": self.supports_text_classification,
                "embeddings": self.supports_embeddings,
                "speech_recognition": self.supports_speech_recognition,
                "text_to_speech": self.supports_text_to_speech,
            },
            "max_model_size_gb": self.max_model_size_gb,
            "requires_webgpu": self.requires_webgpu,
            "mobile_support": self.mobile_support,
            "offline_support": self.offline_support,
            "strengths": self.strengths,
            "weaknesses": self.weaknesses,
        }


# ── Built-in Browser Runtime Profiles ─────────────────────────

TRANSFORMERS_JS_PROFILE = BrowserCapabilityProfile(
    runtime=BrowserRuntime.TRANSFORMERS_JS,
    version="3.x",
    license="Apache-2.0",
    supported_formats=["onnx", "gguf"],
    supported_precisions=["fp32", "fp16", "int8", "int4"],
    supports_text_generation=True,
    supports_image_generation=True,
    supports_image_classification=True,
    supports_text_classification=True,
    supports_embeddings=True,
    supports_speech_recognition=True,
    supports_text_to_speech=True,
    max_model_size_gb=4.0,
    requires_webgpu=False,
    mobile_support=True,
    offline_support=True,
    strengths=["Largest model catalog", "HuggingFace integration", "Multi-modal"],
    weaknesses=["Limited to ONNX-convertible models", "WebGPU not universal"],
)

WEBLLM_PROFILE = BrowserCapabilityProfile(
    runtime=BrowserRuntime.WEBLLM,
    version="0.2.x",
    license="Apache-2.0",
    supported_formats=["tvm"],
    supported_precisions=["fp16", "int4", "int3", "int2"],
    supports_text_generation=True,
    supports_image_generation=False,
    supports_image_classification=False,
    supports_text_classification=False,
    supports_embeddings=False,
    supports_speech_recognition=False,
    supports_text_to_speech=False,
    max_model_size_gb=4.0,
    requires_webgpu=True,
    mobile_support=True,
    offline_support=True,
    strengths=["Best LLM performance in browser", "TVM optimization"],
    weaknesses=["Requires WebGPU", "Limited to LLMs only"],
)

ONNX_WEB_PROFILE = BrowserCapabilityProfile(
    runtime=BrowserRuntime.ONNX_WEB,
    version="1.17.x",
    license="MIT",
    supported_formats=["onnx"],
    supported_precisions=["fp32", "fp16", "int8", "int4"],
    supports_text_generation=True,
    supports_image_generation=True,
    supports_image_classification=True,
    supports_text_classification=True,
    supports_embeddings=True,
    supports_speech_recognition=True,
    supports_text_to_speech=True,
    max_model_size_gb=4.0,
    requires_webgpu=False,
    mobile_support=True,
    offline_support=True,
    strengths=["Broadest model support", "Microsoft backing"],
    weaknesses=["Requires ONNX conversion"],
)

TFJS_PROFILE = BrowserCapabilityProfile(
    runtime=BrowserRuntime.TFJS,
    version="4.x",
    license="Apache-2.0",
    supported_formats=["tfjs", "tflite"],
    supported_precisions=["fp32", "fp16"],
    supports_text_generation=False,
    supports_image_generation=True,
    supports_image_classification=True,
    supports_text_classification=True,
    supports_embeddings=True,
    supports_speech_recognition=True,
    supports_text_to_speech=True,
    max_model_size_gb=2.0,
    requires_webgpu=False,
    mobile_support=True,
    offline_support=True,
    strengths=["Broadest browser support", "Excellent mobile"],
    weaknesses=["Limited LLM support", "Declining activity"],
)


# ── Built-in Model Profiles ────────────────────────────────────

BROWSER_MODEL_PROFILES = [
    BrowserModelProfile(
        model_id="Xenova/gpt2",
        name="GPT-2 (124M)",
        runtime=BrowserRuntime.TRANSFORMERS_JS,
        backend=BrowserBackend.WASM,
        model_format="onnx",
        precision="fp32",
        parameter_count_b=0.124,
        memory_mb=500,
        category="llm",
        supports_streaming=True,
        supports_offline=True,
        license="MIT",
    ),
    BrowserModelProfile(
        model_id="Xenova/distilbert-base-uncased-finetuned-sst-2-english",
        name="DistilBERT Sentiment",
        runtime=BrowserRuntime.TRANSFORMERS_JS,
        backend=BrowserBackend.WASM,
        model_format="onnx",
        precision="fp32",
        parameter_count_b=0.066,
        memory_mb=250,
        category="text_classification",
        supports_streaming=False,
        supports_offline=True,
        license="Apache-2.0",
    ),
    BrowserModelProfile(
        model_id="Xenova/resnet-50",
        name="ResNet-50 Image Classification",
        runtime=BrowserRuntime.TRANSFORMERS_JS,
        backend=BrowserBackend.WASM,
        model_format="onnx",
        precision="fp32",
        parameter_count_b=0.025,
        memory_mb=100,
        category="image_classification",
        supports_streaming=False,
        supports_offline=True,
        license="Apache-2.0",
    ),
    BrowserModelProfile(
        model_id="Xenova/all-MiniLM-L6-v2",
        name="MiniLM Embeddings",
        runtime=BrowserRuntime.TRANSFORMERS_JS,
        backend=BrowserBackend.WASM,
        model_format="onnx",
        precision="fp32",
        parameter_count_b=0.022,
        memory_mb=80,
        category="embedding",
        supports_streaming=False,
        supports_offline=True,
        license="Apache-2.0",
    ),
    BrowserModelProfile(
        model_id="Llama-3.2-1B-Instruct-q4f32_1-MLC",
        name="Llama 3.2 1B (WebLLM)",
        runtime=BrowserRuntime.WEBLLM,
        backend=BrowserBackend.WEBGPU,
        model_format="tvm",
        precision="int4",
        parameter_count_b=1.0,
        memory_mb=2000,
        category="llm",
        supports_streaming=True,
        supports_offline=True,
        license="Apache-2.0",
    ),
    BrowserModelProfile(
        model_id="Phi-3.5-mini-instruct-q4f16_1-MLC",
        name="Phi 3.5 Mini (WebLLM)",
        runtime=BrowserRuntime.WEBLLM,
        backend=BrowserBackend.WEBGPU,
        model_format="tvm",
        precision="int4",
        parameter_count_b=3.8,
        memory_mb=3500,
        category="llm",
        supports_streaming=True,
        supports_offline=True,
        license="MIT",
    ),
]


# ── Browser AI Inference Manager ──────────────────────────────

class BrowserAIManager:
    """
    Manages browser-based AI inference capabilities.

    Registers browser runtimes, maintains model profiles,
    generates browser inference code templates, and integrates
    with the negotiation engine as Tier 4 fallback.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._runtimes: Dict[str, BrowserCapabilityProfile] = {}
        self._models: List[BrowserModelProfile] = []
        self._init_builtin_runtimes()
        self._init_builtin_models()

    def _init_builtin_runtimes(self):
        """Register built-in browser runtime profiles."""
        for profile in [
            TRANSFORMERS_JS_PROFILE,
            WEBLLM_PROFILE,
            ONNX_WEB_PROFILE,
            TFJS_PROFILE,
        ]:
            self._runtimes[profile.runtime.value] = profile

    def _init_builtin_models(self):
        """Register built-in browser model profiles."""
        self._models.extend(BROWSER_MODEL_PROFILES)

    def list_runtimes(self) -> List[Dict[str, Any]]:
        """List all registered browser runtimes."""
        return [p.to_dict() for p in self._runtimes.values()]

    def get_runtime(self, runtime: str) -> Optional[Dict[str, Any]]:
        """Get a specific browser runtime profile."""
        profile = self._runtimes.get(runtime)
        return profile.to_dict() if profile else None

    def list_models(self, category: Optional[str] = None,
                    runtime: Optional[str] = None) -> List[Dict[str, Any]]:
        """List browser-compatible models with optional filtering."""
        models = self._models
        if category:
            models = [m for m in models if m.category == category]
        if runtime:
            models = [m for m in models if m.runtime.value == runtime]
        return [m.to_dict() for m in models]

    def find_models_for_task(self, task_type: str,
                             max_memory_mb: float = 4000) -> List[Dict[str, Any]]:
        """Find browser models suitable for a task type within memory limits."""
        category_map = {
            "text_generation": "llm",
            "text_classification": "text_classification",
            "image_classification": "image_classification",
            "embedding": "embedding",
        }
        target_category = category_map.get(task_type, task_type)
        return [
            m.to_dict() for m in self._models
            if m.category == target_category and m.memory_mb <= max_memory_mb
        ]

    def select_optimal_runtime(self, task_type: str,
                                needs_offline: bool = False,
                                needs_mobile: bool = False) -> Optional[str]:
        """Select the best browser runtime for a given task."""
        candidates = []
        for name, profile in self._runtimes.items():
            score = 0
            if task_type == "text_generation" and profile.supports_text_generation:
                score += 10
            elif task_type == "image_generation" and profile.supports_image_generation:
                score += 10
            elif task_type == "embedding" and profile.supports_embeddings:
                score += 10
            elif task_type == "text_classification" and profile.supports_text_classification:
                score += 10
            elif task_type == "image_classification" and profile.supports_image_classification:
                score += 10

            if score == 0:
                continue

            if not needs_offline or profile.offline_support:
                score += 2
            if not needs_mobile or profile.mobile_support:
                score += 1
            if not profile.requires_webgpu:
                score += 3  # Prefer WASM (broader support)

            candidates.append((name, score))

        if not candidates:
            return None
        candidates.sort(key=lambda x: -x[1])
        return candidates[0][0]

    def generate_inference_template(self, runtime: str, task_type: str,
                                     model_id: Optional[str] = None) -> Dict[str, Any]:
        """Generate a browser inference HTML/JS template."""
        profile = self._runtimes.get(runtime)
        if not profile:
            return {"error": f"Unknown runtime: {runtime}"}

        if runtime == "transformers_js":
            return self._gen_transformers_js_template(task_type, model_id)
        elif runtime == "webllm":
            return self._gen_webllm_template(task_type, model_id)
        elif runtime == "onnx_web":
            return self._gen_onnx_web_template(task_type, model_id)
        elif runtime == "tensorflow_js":
            return self._gen_tfjs_template(task_type, model_id)
        else:
            return {"error": f"No template generator for runtime: {runtime}"}

    def _gen_transformers_js_template(self, task_type: str,
                                       model_id: Optional[str] = None) -> Dict[str, Any]:
        """Generate Transformers.js inference template."""
        model = model_id or "Xenova/gpt2"
        if task_type == "text_generation":
            js_code = f"""
import {{ pipeline }} from 'https://cdn.jsdelivr.net/npm/@huggingface/transformers@3';

const generator = await pipeline('text-generation', '{model}');
const output = await generator('Hello, ', {{ max_new_tokens: 50 }});
console.log(output[0].generated_text);
"""
        elif task_type == "text_classification":
            actual_model = model_id or "Xenova/distilbert-base-uncased-finetuned-sst-2-english"
            js_code = f"""
import {{ pipeline }} from 'https://cdn.jsdelivr.net/npm/@huggingface/transformers@3';

const classifier = await pipeline('text-classification', '{actual_model}');
const output = await classifier('I love this product!');
console.log(output);
"""
        elif task_type == "image_classification":
            actual_model = model_id or "Xenova/resnet-50"
            js_code = f"""
import {{ pipeline }} from 'https://cdn.jsdelivr.net/npm/@huggingface/transformers@3';

const classifier = await pipeline('image-classification', '{actual_model}');
const output = await classifier('https://example.com/image.jpg');
console.log(output);
"""
        elif task_type == "embedding":
            actual_model = model_id or "Xenova/all-MiniLM-L6-v2"
            js_code = f"""
import {{ pipeline }} from 'https://cdn.jsdelivr.net/npm/@huggingface/transformers@3';

const extractor = await pipeline('feature-extraction', '{actual_model}');
const output = await extractor('This is a test sentence.');
console.log(output);
"""
        else:
            return {"error": f"Unsupported task type: {task_type}"}

        return {
            "runtime": "transformers_js",
            "task_type": task_type,
            "model": model,
            "html": f"""<!DOCTYPE html>
<html>
<head><title>Transformers.js Inference</title></head>
<body>
<h1>Browser AI: {task_type}</h1>
<pre id="output">Loading model...</pre>
<script type="module">
{js_code}
document.getElementById('output').textContent = JSON.stringify(output, null, 2);
</script>
</body>
</html>""",
            "javascript": js_code.strip(),
        }

    def _gen_webllm_template(self, task_type: str,
                              model_id: Optional[str] = None) -> Dict[str, Any]:
        """Generate WebLLM inference template."""
        model = model_id or "Llama-3.2-1B-Instruct-q4f32_1-MLC"
        js_code = f"""
import {{ ChatModule }} from 'https://cdn.jsdelivr.net/npm/@mlc-ai/web-llm@0.2';

const llm = new ChatModule();
await llm.reload('{model}');
const output = await llm.generate({{
  messages: [{{ role: 'user', content: 'Hello, how are you?' }}],
  temperature: 0.7,
  max_gen_len: 256,
}});
console.log(output);
"""
        return {
            "runtime": "webllm",
            "task_type": task_type,
            "model": model,
            "html": f"""<!DOCTYPE html>
<html>
<head><title>WebLLM Inference</title></head>
<body>
<h1>Browser LLM: WebLLM</h1>
<pre id="output">Loading model (requires WebGPU)...</pre>
<script type="module">
{js_code}
document.getElementById('output').textContent = output;
</script>
</body>
</html>""",
            "javascript": js_code.strip(),
        }

    def _gen_onnx_web_template(self, task_type: str,
                                model_id: Optional[str] = None) -> Dict[str, Any]:
        """Generate ONNX Runtime Web inference template."""
        js_code = f"""
import * as ort from 'https://cdn.jsdelivr.net/npm/onnxruntime-web@1.17';

const session = await ort.InferenceSession.create('model.onnx');
const input = new ort.Tensor('float32', new Float32Array(1 * 3 * 224 * 224), [1, 3, 224, 224]);
const results = await session.run({{ input: input }});
console.log(results);
"""
        return {
            "runtime": "onnx_web",
            "task_type": task_type,
            "model": model_id or "custom-onnx-model",
            "html": f"""<!DOCTYPE html>
<html>
<head><title>ONNX Runtime Web Inference</title></head>
<body>
<h1>Browser AI: ONNX Runtime Web</h1>
<pre id="output">Loading ONNX model...</pre>
<script type="module">
{js_code}
document.getElementById('output').textContent = JSON.stringify(results, null, 2);
</script>
</body>
</html>""",
            "javascript": js_code.strip(),
        }

    def _gen_tfjs_template(self, task_type: str,
                            model_id: Optional[str] = None) -> Dict[str, Any]:
        """Generate TensorFlow.js inference template."""
        js_code = f"""
import * as tf from 'https://cdn.jsdelivr.net/npm/@tensorflow/tfjs@4';

const model = await tf.loadLayersModel('model.json');
const input = tf.randomNormal([1, 224, 224, 3]);
const output = model.predict(input);
output.print();
"""
        return {
            "runtime": "tensorflow_js",
            "task_type": task_type,
            "model": model_id or "custom-tfjs-model",
            "html": f"""<!DOCTYPE html>
<html>
<head><title>TensorFlow.js Inference</title></head>
<body>
<h1>Browser AI: TensorFlow.js</h1>
<pre id="output">Loading TF.js model...</pre>
<script type="module">
{js_code}
document.getElementById('output').textContent = 'Model loaded and executed.';
</script>
</body>
</html>""",
            "javascript": js_code.strip(),
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get browser AI statistics."""
        runtime_count = len(self._runtimes)
        model_count = len(self._models)
        categories = {}
        for m in self._models:
            categories[m.category] = categories.get(m.category, 0) + 1
        runtimes_used = {}
        for m in self._models:
            runtimes_used[m.runtime.value] = runtimes_used.get(m.runtime.value, 0) + 1

        return {
            "runtime_count": runtime_count,
            "model_count": model_count,
            "categories": categories,
            "runtimes_used": runtimes_used,
            "tier": 4,
            "tier_description": "Browser AI — Tier 4 fallback for edge and privacy use cases",
        }

    def to_negotiation_candidates(self, task_type: str) -> List[Dict[str, Any]]:
        """Generate negotiation engine candidates for browser AI fallback."""
        candidates = []
        for m in self._models:
            if task_type in ("text_generation",) and m.category == "llm":
                candidates.append({
                    "provider": f"browser_{m.runtime.value}",
                    "model": m.model_id,
                    "layer": "browser",
                    "tier": 4,
                    "cost_usd": 0.0,
                    "latency_estimate_ms": m.performance_estimate.get("latency_ms", 5000),
                    "quality_estimate": 0.6,
                    "requires_network": False,
                    "metadata": {
                        "runtime": m.runtime.value,
                        "backend": m.backend.value,
                        "memory_mb": m.memory_mb,
                    },
                })
        return candidates
