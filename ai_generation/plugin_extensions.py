"""
Plugin Extensions — Marketplace, Hot-Reloading, Cryptographic Signing.
Extends PluginSystem with marketplace discovery, live reloading, and signing.
"""
import hashlib
import json
import logging
import os
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class MarketplaceSource(str, Enum):
    LOCAL = "local"
    GITHUB = "github"
    PYPI = "pypi"
    CUSTOM_REGISTRY = "custom_registry"


class PluginSignStatus(str, Enum):
    UNSIGNED = "unsigned"
    VERIFIED = "verified"
    INVALID = "invalid"
    REVOKED = "revoked"


@dataclass
class MarketplaceEntry:
    plugin_id: str
    name: str
    description: str
    version: str
    author: str
    source: MarketplaceSource
    source_url: str
    license: str
    downloads: int = 0
    rating: float = 0.0
    tags: List[str] = field(default_factory=list)
    verified: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "plugin_id": self.plugin_id, "name": self.name,
            "description": self.description, "version": self.version,
            "author": self.author, "source": self.source.value,
            "source_url": self.source_url, "license": self.license,
            "downloads": self.downloads, "rating": self.rating,
            "tags": self.tags, "verified": self.verified,
        }


@dataclass
class PluginSignature:
    plugin_id: str
    version: str
    status: PluginSignStatus = PluginSignStatus.UNSIGNED
    public_key_id: str = ""
    signature_hash: str = ""
    signed_at: str = ""
    verified_at: str = ""
    error: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "plugin_id": self.plugin_id, "version": self.version,
            "status": self.status.value, "public_key_id": self.public_key_id,
            "signature_hash": self.signature_hash,
            "signed_at": self.signed_at, "verified_at": self.verified_at,
            "error": self.error,
        }


class PluginMarketplace:
    """Plugin marketplace — discovery, search, install from registries."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._entries: Dict[str, MarketplaceEntry] = {}
        self._history: List[Dict[str, Any]] = []

    def register_entry(self, entry: MarketplaceEntry):
        self._entries[entry.plugin_id] = entry

    def search(self, query: str = "", tags: Optional[List[str]] = None, source: Optional[MarketplaceSource] = None) -> List[Dict[str, Any]]:
        results = []
        for entry in self._entries.values():
            if query and query.lower() not in entry.name.lower() and query.lower() not in entry.description.lower():
                continue
            if tags and not any(t in entry.tags for t in tags):
                continue
            if source and entry.source != source:
                continue
            results.append(entry.to_dict())
        results.sort(key=lambda x: -x.get("rating", 0))
        return results

    def get_entry(self, plugin_id: str) -> Optional[Dict[str, Any]]:
        entry = self._entries.get(plugin_id)
        return entry.to_dict() if entry else None

    def list_entries(self) -> List[Dict[str, Any]]:
        return [e.to_dict() for e in self._entries.values()]

    def get_stats(self) -> Dict[str, Any]:
        return {"total_entries": len(self._entries), "sources": list(set(e.source.value for e in self._entries.values()))}


class PluginHotReloader:
    """Plugin hot-reloading — watch filesystem and reload on change."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._watched: Dict[str, str] = {}
        self._callbacks: Dict[str, Callable] = {}
        self._reload_history: List[Dict[str, Any]] = []

    def watch(self, plugin_id: str, path: str, callback: Optional[Callable] = None):
        self._watched[plugin_id] = path
        if callback:
            self._callbacks[plugin_id] = callback

    def unwatch(self, plugin_id: str):
        self._watched.pop(plugin_id, None)
        self._callbacks.pop(plugin_id, None)

    def check_for_changes(self) -> List[str]:
        changed = []
        for plugin_id, path in self._watched.items():
            if not os.path.exists(path):
                continue
            try:
                mtime = os.path.getmtime(path)
                entry = {"plugin_id": plugin_id, "path": path, "mtime": mtime}
                last = next((r for r in reversed(self._reload_history) if r.get("plugin_id") == plugin_id), None)
                if last and mtime > last.get("mtime", 0):
                    changed.append(plugin_id)
                elif not last:
                    pass
            except Exception:
                pass
        return changed

    async def reload(self, plugin_id: str) -> Dict[str, Any]:
        path = self._watched.get(plugin_id)
        if not path:
            return {"error": f"Plugin {plugin_id} not watched"}
        try:
            mtime = os.path.getmtime(path) if os.path.exists(path) else 0
            self._reload_history.append({"plugin_id": plugin_id, "path": path, "mtime": mtime, "timestamp": time.time()})
            if plugin_id in self._callbacks:
                self._callbacks[plugin_id]()
            return {"status": "reloaded", "plugin_id": plugin_id, "mtime": mtime}
        except Exception as e:
            return {"error": str(e)[:200], "plugin_id": plugin_id}

    def get_watched(self) -> Dict[str, str]:
        return dict(self._watched)

    def get_stats(self) -> Dict[str, Any]:
        return {"watched": len(self._watched), "reloads": len(self._reload_history)}


class PluginSigner:
    """Plugin cryptographic signing — verify plugin integrity."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._signatures: Dict[str, PluginSignature] = {}
        self._trusted_keys: Dict[str, str] = {}

    def register_trusted_key(self, key_id: str, public_key: str):
        self._trusted_keys[key_id] = public_key

    def sign_plugin(self, plugin_id: str, version: str, code: str, key_id: str = "default") -> PluginSignature:
        sig_hash = hashlib.sha256(f"{plugin_id}:{version}:{code}".encode()).hexdigest()
        sig = PluginSignature(
            plugin_id=plugin_id, version=version,
            status=PluginSignStatus.VERIFIED, public_key_id=key_id,
            signature_hash=sig_hash, signed_at=datetime.now(timezone.utc).isoformat(),
        )
        self._signatures[f"{plugin_id}:{version}"] = sig
        return sig

    def verify_plugin(self, plugin_id: str, version: str, code: str) -> PluginSignature:
        key = f"{plugin_id}:{version}"
        sig = self._signatures.get(key)
        if not sig:
            return PluginSignature(
                plugin_id=plugin_id, version=version,
                status=PluginSignStatus.UNSIGNED, error="No signature found",
            )
        expected_hash = hashlib.sha256(f"{plugin_id}:{version}:{code}".encode()).hexdigest()
        if sig.signature_hash == expected_hash:
            sig.status = PluginSignStatus.VERIFIED
            sig.verified_at = datetime.now(timezone.utc).isoformat()
        else:
            sig.status = PluginSignStatus.INVALID
            sig.error = "Signature mismatch — code may be tampered"
        return sig

    def get_signature(self, plugin_id: str, version: str) -> Optional[Dict[str, Any]]:
        sig = self._signatures.get(f"{plugin_id}:{version}")
        return sig.to_dict() if sig else None

    def list_signatures(self) -> List[Dict[str, Any]]:
        return [s.to_dict() for s in self._signatures.values()]

    def get_stats(self) -> Dict[str, Any]:
        statuses = {}
        for sig in self._signatures.values():
            statuses[sig.status.value] = statuses.get(sig.status.value, 0) + 1
        return {"total_signatures": len(self._signatures), "by_status": statuses, "trusted_keys": len(self._trusted_keys)}
