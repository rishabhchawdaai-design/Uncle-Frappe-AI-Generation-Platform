"""
Kimi K3 Integration — Moonshot AI Kimi K3 as an execution runtime.

Kimi K3 is an open-weight multimodal reasoning model (text + image) with a
1,048,576-token context window. This module makes the platform capable of
automatically using Kimi K3 through every OFFICIALLY supported execution path:

1.  Official Cloud API      — https://api.moonshot.ai/v1 (OpenAI-compatible)
2.  vLLM                    — vllm/vllm-openai:kimi-k3 (self-hosted)
3.  SGLang                  — lmsysorg/sglang:kimi-k3 (self-hosted)
4.  TokenSpeed              — lightseekorg/tokenspeed (per official model card)

Officially UNSUPPORTED runtimes (recorded, never faked):
TensorRT-LLM, DeepSpeed, llama.cpp, Ollama, HuggingFace Inference/TGI,
HuggingFace Endpoints, GGUF (Moonshot publishes no official GGUF).

Every fact in KIMI_K3_SPEC is sourced from official documentation only:
- https://huggingface.co/moonshotai/Kimi-K3 (config.json + model card)
- https://github.com/MoonshotAI/Kimi-K3 (README)
- https://platform.kimi.ai/docs (kimi-k3-quickstart, use-thinking-effort)
- https://recipes.vllm.ai/moonshotai/Kimi-K3 (official vLLM recipe)
- https://docs.sglang.io/cookbook/autoregressive/Moonshotai/Kimi-K3 (official SGLang recipe)
"""
import asyncio
import json
import logging
import os
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────
# Canonical verified specification (official sources only)
# ──────────────────────────────────────────────────────────────────

KIMI_K3_SPEC: Dict[str, Any] = {
    "model": "kimi-k3",
    "model_id": "moonshotai/Kimi-K3",
    "model_type": "kimi_k3",
    "architecture": {
        "family": "MoE (Latent MoE)",
        "total_params": "2.8T",
        "active_params": "104B",
        "layers": 93,
        "hidden_size": 7168,
        "experts": 896,
        "experts_per_token": 16,
        "shared_experts": 2,
        "attention": "69 KDA + 24 Gated MLA",
        "activation": "SiTU-GLU",
        "multimodal": True,
        "vision_encoder": "MoonViT-V2 (401M)",
        "quantization_aware": True,
        "weights_dtype": "MXFP4",
        "activations_dtype": "MXFP8",
        "compute_dtype": "BF16",
    },
    "tokenizer": {
        "name": "TikTokenTokenizer",
        "family": "YToken",
        "vocab_size": 163840,
        "pad_token_id": 163839,
        "bos_token_id": 163584,
        "eos_token_id": 163586,
        "image_token_id": 163605,
    },
    "context_length": 1048576,
    "thinking": {
        "always_on": True,
        "reasoning_effort": ["low", "high", "max"],
        "default_reasoning_effort": "max",
        "reasoning_content_field": "reasoning_content",
        "preserved_thinking": True,
    },
    "license": {
        "name": "Kimi K3 License",
        "open_weights": True,
        "api_usage": "subject to Moonshot AI Terms of Service",
        "note": "Do not vendor weights; download from official source at runtime",
    },
    "engines": {
        "cloud_api": {
            "supported": True,
            "base_url": "https://api.moonshot.ai/v1",
            "chat_endpoint": "/chat/completions",
            "api": "OpenAI-compatible chat completions",
            "auth": "Bearer MOONSHOT_API_KEY",
            "model": "kimi-k3",
            "context": 1048576,
            "caching": "automatic context caching",
            "also_compatible": "Anthropic-compatible per official model card",
            "vision_input": True,
        },
        "vllm": {
            "supported": True,
            "min_version": "0.27.0",
            "images": {
                "nvidia": "vllm/vllm-openai:kimi-k3",
                "amd": "vllm/vllm-openai-rocm:kimi-k3",
            },
            "api": "OpenAI-compatible chat completions",
            "parsers": ["--tool-call-parser kimi_k3", "--enable-auto-tool-choice", "--reasoning-parser kimi_k3"],
            "hardware_recipes": ["blackwell", "hopper", "amd"],
            "parallelism": ["tensor_parallel", "expert_parallel", "pipeline_parallel", "multi_node"],
            "speculative_decoding": "DSpark (Inferact/Kimi-K3-DSpark)",
            "language_model_only": True,
        },
        "sglang": {
            "supported": True,
            "images": ["lmsysorg/sglang:kimi-k3", "lmsysorg/sglang:kimi-k3-cu12",
                       "lmsysorg/sglang-rocm:rocm720-mi35x-k3-20260727"],
            "api": "OpenAI-compatible chat completions",
            "parsers": ["--reasoning-parser kimi_k3", "--tool-call-parser kimi_k3"],
            "hardware_recipes": {
                "b200": "2x8", "gb200": "4x4", "h100": "4x8",
                "b300": "1x8", "h200": "2x8", "mi350x": "1x8", "mi355x": "1x8",
            },
            "parallelism": ["tensor_parallel", "data_parallel", "pipeline_parallel", "pd_disaggregation"],
            "features": ["HiCache hierarchical KV caching", "Deep PP", "DSpark spec-decode", "DFLASH"],
        },
        "tokenspeed": {
            "supported": True,
            "repo": "lightseekorg/tokenspeed",
            "note": "Official model card lists TokenSpeed as a deployment option",
        },
    },
    "unsupported_runtimes": {
        "tensorrt_llm": "No official TensorRT-LLM recipe published by Moonshot AI",
        "deepspeed": "No official DeepSpeed inference support published",
        "llamacpp": "No official llama.cpp support; Moonshot publishes no GGUF",
        "ollama": "No official Ollama support published",
        "huggingface_inference": "No official HF Inference/TGI deployment published",
        "huggingface_endpoints": "No official HF Endpoints deployment published",
        "gguf": "No official GGUF weights; third-party conversions only",
    },
    "deployment": {
        "self_hosted": True,
        "docker": True,
        "kubernetes": True,
        "min_gpus": 8,
        "min_vram_gb": 1680,
        "min_vram_note": "MXFP4 variant; H100 requires 32 GPUs per official recipe",
    },
    "documentation": {
        "huggingface": "https://huggingface.co/moonshotai/Kimi-K3",
        "github": "https://github.com/MoonshotAI/Kimi-K3",
        "platform_kimi": "https://platform.kimi.ai/docs",
        "vllm_recipe": "https://recipes.vllm.ai/moonshotai/Kimi-K3",
        "sglang_recipe": "https://docs.sglang.io/cookbook/autoregressive/Moonshotai/Kimi-K3",
    },
}

