---
type: overview
module: model-registry
status: active
tags: [models, registry, overview]
---

# Model Registry Overview

## Model Categories

### Image Generation Models
| Model | Provider | Type | Status |
|-------|----------|------|--------|
| SDXL | Stability | Diffusion | ✅ |
| FLUX | Black Forest Labs | Diffusion | ✅ |
| Stable Diffusion 3 | Stability | Diffusion | ✅ |

### Video Generation Models
| Model | Provider | Type | Status |
|-------|----------|------|--------|
| Stable Video Diffusion | Stability | Video | ✅ |
| SVD | Replicate | Video | ✅ |

### Audio Models
| Model | Provider | Type | Status |
|-------|----------|------|--------|
| MusicGen | Meta | Music | ✅ |
| AudioGen | Meta | SFX | ✅ |
| Bark | Suno | Speech | ✅ |
| XTTS | Coqui | Voice Cloning | ✅ |

### OCR Models
| Model | Provider | Type | Status |
|-------|----------|------|--------|
| Marker | Open Source | Document Parsing | ✅ |
| Nougat | Meta | Document Parsing | ✅ |
| Docling | IBM | Document Parsing | ✅ |

### 3D Models
| Model | Provider | Type | Status |
|-------|----------|------|--------|
| Splatfacto | nerfstudio | Gaussian Splatting | ✅ |
| NeRF | nerfstudio | 3D Reconstruction | ✅ |

## Model Capabilities

Each model is registered with:
- Supported tasks (image, video, audio, 3D)
- License type (open, proprietary)
- Resource requirements (GPU, CPU)
- Provider availability
- Benchmark scores

## Related

- [[Provider Registry Overview]]
- [[Capability Registry Overview]]
- [[Benchmark Overview]]
