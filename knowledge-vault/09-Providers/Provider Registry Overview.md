---
type: overview
module: provider-registry
status: active
tags: [provider, registry, index]
---

# Provider Registry

## Provider Categories

### Image Generation
- Pollinations (Free)
- Craiyon (Free)
- HuggingFace (Free/Paid)
- Together AI (Paid)
- Stability AI (Paid)
- Replicate (Paid)
- Fal AI (Paid)
- SiliconFlow (Paid)
- DeepAI (Paid)

### Video Generation
- Replicate (Paid)
- Fal AI (Paid)
- Runway (Paid)

### Audio Generation
- Bark (Open Source)
- VALL-E-X (Open Source)
- MusicGen (Open Source)
- AudioGen (Open Source)

### Local Runtimes
- ComfyUI
- Stable Diffusion WebUI
- Ollama
- llama.cpp

## Provider Health

```dataview
TABLE healthy, latency_ms, consecutive_failures
FROM "36-Generated"
WHERE type = "provider-health"
SORT healthy DESC
```

## Related

- [[Architecture Overview]]
- [[Capability Registry Overview]]
- [[Execution Engine Overview]]
