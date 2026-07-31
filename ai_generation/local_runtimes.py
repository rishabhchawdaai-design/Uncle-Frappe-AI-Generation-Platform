"""
Local Runtime Integrations — vLLM, llama.cpp, Ollama routing/profiling wrappers.

Based on ACOS Research: Runtime Capability Registry
Provides detection, routing, profiling, and fallback for local inference runtimes.

These are routing/profiling wrappers — they do NOT require the runtime to be installed.
They detect availability, route requests to the right API, and profile performance.
"""
import asyncio
import hashlib
import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, AsyncIterator, Dict, List, Optional

logger = logging.getLogger(__name__)




class RuntimeType(str, Enum):
    VLLM = "vllm"
    LLAMACPP = "llamacpp"
    OLLAMA = "ollama"
    DIFFUSERS = "diffusers"
    COMFYUI = "comfyui"
    SGLANG = "sglang"
    MLC_LLM = "mlc_llm"
    ONNX_RUNTIME = "onnx_runtime"
    HF_TGI = "hf_tgi"
    EXOLAB = "exolab"
    PETALS = "petals"
class RuntimeStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"
    UNKNOWN = "unknown"


class RuntimeCategory(str, Enum):
    LLM = "llm"
    DIFFUSION = "diffusion"
    MULTIMODAL = "multimodal"


@dataclass
class RuntimeProfile:
    runtime_id: str = ""
    runtime_type: RuntimeType = RuntimeType.VLLM
    status: RuntimeStatus = RuntimeStatus.UNKNOWN
    url: str = ""
    version: str = ""
    models: List[str] = field(default_factory=list)
    hardware: Dict[str, Any] = field(default_factory=dict)
    capabilities: Dict[str, bool] = field(default_factory=dict)
    limits: Dict[str, Any] = field(default_factory=dict)
    last_health_check: str = ""
    latency_ms: float = 0.0
    requests_served: int = 0
    avg_tokens_per_sec: float = 0.0
    uptime_secs: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "runtime_id": self.runtime_id,
            "runtime_type": self.runtime_type.value,
            "status": self.status.value,
            "url": self.url,
            "version": self.version,
            "model_count": len(self.models),
            "models": self.models[:20],
            "hardware": self.hardware,
            "capabilities": self.capabilities,
            "limits": self.limits,
            "last_health_check": self.last_health_check,
            "latency_ms": round(self.latency_ms, 2),
            "requests_served": self.requests_served,
            "avg_tokens_per_sec": round(self.avg_tokens_per_sec, 2),
            "uptime_secs": round(self.uptime_secs, 1),
        }


@dataclass
class RuntimeRequest:
    model: str = ""
    prompt: str = ""
    max_tokens: int = 512
    temperature: float = 0.7
    top_p: float = 0.9
    stream: bool = False
    stop: List[str] = field(default_factory=list)
    system_prompt: str = ""
    images: List[str] = field(default_factory=list)
    extra_params: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "model": self.model,
            "prompt": self.prompt[:200] + ("..." if len(self.prompt) > 200 else ""),
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "stream": self.stream,
        }


@dataclass
class RuntimeResponse:
    runtime: str = ""
    model: str = ""
    text: str = ""
    tokens_generated: int = 0
    prompt_tokens: int = 0
    total_tokens: int = 0
    latency_ms: float = 0.0
    tokens_per_sec: float = 0.0
    finish_reason: str = ""
    error: Optional[str] = None
    cached: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "runtime": self.runtime,
            "model": self.model,
            "text": self.text[:500] + ("..." if len(self.text) > 500 else ""),
            "tokens_generated": self.tokens_generated,
            "prompt_tokens": self.prompt_tokens,
            "total_tokens": self.total_tokens,
            "latency_ms": round(self.latency_ms, 2),
            "tokens_per_sec": round(self.tokens_per_sec, 2),
            "finish_reason": self.finish_reason,
            "error": self.error,
            "cached": self.cached,
        }


