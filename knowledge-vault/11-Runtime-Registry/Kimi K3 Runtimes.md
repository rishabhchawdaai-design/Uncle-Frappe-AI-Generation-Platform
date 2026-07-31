---
type: runtime
runtime: "Kimi K3"
vendor: "Moonshot AI"
status: verified
tags: [runtime, kimi-k3, vllm, sglang, cloud]
---

# Kimi K3 Runtimes

## Official Images

| Engine | Image | Notes |
|--------|-------|-------|
| vLLM (NVIDIA) | `vllm/vllm-openai:kimi-k3` | CUDA 13, r580+ driver; min vLLM 0.27.0 |
| vLLM (AMD) | `vllm/vllm-openai-rocm:kimi-k3` | ROCm |
| SGLang | `lmsysorg/sglang:kimi-k3` / `:kimi-k3-cu12` | port 30000 |
| SGLang (ROCm) | `lmsysorg/sglang-rocm:rocm720-mi35x-k3-20260727` | MI350X/MI355X |

## vLLM Launch Flags (official)

- Base: `--trust-remote-code --moe-backend auto --gpu-memory-utilization 0.95`
- Parsers: `--tool-call-parser kimi_k3 --enable-auto-tool-choice --reasoning-parser kimi_k3`
- Blackwell: `--load-format fastsafetensors --max-model-len 1048576 --kv-cache-dtype fp8 --attention-config '{"use_prefill_query_quantization":true}' --enable-prefix-caching`
- Hopper: `--moe-backend marlin --attention-backend FLASHMLA --max-model-len 32768 --max-num-seqs 5`
- AMD: `--mm-encoder-tp-mode data --max-num-seqs 128 --max-num-batched-tokens 4096`
- Speculative decoding: DSpark via `Inferact/Kimi-K3-DSpark`, `num_speculative_tokens=7`

## SGLang Launch Flags (official)

`--reasoning-parser kimi_k3 --tool-call-parser kimi_k3 --kv-cache-dtype fp8_e4m3 --moe-a2a-backend megamoe --moe-runner-backend deep_gemm --host 0.0.0.0 --port 30000`

- PD disaggregation: `--pp-size 8 --tp-size 1` (long-context prefill)
- HiCache hierarchical KV caching; Deep PP; DSpark spec-decode

## Kubernetes

Single-node Deployment manifests are generated from the official images and
verified flags via `build_vllm_k8s_yaml()` / `build_sglang_k8s_yaml()`
(`ai_generation/kimi_k3.py`). No official Moonshot K8s manifest exists;
multi-node parallelism requires a StatefulSet plus `--dist-init-addr`.

## Platform Integration

- **Event Bus**: every request publishes `kimi_k3.request.complete`,
  `kimi_k3.provider.failed`, and `kimi_k3.request.failed` domain events
  (via `KimiK3Manager._publish_event`, wired to the SDK's shared bus).
- **Observability**: `kimi_k3.requests.total/success/failed` counters and
  `kimi_k3.latency_ms` histogram (monotonic `perf_counter` timing).
- **Negotiation**: `chat_negotiated()` selects the optimal path via the
  Negotiation Engine using `kimi_k3_candidates()`.
- **Local Runtime Registry**: `LocalRuntimeManager.configure_kimi_k3_runtime()`
  registers K3 vLLM/SGLang launch plans (official flags + hardware facts)
  into the Runtime Registry.
- **Supervision**: `register_kimi_k3_supervisor_workers()` registers one
  MONITOR worker per K3 endpoint (fail-fast on unhealthy / not serving kimi-k3).
- **Regression Detection**: `record_kimi_k3_regression()` feeds benchmark
  runs into the Regression Detector (latency / quality / error-rate baselines).
- **Decision Ledger**: every completion records a chat decision entry.

## Health Checks

- vLLM: `GET /v1/models`
- SGLang: `GET /v1/models`

## Related

- [[24-Research/Kimi K3|Research]]
- [[10-Models/Kimi K3|Model]]
- [[Runtime Registry Overview]]
