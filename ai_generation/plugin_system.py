"""
Plugin System Foundation — lifecycle management, MCP extensibility, versioning.

Based on ACOS Research: Plugin Ecosystem Research, Ch8 (Plugin Operating System)
Provides plugin registration, resolution, activation, deactivation, and uninstall.
Supports compute, runtime, workflow, and tool plugin types with MCP-based extensibility.

Plugin Lifecycle:
    Registered → Resolved → Installed → Active → Deactivated → Uninstalled
                  ↓
                Failed (if dependencies missing or security check fails)

Plugin Types:
    - tool: MCP-based tool integration (JSON-RPC)
    - runtime: Inference runtime adapter
    - compute: Hardware/compute backend
    - workflow: DAG workflow step
    - extension: General platform extension
"""
import hashlib
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class PluginType(str, Enum):
    TOOL = "tool"
    RUNTIME = "runtime"
    COMPUTE = "compute"
    WORKFLOW = "workflow"
    EXTENSION = "extension"


class PluginState(str, Enum):
    REGISTERED = "registered"
    RESOLVED = "resolved"
    INSTALLING = "installing"
    INSTALLED = "installed"
    ACTIVE = "active"
    DEACTIVATING = "deactivating"
    DEACTIVATED = "deactivated"
    UPDATING = "updating"
    ROLLING_BACK = "rolling_back"
    UNINSTALLING = "uninstalling"
    UNINSTALLED = "uninstalled"
    FAILED = "failed"


class SandboxLevel(str, Enum):
    NONE = "none"
    PROCESS = "process"
    CONTAINER = "container"
    WASM = "wasm"


@dataclass
class PluginMetadata:
    """Metadata for a registered plugin."""
    plugin_id: str = ""
    name: str = ""
    version: str = "1.0.0"
    author: str = ""
    description: str = ""
    plugin_type: PluginType = PluginType.TOOL
    license: str = ""
    homepage: str = ""
    repository: str = ""
    tags: List[str] = field(default_factory=list)
    min_platform_version: str = "1.0.0"
    created_at: str = ""
    updated_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "plugin_id": self.plugin_id,
            "name": self.name,
            "version": self.version,
            "author": self.author,
            "description": self.description,
            "plugin_type": self.plugin_type.value,
            "license": self.license,
            "homepage": self.homepage,
            "repository": self.repository,
            "tags": self.tags,
            "min_platform_version": self.min_platform_version,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class PluginDependency:
    """A dependency requirement for a plugin."""
    plugin_id: str = ""
    version_range: str = ">=1.0.0"
    optional: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "plugin_id": self.plugin_id,
            "version_range": self.version_range,
            "optional": self.optional,
        }


@dataclass
class PluginPermission:
    """Security permissions for a plugin."""
    compute_access: bool = False
    gpu_access: bool = False
    network_access: bool = False
    file_system_access: bool = False
    model_loading: bool = False
    inference: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "compute_access": self.compute_access,
            "gpu_access": self.gpu_access,
            "network_access": self.network_access,
            "file_system_access": self.file_system_access,
            "model_loading": self.model_loading,
            "inference": self.inference,
        }


@dataclass
class PluginEntry:
    """A registered plugin in the system."""
    metadata: PluginMetadata = field(default_factory=PluginMetadata)
    state: PluginState = PluginState.REGISTERED
    dependencies: List[PluginDependency] = field(default_factory=list)
    permissions: PluginPermission = field(default_factory=PluginPermission)
    sandbox_level: SandboxLevel = SandboxLevel.PROCESS
    tools: List[Dict[str, Any]] = field(default_factory=list)
    config: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    activation_count: int = 0
    last_activated: str = ""
    signature: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            **self.metadata.to_dict(),
            "state": self.state.value,
            "dependencies": [d.to_dict() for d in self.dependencies],
            "permissions": self.permissions.to_dict(),
            "sandbox_level": self.sandbox_level.value,
            "tools_count": len(self.tools),
            "config_keys": list(self.config.keys()),
            "error": self.error,
            "activation_count": self.activation_count,
            "last_activated": self.last_activated,
            "has_signature": self.signature is not None,
        }


