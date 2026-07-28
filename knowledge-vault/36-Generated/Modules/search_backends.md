---
module: "search_backends"
type: module-doc
status: active
owner: ""
lines: 360
classes: 10
functions: 0
tags: [module, documentation]
generated: "2026-07-28"
---

# search_backends

> Search Backends — Meilisearch, OpenSearch, Vector/Semantic Search.
Extends SearchManager with external search backends and semantic search.
All backends gracefully degrade when services are unavailabl

## Overview

- **File**: `ai_generation/search_backends.py`
- **Lines**: 360
- **Classes**: 10
- **Public Functions**: 0

## Classes

- `{{ExternalSearchBackend}}`
- `{{SemanticSearchModel}}`
- `{{VectorDBStatus}}`
- `{{BackendProfile}}`
- `{{SearchResult}}`
- `{{SearchResponse}}`
- `{{MeilisearchBackend}}`
- `{{OpenSearchBackend}}`
- `{{VectorSearchBackend}}`
- `{{SearchBackendManager}}`

## Integration

- Part of the [[Architecture Overview|Unified AI Generation Platform]]
- Exposed via [[05-SDK/SDK Overview|SDK]] and [[06-MCP-Ecosystem/MCP Ecosystem Overview|MCP Tools]]
- Verified in [[02-Capability-Registry/Capability Registry Overview|Capability Registry]]

## Related

- [[Architecture Overview]]
- [[Capability Registry Overview]]
