---
type: research
model: "Kimi K3"
vendor: "Moonshot AI"
status: integrated
tags: [research, model, kimi-k3, moe, reasoning, multimodal]
source: "Official Moonshot AI documentation"
verified: "2026-07-31"
---

# Kimi K3 — Verified Official Research

Kimi K3 is an open-weight multimodal reasoning model from Moonshot AI. This
page records only **officially supported** facts from:
[Hugging Face model card](https://huggingface.co/moonshotai/Kimi-K3),
[MoonshotAI/Kimi-K3 GitHub](https://github.com/MoonshotAI/Kimi-K3),
[platform.kimi.ai docs](https://platform.kimi.ai/docs),
[official vLLM recipe](https://recipes.vllm.ai/moonshotai/Kimi-K3), and
[official SGLang recipe](https://docs.sglang.io/cookbook/autoregressive/Moonshotai/Kimi-K3).

## Architecture

- **Model type**: `kimi_k3` — `KimiK3ForConditionalGeneration`, multimodal (text + image)
- **MoE**: Latent MoE — 2.8T total params, 104B active; 93 layers; hidden 7168
- **Experts**: 896 total (2 shared), 16 experts selected per token
- **Attention**: 69 KDA + 24 Gated MLA
- **Vision encoder**: MoonViT-V2 (401M)
- **Weights**: MXFP4 quantization-aware, MXFP8 activations, BF16 compute
- **Tokenizer**: TikToken (YToken), vocab 163,840; pad 163,839; bos 163,584; eos 163,586; image token 163,605
- **Context**: 1,048,576 tokens

## Thinking

- Thinking is **always on**
- `reasoning_effort`: `low | high | max` (default `max`)
- Returns `reasoning_content`
- Multi-turn preserved thinking: echo `reasoning_content` + `tool_calls` back verbatim on assistant messages

## Officially Supported Execution Paths

| Path | Support | Details |
|------|---------|---------|
| Cloud API | ✅ | `https://api.moonshot.ai/v1` — OpenAI-compatible `/chat/completions`, model `kimi-k3`, Bearer `MOONSHOT_API_KEY`, 1M context, automatic caching |
| vLLM | ✅ | `vllm/vllm-openai:kimi-k3` (CUDA 13); `vllm/vllm-openai-rocm:kimi-k3` (ROCm); min vLLM 0.27.0 |
| SGLang | ✅ | `lmsysorg/sglang:kimi-k3`, `:kimi-k3-cu12`, ROCm image; port 30000 |
| TokenSpeed | ✅ | `lightseekorg/tokenspeed` per official model card deployment list |

## Officially Unsupported Runtimes

TensorRT-LLM, DeepSpeed, llama.cpp, Ollama, Hugging Face Inference/TGI,
Hugging Face Endpoints, and GGUF have **no official Moonshot AI support** and
are recorded as unsupported — never emulated.

## Parallelism (official)

- vLLM: TP8 (8 GPUs), TEP16, TP8×PP2 (16), multi-node DEP (16+); H100 needs 32 GPUs; min ~1680 GB VRAM (MXFP4)
- SGLang: B200 2×8, GB200 4×4, H100 4×8, B300 1×8, H200 2×8, MI350X/MI355X 1×8; balanced TP16/DCP16 (B200/GB200), TP8/DCP8 (B300/GB300), TP8 ROCm/AITER (MI35x)
- Speculative decoding: DSpark via `Inferact/Kimi-K3-DSpark` (num_speculative_tokens 7)

## Related

- [[Kimi K3|Model Page]]
- [[Kimi K3 Runtimes]]
- [[05-SDK/SDK Overview|SDK]]
- [[06-MCP-Ecosystem/MCP Ecosystem Overview|MCP Tools]]
- [[03-Execution-Engine/Execution Engine Overview|Execution Engine]]