# Official execution endpoints registered with the platform.
KIMI_K3_ENDPOINTS = [
    {
        "name": "kimi_k3_cloud",
        "url_env": "KIMI_K3_API_BASE",
        "default_url": "https://api.moonshot.ai/v1",
        "auth_env_var": "MOONSHOT_API_KEY",
        "layer": "public_api",
        "client": "cloud",
    },
    {
        "name": "kimi_k3_vllm",
        "url_env": "KIMI_K3_VLLM_URL",
        "default_url": "http://localhost:8000",
        "auth_env_var": "KIMI_K3_VLLM_API_KEY",
        "layer": "user_configured",
        "client": "vllm",
    },
    {
        "name": "kimi_k3_sglang",
        "url_env": "KIMI_K3_SGLANG_URL",
        "default_url": "http://localhost:30000",
        "auth_env_var": "KIMI_K3_SGLANG_API_KEY",
        "layer": "user_configured",
        "client": "sglang",
    },
]


class KimiK3Error(Exception):
    """Raised for Kimi K3 request failures."""


# ──────────────────────────────────────────────────────────────────
# HTTP helper (stdlib-first; httpx is the only optional HTTP client)
# ──────────────────────────────────────────────────────────────────

async def _post_json(url: str, api_key: str, payload: Dict[str, Any],
                     timeout: float = 120.0) -> Dict[str, Any]:
    """POST an OpenAI-compatible chat completion request and return JSON."""
    import httpx

    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(url, headers=headers, json=payload)
    except Exception as e:
        raise KimiK3Error(f"request failed: {e}") from e
    if resp.status_code >= 400:
        detail = resp.text[:300] if resp.text else resp.reason_phrase
        raise KimiK3Error(f"HTTP {resp.status_code}: {detail}")
    try:
        return resp.json()
    except Exception as e:
        raise KimiK3Error(f"invalid JSON response: {e}") from e


async def _get_json(url: str, api_key: str = "", timeout: float = 15.0) -> Dict[str, Any]:
    """GET an OpenAI-compatible endpoint (used for health/model checks)."""
    import httpx

    headers = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.get(url, headers=headers)
    except Exception as e:
        raise KimiK3Error(f"health check failed: {e}") from e
    if resp.status_code >= 400:
        raise KimiK3Error(f"HTTP {resp.status_code}")
    try:
        return resp.json()
    except Exception:
        return {}


# ──────────────────────────────────────────────────────────────────
# Message building & response parsing (OpenAI-compatible)
# ──────────────────────────────────────────────────────────────────

def build_chat_messages(prompt: str, system_prompt: str = "", images: Optional[List[str]] = None,
                        history: Optional[List[Dict[str, Any]]] = None,
                        preserve_thinking: bool = True) -> List[Dict[str, Any]]:
    """Build an OpenAI-compatible messages list with preserved-thinking support.

    - `history` items use {"role", "content", "reasoning_content", "tool_calls"}.
    - When an assistant message carries `reasoning_content`, it is echoed back
      verbatim so multi-turn preserved-thinking works (official Kimi K3 behavior).
    - Images are attached as `image_url` content parts (official vision support).
    """
    messages: List[Dict[str, Any]] = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})

    for m in history or []:
        role = m.get("role", "user")
        if role == "assistant" and preserve_thinking and m.get("reasoning_content"):
            messages.append({
                "role": "assistant",
                "content": m.get("content", ""),
                "reasoning_content": m.get("reasoning_content"),
                "tool_calls": m.get("tool_calls", []),
            })
        else:
            messages.append({"role": role, "content": m.get("content", "")})

    parts: List[Dict[str, Any]] = [{"type": "text", "text": prompt}]
    for img in images or []:
        parts.append({"type": "image_url", "image_url": {"url": img}})
    user_content: Any = parts if len(parts) > 1 else prompt
    messages.append({"role": "user", "content": user_content})
    return messages


def build_chat_payload(prompt: str, model: str = "kimi-k3", system_prompt: str = "",
                       images: Optional[List[str]] = None, history: Optional[List[Dict[str, Any]]] = None,
                       reasoning_effort: str = "max", max_tokens: Optional[int] = None,
                       temperature: Optional[float] = None, top_p: Optional[float] = None,
                       stream: bool = False, preserve_thinking: bool = True,
                       tools: Optional[List[Dict[str, Any]]] = None,
                       tool_choice: Any = None) -> Dict[str, Any]:
    """Build a Kimi K3 chat completion request body (official parameters only)."""
    if reasoning_effort not in ("low", "high", "max"):
        reasoning_effort = "max"
    body: Dict[str, Any] = {
        "model": model,
        "messages": build_chat_messages(
            prompt, system_prompt=system_prompt, images=images,
            history=history, preserve_thinking=preserve_thinking,
        ),
        "reasoning_effort": reasoning_effort,
        "stream": stream,
    }
    if max_tokens is not None:
        body["max_tokens"] = int(max_tokens)
    if temperature is not None:
        body["temperature"] = float(temperature)
    if top_p is not None:
        body["top_p"] = float(top_p)
    if tools:
        body["tools"] = tools
    if tool_choice is not None:
        body["tool_choice"] = tool_choice
    return body


def parse_chat_response(data: Dict[str, Any]) -> Dict[str, Any]:
    """Parse an OpenAI-compatible chat completion response into a normalized dict."""
    choices = data.get("choices") or []
    if not choices:
        raise KimiK3Error("response contained no choices")
    choice = choices[0]
    message = choice.get("message") or {}
    content = message.get("content") or ""
    reasoning = message.get("reasoning_content") or ""
    usage = data.get("usage") or {}
    return {
        "text": content,
        "reasoning": reasoning,
        "finish_reason": choice.get("finish_reason", ""),
        "model": data.get("model", ""),
        "usage": usage,
        "prompt_tokens": usage.get("prompt_tokens", 0),
        "completion_tokens": usage.get("completion_tokens", 0),
        "total_tokens": usage.get("total_tokens", 0),
        "cached_tokens": usage.get("prompt_tokens_details", {}).get("cached_tokens", 0),
    }


# ──────────────────────────────────────────────────────────────────
# Clients (cloud + self-hosted vLLM/SGLang)
# ──────────────────────────────────────────────────────────────────

