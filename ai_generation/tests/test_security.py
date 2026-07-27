"""
Phase 27 Tests — Security Layer

Tests authentication, RBAC authorization, user management, and SDK/MCP exposure.
"""
import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))


def test_security_level_enum():
    from ai_generation.security import SecurityLevel
    assert SecurityLevel.DEVELOPMENT.value == "development"
    assert SecurityLevel.PRODUCTION.value == "production"
    assert SecurityLevel.STRICT.value == "strict"


def test_role_enum():
    from ai_generation.security import Role
    assert Role.ADMIN.value == "admin"
    assert Role.OPERATOR.value == "operator"
    assert Role.VIEWER.value == "viewer"


def test_permission_enum():
    from ai_generation.security import Permission
    assert Permission.GENERATE.value == "generate"
    assert Permission.ADMIN.value == "admin"


def test_security_manager_import():
    from ai_generation.security import SecurityManager
    sm = SecurityManager()
    assert sm is not None


def test_has_default_admin():
    from ai_generation.security import SecurityManager
    sm = SecurityManager()
    users = sm.list_users()
    assert len(users) >= 1
    assert any(u["username"] == "admin" for u in users)


def test_authenticate_api_key():
    from ai_generation.security import SecurityManager
    sm = SecurityManager()
    admin = sm.get_user("admin")
    assert admin is not None
    # Generate a key and authenticate
    key = sm.generate_api_key("admin")
    assert key is not None
    result = sm.authenticate_api_key(key)
    assert result is not None
    assert result["username"] == "admin"


def test_authenticate_bad_key():
    from ai_generation.security import SecurityManager
    sm = SecurityManager()
    result = sm.authenticate_api_key("bad_key")
    assert result is None


def test_create_user():
    from ai_generation.security import SecurityManager, Role
    sm = SecurityManager()
    result = sm.create_user("operator1", Role.OPERATOR)
    assert result is not None
    assert result["username"] == "operator1"
    assert result["role"] == "operator"


def test_create_duplicate_user():
    from ai_generation.security import SecurityManager
    sm = SecurityManager()
    sm.create_user("test_user")
    result = sm.create_user("test_user")
    assert result is None


def test_authorize_admin():
    from ai_generation.security import SecurityManager, Permission
    sm = SecurityManager()
    decision = sm.authorize("admin", Permission.GENERATE)
    assert decision.allowed is True


def test_authorize_viewer_limited():
    from ai_generation.security import SecurityManager, Permission
    sm = SecurityManager({"security_level": "production"})
    sm.create_user("viewer1")
    decision = sm.authorize("viewer1", Permission.GENERATE)
    assert decision.allowed is False
    decision2 = sm.authorize("viewer1", Permission.SEARCH)
    assert decision2.allowed is True


def test_authorize_development_mode():
    from ai_generation.security import SecurityManager, Permission
    sm = SecurityManager({"security_level": "development"})
    sm.create_user("dev_user")
    decision = sm.authorize("dev_user", Permission.ADMIN)
    assert decision.allowed is True  # dev mode allows everything


def test_check_permission():
    from ai_generation.security import SecurityManager
    sm = SecurityManager()
    assert sm.check_permission("admin", "generate") is True
    assert sm.check_permission("admin", "nonexistent") is False


def test_update_user_role():
    from ai_generation.security import SecurityManager, Role
    sm = SecurityManager()
    sm.create_user("promote_me")
    assert sm.update_user_role("promote_me", Role.OPERATOR)
    user = sm.get_user("promote_me")
    assert user["role"] == "operator"


def test_deactivate_user():
    from ai_generation.security import SecurityManager
    sm = SecurityManager()
    sm.create_user("deactivate_me")
    assert sm.deactivate_user("deactivate_me")
    user = sm.get_user("deactivate_me")
    assert user["is_active"] is False


def test_revoke_api_key():
    from ai_generation.security import SecurityManager
    sm = SecurityManager()
    key = sm.generate_api_key("admin")
    assert sm.revoke_api_key(key) is True
    result = sm.authenticate_api_key(key)
    assert result is None


def test_audit_log():
    from ai_generation.security import SecurityManager
    sm = SecurityManager()
    sm.generate_api_key("admin")
    log = sm.get_audit_log()
    assert len(log) >= 1
    assert any(e["event"] == "api_key_generated" for e in log)


def test_security_stats():
    from ai_generation.security import SecurityManager
    sm = SecurityManager()
    stats = sm.get_stats()
    assert "security_level" in stats
    assert "user_count" in stats
    assert stats["user_count"] >= 1
    assert "roles" in stats
    assert "permissions" in stats


def test_user_serialization():
    from ai_generation.security import SecurityManager
    sm = SecurityManager()
    user = sm.get_user("admin")
    assert "user_id" in user
    assert "username" in user
    assert "role" in user


# ── SDK Integration Tests ─────────────────────────────────────

def test_sdk_security_import():
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    assert hasattr(ai, 'security')
    assert hasattr(ai, 'authenticate_api_key')
    assert hasattr(ai, 'create_user')
    assert hasattr(ai, 'authorize')
    assert hasattr(ai, 'list_security_users')
    assert hasattr(ai, 'get_security_stats')


def test_sdk_list_security_users():
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    users = ai.list_security_users()
    assert len(users) >= 1


def test_sdk_security_stats():
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    stats = ai.get_security_stats()
    assert stats["user_count"] >= 1


def test_sdk_authorize():
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    result = ai.authorize("admin", "generate")
    assert result["allowed"] is True


# ── MCP Tools Tests ──────────────────────────────────────────

def test_mcp_security_tools_exist():
    from ai_generation.mcp_tools import MCP_GENERATION_TOOLS
    assert "list_security_users" in MCP_GENERATION_TOOLS
    assert "authorize_user" in MCP_GENERATION_TOOLS
    assert "get_security_stats" in MCP_GENERATION_TOOLS


def test_mcp_security_handler_import():
    from ai_generation.mcp_tools import MCPGenerationTools
    handler = MCPGenerationTools()
    assert hasattr(handler, '_handle_list_security_users')
    assert hasattr(handler, '_handle_authorize_user')
    assert hasattr(handler, '_handle_get_security_stats')
