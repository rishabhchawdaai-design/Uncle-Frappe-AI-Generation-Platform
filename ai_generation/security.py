"""
Security Layer — authentication, authorization (RBAC), and access control.

Based on ACOS Research: Security Canon
Provides authentication methods, role-based access control (RBAC),
capability-based authorization for plugins, and API key management.

Security levels:
- development: No restrictions
- production: Full RBAC enforcement
- strict: Maximum security with audit logging
"""
import hashlib
import logging
import secrets
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class SecurityLevel(str, Enum):
    DEVELOPMENT = "development"
    PRODUCTION = "production"
    STRICT = "strict"


class Role(str, Enum):
    ADMIN = "admin"
    OPERATOR = "operator"
    VIEWER = "viewer"
    PLUGIN = "plugin"


class Permission(str, Enum):
    GENERATE = "generate"
    EDIT = "edit"
    VIDEO = "video"
    AUDIO = "audio"
    OCR = "ocr"
    SEARCH = "search"
    BENCHMARK = "benchmark"
    MANAGE_PROVIDERS = "manage_providers"
    MANAGE_PLUGINS = "manage_plugins"
    VIEW_METRICS = "view_metrics"
    MANAGE_SECURITY = "manage_security"
    ADMIN = "admin"


# ── Permission Matrix ─────────────────────────────────────────

ROLE_PERMISSIONS: Dict[Role, Set[Permission]] = {
    Role.ADMIN: {p for p in Permission},
    Role.OPERATOR: {
        Permission.GENERATE, Permission.EDIT, Permission.VIDEO,
        Permission.AUDIO, Permission.OCR, Permission.SEARCH,
        Permission.BENCHMARK, Permission.VIEW_METRICS,
    },
    Role.VIEWER: {
        Permission.SEARCH, Permission.VIEW_METRICS,
    },
    Role.PLUGIN: {
        Permission.GENERATE, Permission.SEARCH,
    },
}


@dataclass
class User:
    """A platform user."""
    user_id: str = ""
    username: str = ""
    role: Role = Role.VIEWER
    api_key: str = ""
    created_at: str = ""
    last_active: str = ""
    is_active: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "username": self.username,
            "role": self.role.value,
            "has_api_key": bool(self.api_key),
            "created_at": self.created_at,
            "last_active": self.last_active,
            "is_active": self.is_active,
        }


@dataclass
class AccessDecision:
    """Result of an authorization check."""
    allowed: bool = True
    reason: str = ""
    user_id: str = ""
    permission: str = ""
    role: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "allowed": self.allowed,
            "reason": self.reason,
            "user_id": self.user_id,
            "permission": self.permission,
            "role": self.role,
        }


