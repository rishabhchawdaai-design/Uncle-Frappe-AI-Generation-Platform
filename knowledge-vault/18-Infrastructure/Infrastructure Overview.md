---
type: overview
module: infrastructure
status: active
tags: [infrastructure, overview]
---

# Infrastructure Overview

## Current Infrastructure

| Component | Status | Notes |
|-----------|--------|-------|
| Local GPU | ✅ Available | User-owned |
| Local CPU | ✅ Available | User-owned |
| Cloud GPU | ⚠️ BLOCKED | Requires credentials |
| Kubernetes | ⚠️ BLOCKED | Requires cluster |
| Docker | ⚠️ BLOCKED | Requires Docker daemon |
| Distributed Workers | ⚠️ BLOCKED | Requires Ray |

## Hardware Discovery

The platform automatically discovers:
- GPU devices (NVIDIA, AMD)
- CPU capabilities
- Available memory
- Disk space
- Local runtimes

## Blocked Infrastructure

| Capability | Blocker | Unblocked By |
|------------|---------|--------------|
| K8s Orchestration | No cluster | User provides cluster |
| Cloud Instances | No credentials | User provides API keys |
| Distributed AI | No Ray | Install Ray |
| Storage | No databases | Install PostgreSQL/Redis |

## Related

- [[Architecture Overview]]
- [[Runtime Registry Overview]]
- [[Capability Registry Overview]]
