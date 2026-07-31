---
module: "video_editing"
type: module-doc
status: active
owner: ""
lines: 921
classes: 7
functions: 0
tags: [module, documentation]
generated: "2026-07-31"
---

# video_editing

> Video Editing Layer — trim, concat, transitions, frame interpolation, upscaling.
Uses ffmpeg for editing, RIFE for interpolation, Real-ESRGAN for upscaling.
All operations gracefully degrade when depe

## Overview

- **File**: `ai_generation/video_editing.py`
- **Lines**: 921
- **Classes**: 7
- **Public Functions**: 0

## Classes

- `{{VideoEditOperation}}`
- `{{VideoEditStatus}}`
- `{{InterpolationModel}}`
- `{{UpscaleModel}}`
- `{{VideoEditResult}}`
- `{{VideoEditProfile}}`
- `{{VideoEditingEngine}}`

## Integration

- Part of the [[Architecture Overview|Unified AI Generation Platform]]
- Exposed via [[05-SDK/SDK Overview|SDK]] and [[06-MCP-Ecosystem/MCP Ecosystem Overview|MCP Tools]]
- Verified in [[02-Capability-Registry/Capability Registry Overview|Capability Registry]]

## Related

- [[Architecture Overview]]
- [[Capability Registry Overview]]
