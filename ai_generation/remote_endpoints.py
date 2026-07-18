"""
Remote Endpoints — user-configured remote ComfyUI, Forge, inference APIs.
Removes the need for local GPU/model management.
"""
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class RemoteEndpoint:
    name: str = ""
    url: str = ""
    endpoint_type: str = ""  # comfyui, forge, api, custom
    auth_type: str = "api_key"  # api_key, bearer, basic, none
    auth_env_var: str = ""
    auth_value: str = ""
    supported_tasks: List[str] = field(default_factory=list)
    models: List[str] = field(default_factory=list)
    max_batch_size: int = 1
    timeout_secs: float = 300.0
    health_check_url: str = ""
    healthy: bool = True
    last_check: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    @property
    def auth_header(self) -> Optional[str]:
        if self.auth_type == "none":
            return None
        key = self.auth_value or os.environ.get(self.auth_env_var, "")
        if not key:
            return None
        if self.auth_type == "bearer":
            return f"Bearer {key}"
        if self.auth_type == "api_key":
            return key
        return key

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name, "url": self.url, "type": self.endpoint_type,
            "auth_type": self.auth_type, "auth_env_var": self.auth_env_var,
            "has_auth": bool(self.auth_header),
            "supported_tasks": self.supported_tasks,
            "models": self.models, "healthy": self.healthy,
            "timeout_secs": self.timeout_secs,
        }


class RemoteEndpointManager:
    """Manage user-configured remote inference endpoints."""

    def __init__(self, config_path: str = "./data/remote_endpoints.json"):
        self._config_path = config_path
        self._endpoints: Dict[str, RemoteEndpoint] = {}
        self._load()

    def _load(self):
        import json
        from pathlib import Path
        path = Path(self._config_path)
        if path.exists():
            try:
                data = json.loads(path.read_text())
                for item in data:
                    ep = RemoteEndpoint(**{k: v for k, v in item.items() if hasattr(RemoteEndpoint, k)})
                    self._endpoints[ep.name] = ep
            except Exception as e:
                logger.warning(f"Failed to load remote endpoints: {e}")

    def _save(self):
        import json
        from pathlib import Path
        path = Path(self._config_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        data = [ep.to_dict() for ep in self._endpoints.values()]
        path.write_text(json.dumps(data, indent=2))

    def add_endpoint(self, name: str, url: str, endpoint_type: str = "api",
                     auth_type: str = "api_key", auth_env_var: str = "", **kwargs) -> RemoteEndpoint:
        ep = RemoteEndpoint(
            name=name, url=url, endpoint_type=endpoint_type,
            auth_type=auth_type, auth_env_var=auth_env_var, **kwargs,
        )
        self._endpoints[name] = ep
        self._save()
        return ep

    def remove_endpoint(self, name: str) -> bool:
        if name in self._endpoints:
            del self._endpoints[name]
            self._save()
            return True
        return False

    def get_endpoint(self, name: str) -> Optional[RemoteEndpoint]:
        return self._endpoints.get(name)

    def list_endpoints(self) -> List[Dict[str, Any]]:
        return [ep.to_dict() for ep in self._endpoints.values()]

    async def check_health(self, name: str) -> Dict[str, Any]:
        ep = self._endpoints.get(name)
        if not ep:
            return {"error": f"Endpoint {name} not found"}
        try:
            import httpx
            check_url = ep.health_check_url or ep.url
            async with httpx.AsyncClient(timeout=10) as client:
                headers = {}
                if ep.auth_header:
                    headers["Authorization"] = ep.auth_header
                r = await client.get(check_url, headers=headers)
                ep.healthy = r.status_code < 500
                ep.last_check = datetime.now().isoformat()
                self._save()
                return {"healthy": ep.healthy, "status_code": r.status_code}
        except Exception as e:
            ep.healthy = False
            ep.last_check = datetime.now().isoformat()
            self._save()
            return {"healthy": False, "error": str(e)[:100]}

    async def check_all_health(self) -> Dict[str, Any]:
        results = {}
        for name in self._endpoints:
            results[name] = await self.check_health(name)
        return results

    def get_healthy_endpoints(self) -> List[RemoteEndpoint]:
        return [ep for ep in self._endpoints.values() if ep.healthy]

    def get_stats(self) -> Dict[str, Any]:
        healthy = sum(1 for ep in self._endpoints.values() if ep.healthy)
        return {
            "total_endpoints": len(self._endpoints),
            "healthy": healthy,
            "types": list(set(ep.endpoint_type for ep in self._endpoints.values())),
        }