class RuntimeHealthChecker:
    """Checks availability of local runtimes via HTTP health endpoints."""

    DEFAULT_URLS = {
        RuntimeType.VLLM: "http://localhost:8000",
        RuntimeType.LLAMACPP: "http://localhost:8080",
        RuntimeType.OLLAMA: "http://localhost:11434",
        RuntimeType.DIFFUSERS: "http://localhost:9000",
        RuntimeType.COMFYUI: "http://localhost:8188",
        RuntimeType.SGLANG: "http://localhost:30000",
        RuntimeType.MLC_LLM: "http://localhost:8001",
        RuntimeType.ONNX_RUNTIME: "http://localhost:8002",
        RuntimeType.HF_TGI: "http://localhost:8081",
        RuntimeType.EXOLAB: "http://localhost:8082",
        RuntimeType.PETALS: "http://localhost:8083",
    }

    HEALTH_ENDPOINTS = {
        RuntimeType.VLLM: "/health",
        RuntimeType.LLAMACPP: "/health",
        RuntimeType.OLLAMA: "/",
        RuntimeType.DIFFUSERS: "/health",
        RuntimeType.COMFYUI: "/system_stats",
        RuntimeType.SGLANG: "/health",
        RuntimeType.MLC_LLM: "/health",
        RuntimeType.ONNX_RUNTIME: "/health",
        RuntimeType.HF_TGI: "/health",
        RuntimeType.EXOLAB: "/health",
        RuntimeType.PETALS: "/health",
    }

    MODELS_ENDPOINTS = {
        RuntimeType.VLLM: "/v1/models",
        RuntimeType.LLAMACPP: "/v1/models",
        RuntimeType.OLLAMA: "/api/tags",
        RuntimeType.DIFFUSERS: "/models",
        RuntimeType.COMFYUI: "/system/models",
        RuntimeType.SGLANG: "/v1/models",
        RuntimeType.MLC_LLM: "/v1/models",
        RuntimeType.ONNX_RUNTIME: "/v1/models",
        RuntimeType.HF_TGI: "/v1/models",
        RuntimeType.EXOLAB: "/v1/models",
        RuntimeType.PETALS: "/v1/models",
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._urls: Dict[RuntimeType, str] = {}
        self._health_cache: Dict[RuntimeType, RuntimeProfile] = {}
        self._health_cache_ttl: float = self.config.get("health_cache_ttl", 30.0)
        self._timeouts: Dict[RuntimeType, float] = {}

        for rt in RuntimeType:
            self._urls[rt] = self.config.get(
                f"{rt.value}_url", self.DEFAULT_URLS[rt]
            )
            self._timeouts[rt] = self.config.get(f"{rt.value}_timeout", 3.0)

    async def check_health(self, runtime_type: RuntimeType,
                            url: Optional[str] = None) -> RuntimeProfile:
        target_url = url or self._urls[runtime_type]
        profile = RuntimeProfile(
            runtime_type=runtime_type,
            url=target_url,
            last_health_check=datetime.now().isoformat(),
        )

        try:
            import aiohttp
            timeout = aiohttp.ClientTimeout(total=self._timeouts[runtime_type])
            async with aiohttp.ClientSession(timeout=timeout) as session:
                health_url = target_url + self.HEALTH_ENDPOINTS[runtime_type]
                start = time.time()
                async with session.get(health_url) as resp:
                    latency = (time.time() - start) * 1000
                    if resp.status == 200:
                        profile.status = RuntimeStatus.HEALTHY
                        profile.latency_ms = latency
                        profile.runtime_id = f"{runtime_type.value}-{hashlib.md5(target_url.encode()).hexdigest()[:8]}"
                        await self._fetch_models(session, runtime_type, target_url, profile)
                    else:
                        profile.status = RuntimeStatus.DEGRADED
                        profile.latency_ms = latency
        except ImportError:
            logger.warning("aiohttp not installed, using urllib fallback")
            profile = await self._check_health_urllib(runtime_type, target_url, profile)
        except Exception as e:
            profile.status = RuntimeStatus.UNAVAILABLE
            profile.error = str(e)
            logger.debug(f"Runtime {runtime_type.value} unavailable at {target_url}: {e}")

        self._health_cache[runtime_type] = profile
        return profile

    async def _check_health_urllib(self, runtime_type: RuntimeType,
                                     url: str, profile: RuntimeProfile) -> RuntimeProfile:
        """Fallback health check using urllib (no async)."""
        import urllib.request
        import urllib.error
        try:
            health_url = url + self.HEALTH_ENDPOINTS[runtime_type]
            start = time.time()
            req = urllib.request.Request(health_url, method="GET")
            resp = urllib.request.urlopen(req, timeout=self._timeouts[runtime_type])
            latency = (time.time() - start) * 1000
            if resp.status == 200:
                profile.status = RuntimeStatus.HEALTHY
                profile.latency_ms = latency
                profile.runtime_id = f"{runtime_type.value}-{hashlib.md5(url.encode()).hexdigest()[:8]}"
        except Exception as e:
            profile.status = RuntimeStatus.UNAVAILABLE
        return profile

    async def _fetch_models(self, session, runtime_type: RuntimeType,
                              base_url: str, profile: RuntimeProfile):
        """Fetch available models from a runtime."""
        try:
            models_url = base_url + self.MODELS_ENDPOINTS[runtime_type]
            async with session.get(models_url) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if runtime_type == RuntimeType.OLLAMA:
                        profile.models = [
                            m.get("name", "") for m in data.get("models", [])
                        ]
                    else:
                        profile.models = [
                            m.get("id", "") for m in data.get("data", [])
                        ]
        except Exception:
            pass

    async def check_all(self) -> Dict[RuntimeType, RuntimeProfile]:
        results = {}
        for rt in RuntimeType:
            results[rt] = await self.check_health(rt)
        return results


class RuntimeRouter:
    """Routes inference requests to the best available local runtime."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._health_checker = RuntimeHealthChecker(config)
        self._profiles: Dict[RuntimeType, RuntimeProfile] = {}
        self._request_log: List[Dict[str, Any]] = []
        self._max_log: int = self.config.get("max_log", 1000)

        # Custom URLs
        self._custom_urls: Dict[RuntimeType, str] = {}

    def set_url(self, runtime_type: RuntimeType, url: str):
        self._custom_urls[runtime_type] = url
        self._health_checker._urls[runtime_type] = url

    async def discover(self) -> Dict[RuntimeType, RuntimeProfile]:
        self._profiles = await self._health_checker.check_all()
        return self._profiles

    async def get_healthy_runtimes(self) -> List[RuntimeType]:
        if not self._profiles:
            await self.discover()
        return [rt for rt, p in self._profiles.items()
                if p.status == RuntimeStatus.HEALTHY]

    async def route_request(self, request: RuntimeRequest,
                             preferred: Optional[RuntimeType] = None) -> RuntimeResponse:
        if not self._profiles:
            await self.discover()

        if preferred and preferred in self._profiles:
            if self._profiles[preferred].status == RuntimeStatus.HEALTHY:
                return await self._execute_on_runtime(preferred, request)

        for rt in [RuntimeType.VLLM, RuntimeType.OLLAMA, RuntimeType.LLAMACPP]:
            if rt in self._profiles and self._profiles[rt].status == RuntimeStatus.HEALTHY:
                return await self._execute_on_runtime(rt, request)

        return RuntimeResponse(
            error="No healthy local runtime available",
            runtime="none",
        )

    async def _execute_on_runtime(self, runtime_type: RuntimeType,
                                    request: RuntimeRequest) -> RuntimeResponse:
        url = self._custom_urls.get(runtime_type) or self._health_checker._urls[runtime_type]
        start = time.time()

        try:
            import aiohttp
            timeout = aiohttp.ClientTimeout(total=60.0)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                if runtime_type == RuntimeType.OLLAMA:
                    payload = {
                        "model": request.model,
                        "prompt": request.prompt,
                        "stream": request.stream,
                        "options": {
                            "temperature": request.temperature,
                            "top_p": request.top_p,
                            "num_predict": request.max_tokens,
                        },
                    }
                    if request.system_prompt:
                        payload["system"] = request.system_prompt
                    endpoint = f"{url}/api/generate"
                else:
                    messages = []
                    if request.system_prompt:
                        messages.append({"role": "system", "content": request.system_prompt})
                    messages.append({"role": "user", "content": request.prompt})
                    payload = {
                        "model": request.model,
                        "messages": messages,
                        "max_tokens": request.max_tokens,
                        "temperature": request.temperature,
                        "top_p": request.top_p,
                        "stream": request.stream,
                    }
                    if request.stop:
                        payload["stop"] = request.stop
                    endpoint = f"{url}/v1/chat/completions"

                async with session.post(endpoint, json=payload) as resp:
                    latency = (time.time() - start) * 1000
                    if resp.status != 200:
                        error_text = await resp.text()
                        return RuntimeResponse(
                            runtime=runtime_type.value,
                            model=request.model,
                            latency_ms=latency,
                            error=f"HTTP {resp.status}: {error_text[:200]}",
                        )

                    data = await resp.json()

                    if runtime_type == RuntimeType.OLLAMA:
                        text = data.get("response", "")
                        tokens = data.get("eval_count", 0)
                        prompt_tokens = data.get("prompt_eval_count", 0)
                    else:
                        choice = data.get("choices", [{}])[0]
                        text = choice.get("message", {}).get("content", "")
                        usage = data.get("usage", {})
                        tokens = usage.get("completion_tokens", 0)
                        prompt_tokens = usage.get("prompt_tokens", 0)

                    tokens_per_sec = tokens / (latency / 1000) if latency > 0 else 0

                    response = RuntimeResponse(
                        runtime=runtime_type.value,
                        model=request.model,
                        text=text,
                        tokens_generated=tokens,
                        prompt_tokens=prompt_tokens,
                        total_tokens=tokens + prompt_tokens,
                        latency_ms=latency,
                        tokens_per_sec=tokens_per_sec,
                        finish_reason="stop",
                    )

                    self._log_request(runtime_type, request, response)
                    if runtime_type in self._profiles:
                        self._profiles[runtime_type].requests_served += 1
                    return response

        except ImportError:
            return RuntimeResponse(
                runtime=runtime_type.value,
                model=request.model,
                error="aiohttp not installed. Install with: pip install aiohttp",
            )
        except Exception as e:
            latency = (time.time() - start) * 1000
            return RuntimeResponse(
                runtime=runtime_type.value,
                model=request.model,
                latency_ms=latency,
                error=str(e),
            )

    def _log_request(self, runtime_type: RuntimeType,
                       request: RuntimeRequest, response: RuntimeResponse):
        entry = {
            "runtime": runtime_type.value,
            "model": request.model,
            "tokens": response.tokens_generated,
            "latency_ms": response.latency_ms,
            "tokens_per_sec": response.tokens_per_sec,
            "success": response.error is None,
            "timestamp": datetime.now().isoformat(),
        }
        self._request_log.append(entry)
        if len(self._request_log) > self._max_log:
            self._request_log = self._request_log[-self._max_log:]

    def get_stats(self) -> Dict[str, Any]:
        total = len(self._request_log)
        success = sum(1 for r in self._request_log if r["success"])
        avg_latency = (
            sum(r["latency_ms"] for r in self._request_log) / total
            if total > 0 else 0
        )
        avg_tps = (
            sum(r["tokens_per_sec"] for r in self._request_log) / total
            if total > 0 else 0
        )

        runtime_counts = {}
        for r in self._request_log:
            rt = r["runtime"]
            runtime_counts[rt] = runtime_counts.get(rt, 0) + 1

        return {
            "total_requests": total,
            "successful": success,
            "failed": total - success,
            "success_rate": 100.0 if total == 0 else round(success / total * 100, 1),
            "avg_latency_ms": round(avg_latency, 2),
            "avg_tokens_per_sec": round(avg_tps, 2),
            "requests_by_runtime": runtime_counts,
            "healthy_runtimes": [
                rt.value for rt, p in self._profiles.items()
                if p.status == RuntimeStatus.HEALTHY
            ],
        }

    def get_request_log(self, limit: int = 50) -> List[Dict[str, Any]]:
        return list(reversed(self._request_log[-limit:]))


class LocalRuntimeManager:
    """
    Unified manager for all local runtime integrations.

    Provides a single interface for:
    - vLLM: High-performance GPU inference server
    - llama.cpp: CPU/edge inference with GGUF models
    - Ollama: Easy local model management
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._router = RuntimeRouter(config)
        self._profiles: Dict[RuntimeType, RuntimeProfile] = {}
        self._runtime_configs: Dict[RuntimeType, Dict[str, Any]] = {}
        self._discovery_count: int = 0

    @property
    def router(self) -> RuntimeRouter:
        return self._router

    async def discover_runtimes(self) -> Dict[str, RuntimeProfile]:
        self._discovery_count += 1
        self._profiles = await self._router.discover()
        return self._profiles

    def get_healthy_count(self) -> int:
        return sum(
            1 for p in self._profiles.values()
            if p.status == RuntimeStatus.HEALTHY
        )

    def configure_runtime(self, runtime_type: RuntimeType, **kwargs):
        self._runtime_configs[runtime_type] = kwargs
        if "url" in kwargs:
            self._router.set_url(runtime_type, kwargs["url"])

    def configure_kimi_k3_runtime(self, runtime: RuntimeType, url: str,
                                  hardware: str = "blackwell",
                                  tensor_parallel: int = 8,
                                  expert_parallel: int = 16,
                                  pipeline_parallel: int = 1,
                                  spec_decode: bool = False) -> Dict[str, Any]:
        """Configure a Kimi K3 vLLM/SGLang runtime in the Runtime Registry.

        References the canonical Kimi K3 spec and launch builders from
        ``ai_generation.kimi_k3`` so K3 launch plans are exposed here without
        duplicating official recipes. vLLM accepts the official Blackwell /
        Hopper / AMD flag sets; SGLang accepts the official B200 / GB200 /
        H100 / H200 / B300 / MI350X / MI355X recipes.
        """
        from .kimi_k3 import (
            KIMI_K3_SPEC, build_sglang_command, build_vllm_command,
        )
        if runtime not in (RuntimeType.VLLM, RuntimeType.SGLANG):
            raise ValueError("Kimi K3 runtimes are vLLM (vllm) or SGLang (sglang)")
        self.configure_runtime(runtime, url=url)
        if runtime == RuntimeType.VLLM:
            launch = build_vllm_command(
                hardware=hardware, tensor_parallel=tensor_parallel,
                expert_parallel=expert_parallel,
                pipeline_parallel=pipeline_parallel, spec_decode=spec_decode,
            )
        else:
            launch = build_sglang_command(hardware=hardware, spec_decode=spec_decode)
        plan = {
            "model": KIMI_K3_SPEC["model"],
            "model_id": KIMI_K3_SPEC["model_id"],
            "context_length": KIMI_K3_SPEC["context_length"],
            "min_gpus": KIMI_K3_SPEC["deployment"]["min_gpus"],
            "min_vram_gb": KIMI_K3_SPEC["deployment"]["min_vram_gb"],
            "launch": launch,
        }
        self._runtime_configs[runtime]["kimi_k3"] = plan
        return plan

    def get_kimi_k3_plans(self) -> Dict[str, Dict[str, Any]]:
        """Return configured Kimi K3 launch plans from the Runtime Registry."""
        plans = {}
        for rt in (RuntimeType.VLLM, RuntimeType.SGLANG):
            plan = self._runtime_configs.get(rt, {}).get("kimi_k3")
            if plan:
                plans[rt.value] = plan
        return plans

    def get_runtime_profile(self, runtime_type: RuntimeType) -> Optional[Dict[str, Any]]:
        profile = self._profiles.get(runtime_type)
        return profile.to_dict() if profile else None

    async def generate(self, model: str, prompt: str, runtime: Optional[RuntimeType] = None,
                        **kwargs) -> RuntimeResponse:
        request = RuntimeRequest(
            model=model, prompt=prompt,
            max_tokens=kwargs.get("max_tokens", 512),
            temperature=kwargs.get("temperature", 0.7),
            top_p=kwargs.get("top_p", 0.9),
            stream=kwargs.get("stream", False),
            stop=kwargs.get("stop", []),
            system_prompt=kwargs.get("system_prompt", ""),
        )
        return await self._router.route_request(request, preferred=runtime)

    async def list_all_models(self) -> Dict[str, List[str]]:
        if not self._profiles:
            await self.discover_runtimes()
        return {
            rt.value: profile.models
            for rt, profile in self._profiles.items()
            if profile.status == RuntimeStatus.HEALTHY
        }

    def get_stats(self) -> Dict[str, Any]:
        router_stats = self._router.get_stats()
        return {
            **router_stats,
            "discovery_count": self._discovery_count,
            "configured_runtimes": [rt.value for rt in self._runtime_configs],
            "runtime_profiles": {
                rt.value: profile.to_dict()
                for rt, profile in self._profiles.items()
            },
        }