class PluginSystem:
    """
    Plugin lifecycle management and MCP extensibility layer.

    Manages plugin registration, dependency resolution, activation,
    deactivation, and uninstall with security sandboxing.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._plugins: Dict[str, PluginEntry] = {}
        self._tool_handlers: Dict[str, Callable] = {}
        self._event_listeners: Dict[str, List[Callable]] = {}
        self._init_builtins()

    def _init_builtins(self):
        """Register built-in platform plugins."""
        self.register_plugin(
            plugin_id="acos-core",
            name="ACOS Core Platform",
            version="1.0.0",
            plugin_type=PluginType.EXTENSION,
            description="Core platform functionality",
            author="Uncle Frappe AI",
        )
        self.register_plugin(
            plugin_id="mcp-tools",
            name="MCP Generation Tools",
            version="1.0.0",
            plugin_type=PluginType.TOOL,
            description="MCP-based generation tool interface",
            author="Uncle Frappe AI",
        )
        # Activate built-ins
        for pid in ["acos-core", "mcp-tools"]:
            if pid in self._plugins:
                self._plugins[pid].state = PluginState.ACTIVE

    def register_plugin(self, plugin_id: str, name: str = "",
                         version: str = "1.0.0",
                         plugin_type: PluginType = PluginType.TOOL,
                         description: str = "", author: str = "",
                         dependencies: Optional[List[Dict]] = None,
                         permissions: Optional[Dict] = None,
                         tools: Optional[List[Dict]] = None,
                         config: Optional[Dict] = None,
                         **kwargs) -> PluginEntry:
        """Register a new plugin."""
        now = datetime.now().isoformat()
        metadata = PluginMetadata(
            plugin_id=plugin_id, name=name or plugin_id,
            version=version, plugin_type=plugin_type,
            description=description, author=author,
            created_at=now, updated_at=now,
        )
        entry = PluginEntry(
            metadata=metadata,
            state=PluginState.REGISTERED,
            tools=tools or [],
            config=config or {},
        )
        if dependencies:
            entry.dependencies = [
                PluginDependency(**d) for d in dependencies
            ]
        if permissions:
            entry.permissions = PluginPermission(**permissions)

        self._plugins[plugin_id] = entry
        self._emit("registered", plugin_id)
        logger.info(f"Plugin registered: {plugin_id} v{version}")
        return entry

    def resolve_plugin(self, plugin_id: str) -> bool:
        """Resolve plugin dependencies. Returns True if resolved."""
        entry = self._plugins.get(plugin_id)
        if not entry:
            return False

        missing = []
        for dep in entry.dependencies:
            if dep.plugin_id not in self._plugins:
                if not dep.optional:
                    missing.append(dep.plugin_id)
            elif not self._version_compatible(
                self._plugins[dep.plugin_id].metadata.version,
                dep.version_range
            ):
                if not dep.optional:
                    missing.append(f"{dep.plugin_id}@{dep.version_range}")

        if missing:
            entry.state = PluginState.FAILED
            entry.error = f"Missing dependencies: {', '.join(missing)}"
            self._emit("failed", plugin_id, error=entry.error)
            return False

        entry.state = PluginState.RESOLVED
        self._emit("resolved", plugin_id)
        return True

    def install_plugin(self, plugin_id: str) -> bool:
        """Install a plugin (resolve + mark installed)."""
        entry = self._plugins.get(plugin_id)
        if not entry:
            return False

        if entry.state == PluginState.REGISTERED:
            if not self.resolve_plugin(plugin_id):
                return False

        entry.state = PluginState.INSTALLED
        self._emit("installed", plugin_id)
        logger.info(f"Plugin installed: {plugin_id}")
        return True

    def activate_plugin(self, plugin_id: str) -> bool:
        """Activate a plugin."""
        entry = self._plugins.get(plugin_id)
        if not entry:
            return False

        if entry.state not in (PluginState.INSTALLED, PluginState.DEACTIVATED):
            if entry.state != PluginState.ACTIVE:
                logger.warning(f"Cannot activate {plugin_id}: state={entry.state.value}")
                return False

        # Security check
        if not self._check_permissions(entry):
            entry.state = PluginState.FAILED
            entry.error = "Security check failed"
            self._emit("failed", plugin_id, error="Security check failed")
            return False

        entry.state = PluginState.ACTIVE
        entry.activation_count += 1
        entry.last_activated = datetime.now().isoformat()
        self._emit("activated", plugin_id)
        logger.info(f"Plugin activated: {plugin_id}")
        return True

    def deactivate_plugin(self, plugin_id: str) -> bool:
        """Deactivate a plugin."""
        entry = self._plugins.get(plugin_id)
        if not entry or entry.state != PluginState.ACTIVE:
            return False

        # Check if other active plugins depend on this one
        for other in self._plugins.values():
            if other.state == PluginState.ACTIVE:
                for dep in other.dependencies:
                    if dep.plugin_id == plugin_id and not dep.optional:
                        logger.warning(f"Cannot deactivate {plugin_id}: depended on by {other.metadata.plugin_id}")
                        return False

        entry.state = PluginState.DEACTIVATED
        self._emit("deactivated", plugin_id)
        logger.info(f"Plugin deactivated: {plugin_id}")
        return True

    def uninstall_plugin(self, plugin_id: str) -> bool:
        """Uninstall a plugin."""
        entry = self._plugins.get(plugin_id)
        if not entry:
            return False

        if entry.state == PluginState.ACTIVE:
            if not self.deactivate_plugin(plugin_id):
                return False

        entry.state = PluginState.UNINSTALLED
        self._emit("uninstalled", plugin_id)
        logger.info(f"Plugin uninstalled: {plugin_id}")
        return True

    def list_plugins(self, plugin_type: Optional[PluginType] = None,
                     state: Optional[PluginState] = None) -> List[Dict[str, Any]]:
        """List registered plugins with optional filtering."""
        plugins = list(self._plugins.values())
        if plugin_type:
            plugins = [p for p in plugins if p.metadata.plugin_type == plugin_type]
        if state:
            plugins = [p for p in plugins if p.state == state]
        return [p.to_dict() for p in plugins]

    def get_plugin(self, plugin_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific plugin."""
        entry = self._plugins.get(plugin_id)
        return entry.to_dict() if entry else None

    def register_tool(self, plugin_id: str, tool_name: str,
                       handler: Callable, description: str = "",
                       input_schema: Optional[Dict] = None):
        """Register an MCP tool handler from a plugin."""
        entry = self._plugins.get(plugin_id)
        if not entry:
            return

        tool_def = {
            "name": tool_name,
            "description": description,
            "inputSchema": input_schema or {"type": "object", "properties": {}},
            "plugin_id": plugin_id,
        }
        entry.tools.append(tool_def)
        self._tool_handlers[tool_name] = handler

    def get_tool_handler(self, tool_name: str) -> Optional[Callable]:
        """Get a registered tool handler."""
        return self._tool_handlers.get(tool_name)

    def list_tools(self) -> List[Dict[str, Any]]:
        """List all registered plugin tools."""
        tools = []
        for entry in self._plugins.values():
            for tool in entry.tools:
                tools.append({**tool, "active": entry.state == PluginState.ACTIVE})
        return tools

    def on(self, event: str, callback: Callable):
        """Register an event listener."""
        if event not in self._event_listeners:
            self._event_listeners[event] = []
        self._event_listeners[event].append(callback)

    def _emit(self, event: str, plugin_id: str, **kwargs):
        """Emit a plugin lifecycle event."""
        for listener in self._event_listeners.get(event, []):
            try:
                listener(plugin_id, **kwargs)
            except Exception as e:
                logger.warning(f"Event listener error: {e}")

    def _check_permissions(self, entry: PluginEntry) -> bool:
        """Check plugin permissions against security policy."""
        security_level = self.config.get("security_level", "production")
        if security_level == "development":
            return True

        perms = entry.permissions
        if perms.compute_access and not self.config.get("allow_compute_plugins", False):
            return False
        if perms.gpu_access and not self.config.get("allow_gpu_plugins", False):
            return False
        return True

    def _version_compatible(self, actual: str, required_range: str) -> bool:
        """Simple semver compatibility check."""
        if required_range.startswith(">="):
            required = required_range[2:]
            return self._parse_version(actual) >= self._parse_version(required)
        elif required_range.startswith("=="):
            required = required_range[2:]
            return actual == required
        return True

    @staticmethod
    def _parse_version(version: str) -> tuple:
        """Parse semver string to comparable tuple."""
        parts = version.split(".")
        return tuple(int(p) for p in parts[:3])

    def get_stats(self) -> Dict[str, Any]:
        """Get plugin system statistics."""
        by_type = {}
        by_state = {}
        for entry in self._plugins.values():
            t = entry.metadata.plugin_type.value
            s = entry.state.value
            by_type[t] = by_type.get(t, 0) + 1
            by_state[s] = by_state.get(s, 0) + 1

        return {
            "total_plugins": len(self._plugins),
            "by_type": by_type,
            "by_state": by_state,
            "tools_registered": len(self._tool_handlers),
            "events_supported": list(self._event_listeners.keys()),
        }
