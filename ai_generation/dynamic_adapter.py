"""
Dynamic Adapter System — auto-generates provider adapters from schemas.
Instead of handwritten adapters, parse OpenAPI/JSON schemas and compile execution adapters.
"""
import hashlib
import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class AdapterSchema:
    provider: str = ""
    schema_type: str = ""  # openapi, json_schema, mcp_tools, custom
    schema_data: Dict[str, Any] = field(default_factory=dict)
    endpoints: List[Dict[str, Any]] = field(default_factory=list)
    auth_config: Dict[str, Any] = field(default_factory=dict)
    parsed_at: str = ""

    def __post_init__(self):
        if not self.parsed_at:
            self.parsed_at = datetime.utcnow().isoformat()

    def schema_hash(self) -> str:
        return hashlib.md5(json.dumps(self.schema_data, sort_keys=True).encode()).hexdigest()[:12]


@dataclass
class CompiledAdapter:
    provider: str = ""
    adapter_id: str = ""
    schema_hash: str = ""
    endpoint_handlers: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    auth_handler: Dict[str, Any] = field(default_factory=dict)
    compiled_at: str = ""
    version: int = 1
    is_valid: bool = True
    errors: List[str] = field(default_factory=list)

    def __post_init__(self):
        if not self.compiled_at:
            self.compiled_at = datetime.utcnow().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "provider": self.provider, "adapter_id": self.adapter_id,
            "schema_hash": self.schema_hash, "handlers": list(self.endpoint_handlers.keys()),
            "auth_type": self.auth_handler.get("type", "none"),
            "compiled_at": self.compiled_at, "version": self.version,
            "is_valid": self.is_valid, "errors": self.errors,
        }


class SchemaParser:
    """Parses various schema formats into intermediate representation."""

    def parse_openapi(self, schema_data: Dict[str, Any]) -> AdapterSchema:
        adapter = AdapterSchema(schema_type="openapi", schema_data=schema_data)
        paths = schema_data.get("paths", {})
        for path, methods in paths.items():
            for method, details in methods.items():
                if method.lower() in ("get", "post", "put", "delete", "patch"):
                    adapter.endpoints.append({
                        "path": path, "method": method.upper(),
                        "operation_id": details.get("operationId", ""),
                        "summary": details.get("summary", ""),
                        "parameters": details.get("parameters", []),
                        "request_body": details.get("requestBody", {}),
                        "responses": details.get("responses", {}),
                    })
        sec = schema_data.get("securityDefinitions", schema_data.get("components", {}).get("securitySchemes", {}))
        if sec:
            adapter.auth_config = {"type": "openapi_security", "schemes": sec}
        return adapter

    def parse_json_schema(self, schema_data: Dict[str, Any], provider: str = "") -> AdapterSchema:
        adapter = AdapterSchema(provider=provider, schema_type="json_schema", schema_data=schema_data)
        props = schema_data.get("properties", {})
        for prop_name, prop_def in props.items():
            adapter.endpoints.append({
                "name": prop_name, "type": prop_def.get("type", "string"),
                "description": prop_def.get("description", ""),
                "required": prop_name in schema_data.get("required", []),
            })
        return adapter

    def parse_mcp_tools(self, tools_data: Dict[str, Any], provider: str = "") -> AdapterSchema:
        adapter = AdapterSchema(provider=provider, schema_type="mcp_tools", schema_data=tools_data)
        for tool_name, tool_def in tools_data.items():
            adapter.endpoints.append({
                "name": tool_name,
                "input_schema": tool_def.get("inputSchema", {}),
                "description": tool_def.get("description", ""),
            })
        return adapter

    def parse_custom(self, schema_data: Dict[str, Any], provider: str = "") -> AdapterSchema:
        adapter = AdapterSchema(provider=provider, schema_type="custom", schema_data=schema_data)
        for key, val in schema_data.items():
            if isinstance(val, dict):
                adapter.endpoints.append({"name": key, "details": val})
        return adapter


class AdapterCompiler:
    """Compiles parsed schemas into executable adapters."""

    def compile(self, schema: AdapterSchema) -> CompiledAdapter:
        adapter = CompiledAdapter(
            provider=schema.provider,
            schema_hash=schema.schema_hash(),
        )

        for ep in schema.endpoints:
            handler = self._compile_endpoint(ep, schema)
            name = ep.get("operation_id") or ep.get("name") or ep.get("path", "unknown")
            adapter.endpoint_handlers[name] = handler

        if schema.auth_config:
            adapter.auth_handler = self._compile_auth(schema.auth_config)

        adapter.adapter_id = f"{schema.provider}_{adapter.schema_hash}"
        return adapter

    def _compile_endpoint(self, endpoint: Dict[str, Any], schema: AdapterSchema) -> Dict[str, Any]:
        handler = {
            "method": endpoint.get("method", endpoint.get("type", "POST")),
            "path": endpoint.get("path", endpoint.get("name", "")),
            "description": endpoint.get("summary", endpoint.get("description", "")),
            "parameters": endpoint.get("parameters", []),
            "input_schema": endpoint.get("input_schema", {}),
            "compiled_at": datetime.utcnow().isoformat(),
        }
        return handler

    def _compile_auth(self, auth_config: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "type": auth_config.get("type", "api_key"),
            "schemes": auth_config.get("schemes", {}),
            "env_var": auth_config.get("env_var", ""),
        }


class DynamicAdapterManager:
    """Manages the lifecycle of dynamic adapters: parse → compile → cache → execute → refresh."""

    def __init__(self):
        self._schemas: Dict[str, AdapterSchema] = {}
        self._adapters: Dict[str, CompiledAdapter] = {}
        self._handlers: Dict[str, Any] = {}
        self._parser = SchemaParser()
        self._compiler = AdapterCompiler()

    def register_schema(self, provider: str, schema_data: Dict[str, Any], schema_type: str = "custom") -> CompiledAdapter:
        parse_fn = {
            "openapi": self._parser.parse_openapi,
            "json_schema": self._parser.parse_json_schema,
            "mcp_tools": self._parser.parse_mcp_tools,
            "custom": self._parser.parse_custom,
        }.get(schema_type, self._parser.parse_custom)

        schema = parse_fn(schema_data, provider=provider)
        schema.provider = provider
        self._schemas[provider] = schema

        existing = self._adapters.get(provider)
        if existing and existing.schema_hash == schema.schema_hash():
            return existing

        adapter = self._compiler.compile(schema)
        self._adapters[provider] = adapter
        logger.info(f"Compiled adapter for {provider}: {len(adapter.endpoint_handlers)} handlers")
        return adapter

    def get_adapter(self, provider: str) -> Optional[CompiledAdapter]:
        return self._adapters.get(provider)

    def rebuild_adapter(self, provider: str) -> Optional[CompiledAdapter]:
        schema = self._schemas.get(provider)
        if not schema:
            return None
        adapter = self._compiler.compile(schema)
        self._adapters[provider] = adapter
        return adapter

    def remove_adapter(self, provider: str):
        self._adapters.pop(provider, None)
        self._schemas.pop(provider, None)

    def list_adapters(self) -> List[Dict[str, Any]]:
        return [a.to_dict() for a in self._adapters.values()]

    def get_stats(self) -> Dict[str, Any]:
        valid = sum(1 for a in self._adapters.values() if a.is_valid)
        return {
            "total_schemas": len(self._schemas),
            "total_adapters": len(self._adapters),
            "valid_adapters": valid,
            "invalid_adapters": len(self._adapters) - valid,
            "schema_types": {},
        }