class KimiK3Client:
    """OpenAI-compatible chat client for a single Kimi K3 endpoint."""

    def __init__(self, base_url: str, api_key: str = "", model: str = "kimi-k3",
                 timeout: float = 120.0):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key or ""
        self.model = model or "kimi-k3"
        self.timeout = timeout

    @property
    def chat_url(self) -> str:
        return f"{self.base_url}/chat/completions"

    @property
    def models_url(self) -> str:
        return f"{self.base_url}/models"

    async def chat(self, prompt: str, **kwargs) -> Dict[str, Any]:
        payload = build_chat_payload(prompt, model=kwargs.pop("model", self.model), **kwargs)
        data = await _post_json(self.chat_url, self.api_key, payload, timeout=self.timeout)
        return parse_chat_response(data)

    async def health(self) -> Dict[str, Any]:
        """Check endpoint availability and list served models."""
        try:
            data = await _get_json(self.models_url, self.api_key)
            models = [m.get("id", "") for m in data.get("data", [])]
            return {"healthy": True, "models": models, "serves_kimi_k3": any(
                "kimi" in m.lower() for m in models
            )}
        except Exception as e:
            return {"healthy": False, "error": str(e)[:200], "models": []}


class KimiK3CloudClient(KimiK3Client):
    """Official Moonshot AI cloud API client (https://api.moonshot.ai/v1)."""

    def __init__(self, base_url: str = "https://api.moonshot.ai/v1", api_key: str = "",
                 model: str = "kimi-k3", timeout: float = 120.0):
        super().__init__(base_url=base_url, api_key=api_key, model=model, timeout=timeout)


class KimiK3VllmServer(KimiK3Client):
    """Self-hosted vLLM server (vllm/vllm-openai:kimi-k3)."""


class KimiK3SglangServer(KimiK3Client):
    """Self-hosted SGLang server (lmsysorg/sglang:kimi-k3)."""


CLIENT_CLASSES: Dict[str, Callable[..., KimiK3Client]] = {
    "cloud": KimiK3CloudClient,
    "vllm": KimiK3VllmServer,
    "sglang": KimiK3SglangServer,
}


# ──────────────────────────────────────────────────────────────────
# Official launch command builders (verified flags only)
# ──────────────────────────────────────────────────────────────────

VLLM_COMMON_ARGS = [
    "--trust-remote-code",
    "--moe-backend", "auto",
    "--gpu-memory-utilization", "0.95",
    "--tool-call-parser", "kimi_k3",
    "--enable-auto-tool-choice",
    "--reasoning-parser", "kimi_k3",
]

VLLM_HARDWARE_ARGS = {
    "blackwell": [
        "--load-format", "fastsafetensors",
        "--max-model-len", "1048576",
        "--kv-cache-dtype", "fp8",
        "--attention-config", '{"use_prefill_query_quantization":true}',
        "--enable-prefix-caching",
    ],
    "hopper": [
        "--moe-backend", "marlin",
        "--attention-backend", "FLASHMLA",
        "--max-model-len", "32768",
        "--max-num-seqs", "5",
    ],
    "amd": [
        "--mm-encoder-tp-mode", "data",
        "--max-num-seqs", "128",
        "--max-num-batched-tokens", "4096",
    ],
}

VLLM_HARDWARE_ENV = {
    "blackwell": {
        "VLLM_ENABLE_K3_LATENT_MOE_TAIL_FUSION": "1",
        "VLLM_ALLREDUCE_USE_FLASHINFER": "1",
        "VLLM_ENGINE_READY_TIMEOUT_S": "3600",
        "VLLM_USE_V2_MODEL_RUNNER": "1",
        "VLLM_USE_RUST_FRONTEND": "1",
    },
    "hopper": {
        "VLLM_ENGINE_READY_TIMEOUT_S": "3600",
        "VLLM_USE_V2_MODEL_RUNNER": "1",
        "VLLM_USE_RUST_FRONTEND": "1",
        "PYTORCH_CUDA_ALLOC_CONF": "expandable_segments:True",
    },
    "amd": {
        "VLLM_ROCM_USE_AITER": "1",
        "SAFETENSORS_FAST_GPU": "1",
        "AITER_SITUV2_A8W4": "1",
        "VLLM_USE_BREAKABLE_CUDAGRAPH": "0",
    },
}


def build_vllm_command(model: str = "moonshotai/Kimi-K3", hardware: str = "blackwell",
                       tensor_parallel: int = 8, expert_parallel: int = 16,
                       pipeline_parallel: int = 1, spec_decode: bool = False,
                       language_model_only: bool = False,
                       all2all_backend: str = "") -> Dict[str, Any]:
    """Return an official vLLM launch command for Kimi K3.

    Official recipe: https://recipes.vllm.ai/moonshotai/Kimi-K3
    """
    if hardware not in VLLM_HARDWARE_ARGS:
        hardware = "blackwell"
    args = list(VLLM_COMMON_ARGS) + list(VLLM_HARDWARE_ARGS[hardware])
    args += ["--model", model]
    args += ["--tensor-parallel-size", str(tensor_parallel)]
    args += ["--expert-parallel-size", str(expert_parallel)]
    if pipeline_parallel > 1:
        args += ["--pipeline-parallel-size", str(pipeline_parallel)]
    if spec_decode:
        args += [
            "--speculative-config",
            json.dumps({
                "model": "Inferact/Kimi-K3-DSpark",
                "num_speculative_tokens": 7,
                "method": "dspark",
                "attention_backend": "FLASHINFER_MLA",
                "draft_sample_method": "probabilistic",
                "rejection_sample_method": "block",
            }),
        ]
    if language_model_only:
        args += ["--language-model-only"]
    if all2all_backend:
        args += ["--all2all-backend", all2all_backend]

    env = dict(VLLM_HARDWARE_ENV[hardware])
    if hardware == "amd" and spec_decode:
        env["VLLM_USE_TRITON_MLA"] = "1"
    image = "vllm/vllm-openai:kimi-k3"
    if hardware == "amd":
        image = "vllm/vllm-openai-rocm:kimi-k3"

    notes = []
    if hardware == "blackwell":
        notes.append("Requires CUDA 13 + r580+ driver; TP8/TEP16 for 8x Blackwell")
    elif hardware == "hopper":
        notes.append("H100 recipe requires 32 GPUs; TP8/TEP16 baseline")
    elif hardware == "amd":
        notes.append("ROCm MI350X recipe; mm-encoder data parallel")
    if spec_decode:
        notes.append("DSpark speculative decoding via Inferact/Kimi-K3-DSpark (num_speculative_tokens=7)")
    if pipeline_parallel > 1:
        notes.append("Multi-node PP: use --distributed-executor-backend ray + node configs")

    return {
        "engine": "vllm",
        "image": image,
        "command": ["python", "-m", "vllm.entrypoints.openai.api_server"] + args,
        "env": env,
        "hardware": hardware,
        "parallelism": {
            "tensor_parallel": tensor_parallel,
            "expert_parallel": expert_parallel,
            "pipeline_parallel": pipeline_parallel,
        },
        "notes": notes,
        "min_vram_gb": 1680,
    }


