---
type: model
model: "Kimi K3"
vendor: "Moonshot AI"
status: verified
tasks: [chat, vision]
tags: [model, kimi-k3, moe, reasoning]
---

# Kimi K3

Moonshot AI's open-weight multimodal reasoning model integrated as an
execution runtime.

## Key Facts

- **Context length**: 1,048,576 tokens
- **Architecture**: Latent MoE — 2.8T total / 104B active, 93 layers, 896 experts (16 active + 2 shared)
- **Quantization**: MXFP4 weights / MXFP8 activations (quantization-aware), BF16
- **Multimodal**: text + image (MoonViT-V2, 401M)
- **Thinking**: always on; `reasoning_effort` low/high/max; returns `reasoning_content`
- **License**: Kimi K3 License (open weights; API use subject to Moonshot AI ToS)

## Execution Paths

| Endpoint | Layer | API | Notes |
|----------|-------|-----|-------|
| `kimi_k3_cloud` | PUBLIC_API | OpenAI-compatible chat | `MOONSHOT_API_KEY` required |
| `kimi_k3_vllm` | USER_CONFIGURED | OpenAI-compatible chat | `vllm/vllm-openai:kimi-k3` |
| `kimi_k3_sglang` | USER_CONFIGURED | OpenAI-compatible chat | `lmsysorg/sglang:kimi-k3` |

## SDK

```python
ai = UncleFrappeAI()
result = await ai.chat("Explain MoE", reasoning_effort="high")
print(result["text"], result["reasoning"])
```

## Related

- [[24-Research/Kimi K3|Research]]
- [[Kimi K3 Runtimes]]
- [[Model Registry Overview]]