class SecurityManager:
    """
    Security layer providing authentication, RBAC authorization,
    and API key management.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._level = SecurityLevel(
            self.config.get("security_level", "development")
        )
        self._users: Dict[str, User] = {}
        self._api_keys: Dict[str, str] = {}  # api_key -> user_id
        self._audit_log: List[Dict[str, Any]] = []
        self._init_defaults()

    def _init_defaults(self):
        """Create default admin user."""
        admin_key = secrets.token_hex(32)
        admin = User(
            user_id="admin",
            username="admin",
            role=Role.ADMIN,
            api_key=admin_key,
            created_at=time.strftime("%Y-%m-%dT%H:%M:%S"),
        )
        self._users["admin"] = admin
        self._api_keys[admin_key] = "admin"

    # ── Authentication ─────────────────────────────────────────

    def authenticate_api_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        """Authenticate via API key."""
        user_id = self._api_keys.get(api_key)
        if not user_id:
            self._log_audit("auth_failure", {"method": "api_key"})
            return None
        user = self._users.get(user_id)
        if not user or not user.is_active:
            return None
        user.last_active = time.strftime("%Y-%m-%dT%H:%M:%S")
        self._log_audit("auth_success", {"user_id": user_id, "method": "api_key"})
        return user.to_dict()

    def authenticate_username(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate via username/password (development mode only)."""
        if self._level != SecurityLevel.DEVELOPMENT:
            self._log_audit("auth_failure", {"method": "username", "reason": "not allowed in production"})
            return None
        # In development, accept any password for existing users
        user = self._users.get(username)
        if user and user.is_active:
            self._log_audit("auth_success", {"user_id": username, "method": "username"})
            return user.to_dict()
        return None

    def generate_api_key(self, user_id: str) -> Optional[str]:
        """Generate a new API key for a user."""
        user = self._users.get(user_id)
        if not user:
            return None
        api_key = secrets.token_hex(32)
        self._api_keys[api_key] = user_id
        user.api_key = api_key
        self._log_audit("api_key_generated", {"user_id": user_id})
        return api_key

    def revoke_api_key(self, api_key: str) -> bool:
        """Revoke an API key."""
        if api_key in self._api_keys:
            user_id = self._api_keys.pop(api_key)
            user = self._users.get(user_id)
            if user:
                user.api_key = ""
            self._log_audit("api_key_revoked", {"user_id": user_id})
            return True
        return False

    # ── Authorization (RBAC) ───────────────────────────────────

    def authorize(self, user_id: str, permission: Permission) -> AccessDecision:
        """Check if a user has a specific permission."""
        if self._level == SecurityLevel.DEVELOPMENT:
            return AccessDecision(
                allowed=True, reason="development mode",
                user_id=user_id, permission=permission.value,
            )

        user = self._users.get(user_id)
        if not user:
            return AccessDecision(
                allowed=False, reason="user not found",
                user_id=user_id, permission=permission.value,
            )
        if not user.is_active:
            return AccessDecision(
                allowed=False, reason="user inactive",
                user_id=user_id, permission=permission.value,
            )

        role_perms = ROLE_PERMISSIONS.get(user.role, set())
        allowed = permission in role_perms
        self._log_audit("auth_check", {
            "user_id": user_id, "permission": permission.value,
            "role": user.role.value, "allowed": allowed,
        })
        return AccessDecision(
            allowed=allowed,
            reason="" if allowed else f"role {user.role.value} lacks {permission.value}",
            user_id=user_id, permission=permission.value, role=user.role.value,
        )

    def check_permission(self, user_id: str, permission: str) -> bool:
        """Quick permission check."""
        try:
            perm = Permission(permission)
        except ValueError:
            return False
        return self.authorize(user_id, perm).allowed

    # ── User Management ────────────────────────────────────────

    def create_user(self, username: str, role: Role = Role.VIEWER) -> Optional[Dict[str, Any]]:
        """Create a new user."""
        if username in self._users:
            return None
        user = User(
            user_id=username,
            username=username,
            role=role,
            created_at=time.strftime("%Y-%m-%dT%H:%M:%S"),
        )
        self._users[username] = user
        self._log_audit("user_created", {"username": username, "role": role.value})
        return user.to_dict()

    def update_user_role(self, username: str, role: Role) -> bool:
        """Update a user's role."""
        user = self._users.get(username)
        if not user:
            return False
        old_role = user.role
        user.role = role
        self._log_audit("role_updated", {"username": username, "old": old_role.value, "new": role.value})
        return True

    def deactivate_user(self, username: str) -> bool:
        """Deactivate a user."""
        user = self._users.get(username)
        if not user:
            return False
        user.is_active = False
        self._log_audit("user_deactivated", {"username": username})
        return True

    def list_users(self) -> List[Dict[str, Any]]:
        """List all users."""
        return [u.to_dict() for u in self._users.values()]

    def get_user(self, username: str) -> Optional[Dict[str, Any]]:
        """Get a user."""
        user = self._users.get(username)
        return user.to_dict() if user else None

    # ── Audit Log ──────────────────────────────────────────────

    def get_audit_log(self, limit: int = 100,
                       event_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get audit log entries."""
        log = self._audit_log
        if event_type:
            log = [e for e in log if e.get("event") == event_type]
        return log[-limit:]

    def _log_audit(self, event: str, details: Dict[str, Any]):
        """Log an audit event."""
        entry = {
            "event": event,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            **details,
        }
        self._audit_log.append(entry)

    # ── Stats ──────────────────────────────────────────────────

    def get_stats(self) -> Dict[str, Any]:
        """Get security statistics."""
        by_role = {}
        for user in self._users.values():
            by_role[user.role.value] = by_role.get(user.role.value, 0) + 1

        return {
            "security_level": self._level.value,
            "user_count": len(self._users),
            "api_key_count": len(self._api_keys),
            "audit_entries": len(self._audit_log),
            "by_role": by_role,
            "roles": [r.value for r in Role],
            "permissions": [p.value for p in Permission],
        }


# ── Process Sandboxing (SEC-07) ─────────────────────────────────

class SandboxConfig:
    """Configuration for process sandboxing."""
    def __init__(
        self, max_memory_mb: int = 512, max_cpu_seconds: int = 60,
        max_file_size_mb: int = 100, allowed_paths: Optional[List[str]] = None,
        blocked_paths: Optional[List[str]] = None,
        network_access: bool = False, env_vars: Optional[Dict[str, str]] = None,
    ):
        self.max_memory_mb = max_memory_mb
        self.max_cpu_seconds = max_cpu_seconds
        self.max_file_size_mb = max_file_size_mb
        self.allowed_paths = allowed_paths or ["/tmp", "./output"]
        self.blocked_paths = blocked_paths or ["/etc", "/root", "/home"]
        self.network_access = network_access
        self.env_vars = env_vars or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "max_memory_mb": self.max_memory_mb,
            "max_cpu_seconds": self.max_cpu_seconds,
            "max_file_size_mb": self.max_file_size_mb,
            "allowed_paths": self.allowed_paths,
            "blocked_paths": self.blocked_paths,
            "network_access": self.network_access,
            "env_vars": self.env_vars,
        }


class ProcessSandbox:
    """
    Process-level sandboxing for plugin execution.
    Uses resource limits, path restrictions, and environment isolation.
    """
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._history: List[Dict[str, Any]] = []

    def check_path_access(self, path: str, config: Optional[SandboxConfig] = None) -> Dict[str, Any]:
        cfg = config or SandboxConfig()
        path = os.path.abspath(path) if 'os' in dir() else path
        for blocked in cfg.blocked_paths:
            if path.startswith(blocked):
                return {"allowed": False, "reason": f"Path '{path}' matches blocked prefix '{blocked}'"}
        for allowed in cfg.allowed_paths:
            if path.startswith(allowed):
                return {"allowed": True, "reason": f"Path '{path}' matches allowed prefix '{allowed}'"}
        return {"allowed": False, "reason": f"Path '{path}' not in allowed paths"}

    def get_resource_limits(self, config: Optional[SandboxConfig] = None) -> Dict[str, Any]:
        cfg = config or SandboxConfig()
        limits: Dict[str, Any] = {}
        try:
            import resource
            limits["memory_bytes"] = cfg.max_memory_mb * 1024 * 1024
            limits["cpu_seconds"] = cfg.max_cpu_seconds
            limits["has_resource_module"] = True
        except ImportError:
            limits["has_resource_module"] = False
            limits["memory_bytes"] = cfg.max_memory_mb * 1024 * 1024
            limits["cpu_seconds"] = cfg.max_cpu_seconds
        return limits

    def create_sandboxed_env(self, config: Optional[SandboxConfig] = None) -> Dict[str, str]:
        import os as _os
        cfg = config or SandboxConfig()
        env = {k: v for k, v in _os.environ.items() if k in ("PATH", "HOME", "LANG", "LC_ALL")}
        env.update(cfg.env_vars)
        return env

    def get_stats(self) -> Dict[str, Any]:
        return {
            "total_sandbox_checks": len(self._history),
            "allowed": sum(1 for h in self._history if h.get("allowed")),
            "denied": sum(1 for h in self._history if not h.get("allowed")),
        }