SGLANG_COMMON_ARGS = [
    "--reasoning-parser", "kimi_k3",
    "--tool-call-parser", "kimi_k3",
    "--kv-cache-dtype", "fp8_e4m3",
    "--moe-a2a-backend", "megamoe",
    "--moe-runner-backend", "deep_gemm",
]

SGLANG_RECIPES = {
    "b200": {"tp": 16, "dp": 16, "image": "lmsysorg/sglang:kimi-k3"},
    "gb200": {"tp": 16, "dp": 16, "image": "lmsysorg/sglang:kimi-k3"},
    "h100": {"tp": 8, "dp": 8, "image": "lmsysorg/sglang:kimi-k3-cu12"},
    "h200": {"tp": 8, "dp": 8, "image": "lmsysorg/sglang:kimi-k3-cu12"},
    "b300": {"tp": 8, "dp": 8, "image": "lmsysorg/sglang:kimi-k3-cu12"},
    "mi350x": {"tp": 8, "dp": 8, "image": "lmsysorg/sglang-rocm:rocm720-mi35x-k3-20260727"},
    "mi355x": {"tp": 8, "dp": 8, "image": "lmsysorg/sglang-rocm:rocm720-mi35x-k3-20260727"},
}


def build_sglang_command(model: str = "moonshotai/Kimi-K3", hardware: str = "b200",
                         tp: Optional[int] = None, dp: Optional[int] = None,
                         pp_size: int = 0, dp_attention: bool = False,
                         enable_dp_lm_head: bool = False,
                         spec_decode: bool = False, nnodes: int = 1,
                         dist_init_addr: str = "") -> Dict[str, Any]:
    """Return an official SGLang launch command for Kimi K3.

    Official recipe: https://docs.sglang.io/cookbook/autoregressive/Moonshotai/Kimi-K3
    """
    recipe = SGLANG_RECIPES.get(hardware, SGLANG_RECIPES["b200"])
    tensor_p = tp or recipe["tp"]
    data_p = dp or recipe["dp"]
    args = list(SGLANG_COMMON_ARGS)
    args += ["--model-path", model]
    args += ["--tp-size", str(tensor_p)]
    args += ["--dp-size", str(data_p)]
    if pp_size > 1:
        # PD disaggregation: long-context prefill pool with separate decode pool.
        args += ["--pp-size", str(pp_size), "--tp-size", "1", "--dp-size", "1"]
    if dp_attention:
        args += ["--enable-dp-attention"]
    if enable_dp_lm_head:
        args += ["--enable-dp-lm-head"]
    if spec_decode:
        args += ["--speculative-algorithm", "DSPARK"]
    if nnodes > 1:
        args += ["--nnodes", str(nnodes), "--node-rank", "0"]
        if dist_init_addr:
            args += ["--dist-init-addr", dist_init_addr]
    args += ["--host", "0.0.0.0", "--port", "30000"]

    env = {}
    if hardware in ("mi350x", "mi355x"):
        env = {"VLLM_ROCM_USE_AITER": "1", "AITER_SITUV2_A8W4": "1"}

    return {
        "engine": "sglang",
        "image": recipe["image"],
        "command": ["python", "-m", "sglang.launch_server"] + args,
        "env": env,
        "hardware": hardware,
        "parallelism": {"tensor_parallel": tensor_p, "data_parallel": data_p},
        "notes": [
            f"Official recipe: {hardware.upper()} {recipe['tp']}xTP / {recipe['dp']}xDP",
            "PD disaggregation available for 1M long-context prefill",
            "HiCache hierarchical KV caching enabled by default in K3 image",
        ],
        "min_vram_gb": 1680,
    }


# ──────────────────────────────────────────────────────────────────
# Manager — intelligent runtime selection across all K3 paths
# ──────────────────────────────────────────────────────────────────

@dataclass
class KimiK3Request:
    prompt: str = ""
    provider: str = "auto"  # auto | kimi_k3_cloud | kimi_k3_vllm | kimi_k3_sglang
    system_prompt: str = ""
    images: List[str] = field(default_factory=list)
    history: List[Dict[str, Any]] = field(default_factory=list)
    reasoning_effort: str = "max"
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    timeout_secs: float = 120.0


@dataclass
class KimiK3Result:
    text: str = ""
    reasoning: str = ""
    provider: str = ""
    model: str = "kimi-k3"
    latency_ms: float = 0.0
    usage: Dict[str, Any] = field(default_factory=dict)
    quality_score: float = 0.0
    fallbacks: List[str] = field(default_factory=list)
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "reasoning": self.reasoning,
            "provider": self.provider,
            "model": self.model,
            "latency_ms": round(self.latency_ms, 1),
            "usage": self.usage,
            "quality_score": round(self.quality_score, 2),
            "fallbacks": self.fallbacks,
            "error": self.error,
        }


