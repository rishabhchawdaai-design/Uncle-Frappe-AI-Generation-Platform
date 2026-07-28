---
type: overview
module: plugin-system
status: active
tags: [plugin, overview]
---

# Plugin System Overview

## Plugin Architecture

```mermaid
graph TB
    subgraph "Plugin System"
        Registry["Plugin Registry"]
        Loader["Plugin Loader"]
        HotReload["Hot Reloader"]
        Marketplace["Marketplace"]
        Signer["Crypto Signer"]
    end
    
    subgraph "Plugin Types"
        Provider["Provider Plugins"]
        Backend["Backend Plugins"]
        Quality["Quality Plugins"]
        Workflow["Workflow Plugins"]
    end
    
    Registry --> Loader
    Loader --> HotReload
    Marketplace --> Registry
    Signer --> Registry
    Provider --> Loader
    Backend --> Loader
    Quality --> Loader
    Workflow --> Loader
```

## Plugin Components

| Component | Module | Purpose |
|-----------|--------|---------|
| PluginSystem | `plugin_system.py` | Core plugin management |
| PluginExtensions | `plugin_extensions.py` | Marketplace, hot-reload, signing |

## Plugin Lifecycle

1. **Discovery** — Find available plugins
2. **Installation** — Install plugin files
3. **Loading** — Load plugin into runtime
4. **Registration** — Register plugin capabilities
5. **Execution** — Execute plugin functionality
6. **Hot Reload** — Reload on changes
7. **Verification** — Verify plugin integrity

## Related

- [[Architecture Overview]]
- [[Skills Overview]]
- [[MCP Ecosystem Overview]]