class KimiK3Manager:
    """Unified Kimi K3 execution manager with automatic runtime selection.

    Selection order: cloud API → self-hosted vLLM → self-hosted SGLang.
    Falls back across paths, records decisions in the Decision Ledger,
    evaluates quality, tracks benchmarks, and reports failures.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None,
                 benchmark_lab=None):
        self.config = config or {}
        self._benchmark_lab = benchmark_lab
        self._history: List[Dict[str, Any]] = []
        self._stats: Dict[str, Any] = {
            "total_requests": 0,
            "successful": 0,
            "failed": 0,
            "by_provider": {},
            "total_latency_ms": 0.0,
        }
        self._ledger = None
        self._quality_engine = None
        self._benchmark_engine = None
        self._failure_recovery = None

    # ── Injected subsystems (lazy, optional) ──

    @property
    def ledger(self):
        if self._ledger is None:
            from .decision_ledger import DecisionLedger
            self._ledger = DecisionLedger(self.config)
        return self._ledger

    @property
    def quality_engine(self):
        if self._quality_engine is None:
            from .quality_engine import QualityEngine
            self._quality_engine = QualityEngine()
        return self._quality_engine

    @property
    def benchmark_engine(self):
        if self._benchmark_engine is None:
            from .benchmark_engine import BenchmarkEngine
            self._benchmark_engine = BenchmarkEngine()
        return self._benchmark_engine

    @property
    def failure_recovery(self):
        if self._failure_recovery is None:
            from .failure_recovery import FailureRecoveryEngine
            self._failure_recovery = FailureRecoveryEngine(self.config)
        return self._failure_recovery

    # ── Endpoint discovery ──

    def configured_endpoints(self) -> List[Dict[str, Any]]:
        """Return K3 endpoints that are configured (env URL present or default)."""
        endpoints = []
        for ep in KIMI_K3_ENDPOINTS:
            url = os.environ.get(ep["url_env"], self.config.get(ep["url_env"], ep["default_url"]))
            auth = os.environ.get(ep["auth_env_var"], "")
            endpoints.append({
                "name": ep["name"],
                "url": url,
                "auth_env_var": ep["auth_env_var"],
                "api_key_set": bool(auth),
                "layer": ep["layer"],
                "client": ep["client"],
                "model": "kimi-k3",
            })
        return endpoints

    def provider_order(self, provider: str = "auto") -> List[Dict[str, Any]]:
        endpoints = {e["name"]: e for e in self.configured_endpoints()}
        order = ["kimi_k3_cloud", "kimi_k3_vllm", "kimi_k3_sglang"]
        if provider and provider != "auto":
            if provider not in endpoints:
                raise KimiK3Error(f"unknown Kimi K3 provider: {provider}")
            order = [provider]
        return [endpoints[n] for n in order if n in endpoints]

    def _make_client(self, endpoint: Dict[str, Any]) -> KimiK3Client:
        cls = CLIENT_CLASSES.get(endpoint["client"], KimiK3CloudClient)
        api_key = os.environ.get(endpoint["auth_env_var"], "")
        return cls(base_url=endpoint["url"], api_key=api_key, model="kimi-k3",
                   timeout=float(self.config.get("kimi_k3_timeout_secs", 120.0)))

    # ── Chat execution ──

    async def chat(self, prompt: str, provider: str = "auto", system_prompt: str = "",
                   images: Optional[List[str]] = None, history: Optional[List[Dict[str, Any]]] = None,
                   reasoning_effort: str = "max", max_tokens: Optional[int] = None,
                   temperature: Optional[float] = None, top_p: Optional[float] = None,
                   timeout_secs: float = 120.0) -> KimiK3Result:
        request = KimiK3Request(
            prompt=prompt, provider=provider, system_prompt=system_prompt,
            images=images or [], history=history or [],
            reasoning_effort=reasoning_effort, max_tokens=max_tokens,
            temperature=temperature, top_p=top_p, timeout_secs=timeout_secs,
        )
        return await self._execute(request)

    async def _execute(self, request: KimiK3Request) -> KimiK3Result:
        fallbacks: List[str] = []
        last_error: Optional[str] = None
        for endpoint in self.provider_order(request.provider):
            start = time.time()
            client = self._make_client(endpoint)
            try:
                parsed = await asyncio.wait_for(
                    client.chat(
                        request.prompt,
                        system_prompt=request.system_prompt,
                        images=request.images,
                        history=request.history,
                        reasoning_effort=request.reasoning_effort,
                        max_tokens=request.max_tokens,
                        temperature=request.temperature,
                        top_p=request.top_p,
                    ),
                    timeout=request.timeout_secs,
                )
            except Exception as e:
                latency = round((time.time() - start) * 1000, 1)
                last_error = str(e)[:300]
                self._record(endpoint["name"], latency, success=False, error=last_error)
                self._record_failure(request, endpoint["name"], last_error, latency)
                fallbacks.append(endpoint["name"])
                logger.warning("Kimi K3 provider %s failed: %s", endpoint["name"], last_error)
                continue

            latency = round((time.time() - start) * 1000, 1)
            result = KimiK3Result(
                text=parsed["text"],
                reasoning=parsed["reasoning"],
                provider=endpoint["name"],
                model=parsed.get("model") or "kimi-k3",
                latency_ms=latency,
                usage=parsed["usage"],
                fallbacks=fallbacks,
            )
            quality = self._score_chat(request.prompt, result)
            result.quality_score = quality
            self._record(endpoint["name"], latency, success=True, usage=parsed["usage"])
            self._record_decision(request, result, quality)
            return result

        result = KimiK3Result(error=last_error or "all Kimi K3 providers failed",
                              fallbacks=fallbacks, provider=request.provider)
        self._record(request.provider, 0.0, success=False, error=result.error)
        return result

    def _score_chat(self, prompt: str, result: KimiK3Result) -> float:
        """Quality score for a chat response (prompt relevance + completeness)."""
        try:
            report = self.quality_engine.evaluate_chat(prompt, result.text)
            return report.overall_score
        except Exception:
            return 50.0

    def _record(self, provider: str, latency_ms: float, success: bool,
                usage: Optional[Dict[str, Any]] = None, error: str = ""):
        self._stats["total_requests"] += 1
        if success:
            self._stats["successful"] += 1
        else:
            self._stats["failed"] += 1
        self._stats["total_latency_ms"] += latency_ms
        p = self._stats["by_provider"].setdefault(provider, {
            "requests": 0, "successful": 0, "failed": 0, "total_latency_ms": 0.0,
        })
        p["requests"] += 1
        p["successful"] += 1 if success else 0
        p["failed"] += 0 if success else 1
        p["total_latency_ms"] += latency_ms
        self._history.append({
            "provider": provider, "success": success, "latency_ms": latency_ms,
            "error": error, "timestamp": datetime.now().isoformat(),
        })

    def _record_decision(self, request: KimiK3Request, result: KimiK3Result, quality: float):
        try:
            from .decision_ledger import DecisionOutcome
            self.ledger.record_generation(
                request_id=f"kimi-{int(time.time() * 1000)}",
                prompt=request.prompt[:200],
                task_type="chat",
                provider=result.provider,
                model=result.model,
                outcome=DecisionOutcome.SUCCESS,
                latency_ms=result.latency_ms,
                quality_score=quality,
            )
        except Exception as e:
            logger.debug("decision ledger record skipped: %s", e)

    def _record_failure(self, request: KimiK3Request, provider: str, error: str, latency_ms: float):
        try:
            from .decision_ledger import DecisionOutcome
            self.ledger.record_generation(
                request_id=f"kimi-{int(time.time() * 1000)}",
                prompt=request.prompt[:200],
                task_type="chat",
                provider=provider,
                model="kimi-k3",
                outcome=DecisionOutcome.FAILURE,
                latency_ms=latency_ms,
                error=error,
            )
            recovery = self.failure_recovery.attempt_recovery(
                error, {"provider": provider, "task_type": "chat", "model": "kimi-k3"}
            )
            if recovery and getattr(recovery, "success", False):
                self.ledger.record_recovery(
                    request_id=f"kimi-{int(time.time() * 1000)}",
                    failed_provider=provider,
                    error=error,
                    recovery_provider=request.provider,
                    reasoning=recovery.final_action or "automatic recovery applied",
                )
        except Exception as e:
            logger.debug("failure recovery record skipped: %s", e)

    # ── Health ──

    async def health(self) -> Dict[str, Any]:
        """Health-check every configured K3 endpoint."""
        results = {}
        for endpoint in self.configured_endpoints():
            try:
                client = self._make_client(endpoint)
                h = await client.health()
                results[endpoint["name"]] = {
                    "url": endpoint["url"],
                    "healthy": h.get("healthy", False),
                    "models": h.get("models", [])[:20],
                    "serves_kimi_k3": h.get("serves_kimi_k3", False),
                    "error": h.get("error", ""),
                }
            except Exception as e:
                results[endpoint["name"]] = {
                    "url": endpoint["url"], "healthy": False, "error": str(e)[:200],
                }
        return results

    # ── Benchmark ──

    async def benchmark(self, prompt: str, runs: int = 2, provider: str = "auto",
                        reasoning_effort: str = "low") -> Dict[str, Any]:
        """Benchmark K3 chat latency/quality across the configured provider."""
        runs = max(1, int(runs))
        results = []
        for _ in range(runs):
            start = time.time()
            result = await self.chat(prompt, provider=provider,
                                     reasoning_effort=reasoning_effort)
            latency = result.latency_ms or round((time.time() - start) * 1000, 1)
            entry = {
                "provider": result.provider,
                "success": result.error is None,
                "latency_ms": latency,
                "quality_score": result.quality_score,
                "completion_tokens": result.usage.get("completion_tokens", 0),
                "error": result.error or "",
            }
            results.append(entry)
            try:
                self.benchmark_engine._results.append(_BenchmarkRecord(
                    provider=result.provider, prompt=prompt[:200], success=entry["success"],
                    latency_ms=latency, error=entry["error"],
                ))
            except Exception:
                pass
            if self._benchmark_lab is not None:
                try:
                    from .benchmark_lab import BenchmarkResult as LabBenchmarkResult
                    self._benchmark_lab.record_result(LabBenchmarkResult(
                        provider=result.provider,
                        model=result.model,
                        category="chat",
                        prompt=prompt[:200],
                        quality_score=result.quality_score,
                        prompt_adherence=result.quality_score,
                        latency_ms=latency,
                        success=entry["success"],
                        error=entry["error"],
                    ))
                except Exception:
                    pass
        return {
            "prompt": prompt[:200],
            "runs": results,
            "stats": self.benchmark_engine.get_stats(),
        }

    # ── Info / stats ──

    def info(self) -> Dict[str, Any]:
        """Return the canonical K3 spec, supported paths, and configuration state."""
        return {
            "spec": KIMI_K3_SPEC,
            "supported_paths": [
                {"name": "cloud_api", "supported": True, "description": KIMI_K3_SPEC["engines"]["cloud_api"]["api"]},
                {"name": "vllm", "supported": True, "description": "Self-hosted vLLM (vllm/vllm-openai:kimi-k3)"},
                {"name": "sglang", "supported": True, "description": "Self-hosted SGLang (lmsysorg/sglang:kimi-k3)"},
                {"name": "tokenspeed", "supported": True, "description": KIMI_K3_SPEC["engines"]["tokenspeed"]["note"]},
            ],
            "unsupported_paths": [
                {"name": name, "supported": False, "reason": reason}
                for name, reason in KIMI_K3_SPEC["unsupported_runtimes"].items()
            ],
            "configured_endpoints": self.configured_endpoints(),
        }

    def get_stats(self) -> Dict[str, Any]:
        s = self._stats
        successful = s.get("successful", 0)
        total = s.get("total_requests", 0)
        return {
            "total_requests": total,
            "successful": successful,
            "failed": s.get("failed", 0),
            "success_rate": 100.0 if total == 0 else round(successful / total * 100, 1),
            "avg_latency_ms": round(s["total_latency_ms"] / max(total, 1), 1),
            "by_provider": s.get("by_provider", {}),
            "configured_endpoints": [e["name"] for e in self.configured_endpoints()],
            "recent": self._history[-10:],
        }


# Local BenchmarkResult-like record (avoids hard dependency on engine internals)
@dataclass
class _BenchmarkRecord:
    provider: str
    prompt: str
    success: bool = False
    latency_ms: float = 0.0
    output_bytes: int = 0
    output_url: str = ""
    cost_estimate: float = 0.0
    error: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


# ──────────────────────────────────────────────────────────────────
# Platform registration helpers
# ──────────────────────────────────────────────────────────────────

def _build_chat_task_payload(task) -> Dict[str, Any]:
    """Derive chat kwargs from an ExecutionTask (handler contract)."""
    params = task.params or {}
    input_data = task.input_data or {}
    images = params.get("images") or input_data.get("images") or []
    history = params.get("history") or input_data.get("history") or []
    return {
        "system_prompt": params.get("system_prompt", ""),
        "images": images,
        "history": history,
        "reasoning_effort": params.get("reasoning_effort", "max"),
        "max_tokens": params.get("max_tokens"),
        "temperature": params.get("temperature"),
        "top_p": params.get("top_p"),
    }


async def _kimi_k3_endpoint_handler(task, endpoint, context):
    """ExecutionEngine handler: run a Kimi K3 chat request through an endpoint."""
    from .execution_engine import ExecutionStatus

    kwargs = _build_chat_task_payload(task)
    client_type = (endpoint.metadata or {}).get("client", "cloud")
    cls = CLIENT_CLASSES.get(client_type, KimiK3CloudClient)
    auth_env = endpoint.auth_env_var or "MOONSHOT_API_KEY"
    api_key = os.environ.get(auth_env, "")
    client = cls(base_url=endpoint.url, api_key=api_key,
                 model=(endpoint.metadata or {}).get("model", "kimi-k3"))
    try:
        parsed = await client.chat(
            task.prompt,
            system_prompt=kwargs["system_prompt"],
            images=kwargs["images"],
            history=kwargs["history"],
            reasoning_effort=kwargs["reasoning_effort"],
            max_tokens=kwargs["max_tokens"],
            temperature=kwargs["temperature"],
            top_p=kwargs["top_p"],
        )
    except Exception as e:
        # The execution engine treats handler exceptions as failures and
        # continues down the fallback chain; failed dicts would be wrapped
        # as completed results.
        raise KimiK3Error(str(e)[:300]) from e
    return {
        "status": ExecutionStatus.COMPLETED.value,
        "provider": endpoint.name,
        "model": parsed.get("model") or "kimi-k3",
        "output_format": "text",
        "text": parsed["text"],
        "reasoning": parsed["reasoning"],
        "usage": parsed["usage"],
        "prompt_tokens": parsed["prompt_tokens"],
        "completion_tokens": parsed["completion_tokens"],
        "total_tokens": parsed["total_tokens"],
    }


def register_kimi_k3(engine):
    """Register Kimi K3 endpoints + handlers with an ExecutionEngine.

    Cloud API is Layer 1 (PUBLIC_API); self-hosted vLLM/SGLang are Layer 3
    (USER_CONFIGURED) and only register when their env URLs are set.
    """
    from .execution_engine import ExecutionLayer, ProviderEndpoint, TaskType

    cloud_url = os.environ.get("KIMI_K3_API_BASE", "https://api.moonshot.ai/v1")
    cloud = ProviderEndpoint(
        name="kimi_k3_cloud",
        layer=ExecutionLayer.PUBLIC_API,
        url=cloud_url,
        auth_type="api_key",
        auth_env_var="MOONSHOT_API_KEY",
        supported_tasks=[TaskType.CHAT],
        models=["kimi-k3"],
        free_tier=False,
        verified=True,
        documentation_url="https://platform.kimi.ai/docs",
        license_info="Kimi K3 License — open weights; API use subject to Moonshot AI ToS",
        estimated_latency_ms=5000,
        metadata={
            "client": "cloud", "model": "kimi-k3", "context_length": 1048576,
            "reasoning_effort": ["low", "high", "max"], "vision": True,
        },
    )
    engine.router.register_endpoint(cloud)
    engine.router.register_handler("kimi_k3_cloud", _kimi_k3_endpoint_handler)

    for name, env_var, default_url, client in (
        ("kimi_k3_vllm", "KIMI_K3_VLLM_URL", "http://localhost:8000", "vllm"),
        ("kimi_k3_sglang", "KIMI_K3_SGLANG_URL", "http://localhost:30000", "sglang"),
    ):
        url = os.environ.get(env_var, "")
        if not url:
            continue
        ep = ProviderEndpoint(
            name=name,
            layer=ExecutionLayer.USER_CONFIGURED,
            url=url,
            auth_type="api_key",
            auth_env_var=f"{env_var}_API_KEY" if env_var else "",
            supported_tasks=[TaskType.CHAT],
            models=["kimi-k3"],
            free_tier=False,
            verified=False,
            health_url=f"{url}/v1/models",
            documentation_url="https://github.com/MoonshotAI/Kimi-K3",
            license_info="Kimi K3 License — open weights",
            metadata={"client": client, "model": "kimi-k3", "context_length": 1048576},
        )
        engine.router.register_endpoint(ep)
        engine.router.register_handler(name, _kimi_k3_endpoint_handler)


def register_kimi_k3_health(monitor) -> Dict[str, Any]:
    """Register Kimi K3 endpoints with a HealthMonitor."""
    from .health_monitor import HealthMonitor

    if not isinstance(monitor, HealthMonitor):
        return {}
    registered = {}
    for ep in KIMI_K3_ENDPOINTS:
        name = ep["name"]
        health_url = ""
        if ep["layer"] != "public_api":
            url = os.environ.get(ep["url_env"], "")
            if url:
                health_url = f"{url.rstrip('/')}/v1/models"
        monitor.register_provider(name, health_url)
        registered[name] = {"health_url": health_url}
    return registered


def register_kimi_k3_graph(graph) -> int:
    """Add Kimi K3 provider/model/capability nodes to the KnowledgeGraph."""
    from .knowledge_graph import GraphEdge, GraphNode

    added = 0
    provider = graph.get_node("provider:kimi_k3")
    if provider is None:
        graph.add_node(GraphNode(
            node_id="provider:kimi_k3", node_type="provider",
            name="kimi_k3", properties={
                "model": "kimi-k3", "context_length": 1048576,
                "license": "Kimi K3 License", "engines": ["cloud_api", "vllm", "sglang", "tokenspeed"],
            },
        ))
        added += 1

    model = graph.get_node("model:kimi-k3")
    if model is None:
        graph.add_node(GraphNode(
            node_id="model:kimi-k3", node_type="model",
            name="kimi-k3", properties={
                "architecture": "MoE 2.8T/104B active",
                "context_length": 1048576,
                "multimodal": True,
                "reasoning_effort": ["low", "high", "max"],
            },
        ))
        added += 1

    cap = graph.get_node("capability:chat")
    if cap is None:
        graph.add_node(GraphNode(
            node_id="capability:chat", node_type="capability",
            name="chat", properties={"tasks": ["chat"]},
        ))
        added += 1

    edge_keys = {(e.source_id, e.target_id, e.edge_type) for e in graph._edges}
    for source, target, edge_type in (
        ("provider:kimi_k3", "model:kimi-k3", "offers_model"),
        ("model:kimi-k3", "capability:chat", "supports"),
        ("provider:kimi_k3", "capability:chat", "supports"),
    ):
        if (source, target, edge_type) not in edge_keys:
            graph.add_edge(GraphEdge(source_id=source, target_id=target, edge_type=edge_type))
            added += 1
    return added


def kimi_k3_capabilities() -> List[Dict[str, Any]]:
    """Capability Registry entries for Kimi K3 (media_type="text", task="chat")."""
    return [
        {
            "model_id": "kimi-k3-cloud", "provider": "kimi_k3_cloud",
            "model_name": "kimi-k3", "media_type": "text",
            "supported_tasks": ["chat"],
            "api_key_required": True, "free_tier": False,
            "known_limits": {
                "context_length": 1048576,
                "reasoning_effort": ["low", "high", "max"],
                "architecture": "MoE 2.8T total / 104B active",
            },
        },
        {
            "model_id": "kimi-k3-vllm", "provider": "kimi_k3_vllm",
            "model_name": "kimi-k3", "media_type": "text",
            "supported_tasks": ["chat"],
            "api_key_required": False, "free_tier": False,
            "known_limits": {"context_length": 1048576, "engine": "vLLM >= 0.27.0"},
        },
        {
            "model_id": "kimi-k3-sglang", "provider": "kimi_k3_sglang",
            "model_name": "kimi-k3", "media_type": "text",
            "supported_tasks": ["chat"],
            "api_key_required": False, "free_tier": False,
            "known_limits": {"context_length": 1048576, "engine": "SGLang (kimi-k3 image)"},
        },
    ]


def kimi_k3_candidates() -> List[Any]:
    """Build Negotiation Engine candidates for every official Kimi K3 path.

    Lets the Negotiation Engine treat K3 as a first-class execution target:
    cloud API (Layer 1) plus self-hosted vLLM/SGLang (Layer 3) with the
    official 1M context and reasoning-effort capabilities.
    """
    from .negotiation_engine import ExecutionCandidate, ExecutionLayer

    candidates = []
    for ep in KIMI_K3_ENDPOINTS:
        layer = (ExecutionLayer.PUBLIC_API if ep["layer"] == "public_api"
                 else ExecutionLayer.USER_CONFIGURED)
        url = os.environ.get(ep["url_env"], ep["default_url"])
        candidates.append(ExecutionCandidate(
            candidate_id=ep["name"],
            provider_name=ep["name"],
            model_id="kimi-k3",
            model_name="kimi-k3",
            layer=layer,
            layer_name=layer.name.lower(),
            task_type="chat",
            media_type="text",
            supported_tasks=["chat"],
            api_key_required=(ep["auth_env_var"] == "MOONSHOT_API_KEY"),
            api_key_available=bool(os.environ.get(ep["auth_env_var"], "")),
            expected_quality_score=0.92,
            expected_latency_ms=5000 if ep["layer"] == "public_api" else 2000,
            verified=(ep["layer"] == "public_api"),
            healthy=True,
            streaming=True,
            batching=True,
            metadata={"context_length": 1048576, "url": url,
                      "reasoning_effort": ["low", "high", "max"],
                      "capabilities": ["chat"]},
        ))
    return candidates


def build_vllm_docker_run(model: str = "moonshotai/Kimi-K3", hardware: str = "blackwell",
                          tensor_parallel: int = 8, expert_parallel: int = 16,
                          port: int = 8000, spec_decode: bool = False,
                          language_model_only: bool = False) -> Dict[str, Any]:
    """Return an official `docker run` command for a Kimi K3 vLLM server.

    Uses the official image (`vllm/vllm-openai:kimi-k3` or `-rocm`) with the
    verified launch flags from the official vLLM recipe.
    """
    plan = build_vllm_command(
        model=model, hardware=hardware, tensor_parallel=tensor_parallel,
        expert_parallel=expert_parallel, spec_decode=spec_decode,
        language_model_only=language_model_only,
    )
    env_args = " ".join(f"-e {k}={v}" for k, v in plan["env"].items())
    gpus = tensor_parallel * expert_parallel
    run = (
        f"docker run --gpus all --shm-size 64g "
        f"{env_args} -p {port}:8000 "
        f"--ipc=host {plan['image']} "
        + " ".join(plan["command"][2:])
    )
    return {
        "engine": "vllm",
        "image": plan["image"],
        "docker_run": run,
        "requires_gpus": gpus,
        "min_vram_gb": plan["min_vram_gb"],
        "env": plan["env"],
        "notes": plan["notes"],
    }


def build_sglang_docker_run(model: str = "moonshotai/Kimi-K3", hardware: str = "b200",
                            port: int = 30000, tp: Optional[int] = None,
                            dp: Optional[int] = None, nnodes: int = 1) -> Dict[str, Any]:
    """Return an official `docker run` command for a Kimi K3 SGLang server.

    Uses the official images (`lmsysorg/sglang:kimi-k3` family) with the
    verified flags from the official SGLang recipe.
    """
    plan = build_sglang_command(
        model=model, hardware=hardware, tp=tp, dp=dp, nnodes=nnodes,
    )
    env_args = " ".join(f"-e {k}={v}" for k, v in plan["env"].items())
    gpus = (tp or plan["parallelism"]["tensor_parallel"]) * (dp or plan["parallelism"]["data_parallel"])
    run = (
        f"docker run --gpus all --shm-size 64g "
        f"{env_args} -p {port}:30000 "
        f"--ipc=host {plan['image']} "
        + " ".join(plan["command"][2:])
    )
    return {
        "engine": "sglang",
        "image": plan["image"],
        "docker_run": run,
        "requires_gpus": gpus,
        "min_vram_gb": plan["min_vram_gb"],
        "env": plan["env"],
        "notes": plan["notes"],
    }


def register_kimi_k3_capability_graph(graph) -> int:
    """Add Kimi K3 nodes/edges to a CapabilityGraph (idempotent).

    The default CapabilityGraph already contains K3; this helper extends any
    dynamic/graph instance with the same canonical nodes and edges.
    """
    from .capability_graph import EdgeType, NodeType

    added = 0
    providers = {
        "kimi_k3_cloud": ("Kimi K3 Cloud API", {"tier": "paid", "type": "text", "context_length": 1048576}),
        "kimi_k3_vllm": ("Kimi K3 vLLM", {"tier": "paid", "type": "text", "runtime": "vllm", "context_length": 1048576}),
        "kimi_k3_sglang": ("Kimi K3 SGLang", {"tier": "paid", "type": "text", "runtime": "sglang", "context_length": 1048576}),
    }
    for pid, (name, attrs) in providers.items():
        if graph.get_node(pid) is None:
            graph.add_node(pid, NodeType.PROVIDER, name, attrs)
            added += 1
    if graph.get_node("chat") is None:
        graph.add_node("chat", NodeType.CAPABILITY, "Chat / Text Reasoning")
        added += 1

    existing_edges = set()
    for edges in graph._edges.values():
        for e in edges:
            existing_edges.add((e.source_id, e.target_id, e.edge_type))
    for pid in providers:
        if (pid, "chat", EdgeType.SUPPORTS) not in existing_edges:
            graph.add_edge(pid, "chat", EdgeType.SUPPORTS)
            added += 1
    for src, tgt in (("kimi_k3_cloud", "kimi_k3_vllm"), ("kimi_k3_vllm", "kimi_k3_sglang")):
        if (src, tgt, EdgeType.FALLBACK_TO) not in existing_edges:
            graph.add_edge(src, tgt, EdgeType.FALLBACK_TO, weight=0.9)
            added += 1
    return added
