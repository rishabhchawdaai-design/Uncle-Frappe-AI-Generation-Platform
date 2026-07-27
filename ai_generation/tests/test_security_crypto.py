"""
Phase 30 Tests — Security Crypto Layer (SEC-05, SEC-06, SEC-12)

Tests encryption at rest, TLS verification, and model integrity.
"""
import os
import tempfile
import pytest
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))


def test_import_enums():
    from ai_generation.security_crypto import (
        EncryptionAlgorithm, KeyDerivationMethod, ChecksumAlgorithm, TLSVersion,
    )
    assert EncryptionAlgorithm.AES_256_GCM.value == "aes-256-gcm"
    assert ChecksumAlgorithm.SHA256.value == "sha256"
    assert TLSVersion.TLS_1_3.value == "tls-1.3"


def test_encryption_key_defaults():
    from ai_generation.security_crypto import EncryptionKey, EncryptionAlgorithm
    k = EncryptionKey()
    assert k.key_id == ""
    assert k.algorithm == EncryptionAlgorithm.AES_256_GCM
    assert k.rotated is False
    d = k.to_dict()
    assert d["algorithm"] == "aes-256-gcm"


def test_encrypted_payload_serialization():
    from ai_generation.security_crypto import EncryptedPayload
    p = EncryptedPayload(
        ciphertext=b"test", nonce=b"nonce", tag=b"tag",
        algorithm="aes-256-gcm", key_id="key-1", checksum="abc",
    )
    d = p.to_dict()
    assert d["algorithm"] == "aes-256-gcm"
    assert d["ciphertext_size"] == 4
    assert d["key_id"] == "key-1"


def test_file_checksum_serialization():
    from ai_generation.security_crypto import FileChecksum, ChecksumAlgorithm
    fc = FileChecksum(
        file_path="/test.bin", algorithm=ChecksumAlgorithm.SHA256,
        checksum="abc123", file_size=1024, verified=True,
    )
    d = fc.to_dict()
    assert d["file_path"] == "/test.bin"
    assert d["checksum"] == "abc123"
    assert d["verified"] is True


def test_tls_verification_serialization():
    from ai_generation.security_crypto import TLSVerification, TLSVersion
    tv = TLSVerification(host="example.com", port=443, tls_version=TLSVersion.TLS_1_3)
    d = tv.to_dict()
    assert d["host"] == "example.com"
    assert d["tls_version"] == "tls-1.3"
    assert d["certificate_valid"] is False


# ── EncryptionAtRest Tests ──

def test_encryption_at_rest_init():
    from ai_generation.security_crypto import EncryptionAtRest
    ear = EncryptionAtRest()
    stats = ear.get_stats()
    assert stats["key_count"] == 0
    assert stats["has_aes_support"] is True


def test_generate_key():
    from ai_generation.security_crypto import EncryptionAtRest
    ear = EncryptionAtRest()
    key = ear.generate_key()
    assert key.key_id.startswith("key-")
    assert key.key_material is not None
    assert len(key.key_material) == 32
    assert ear.get_stats()["key_count"] == 1


def test_generate_key_custom_material():
    from ai_generation.security_crypto import EncryptionAtRest
    ear = EncryptionAtRest()
    material = b"0123456789abcdef0123456789abcdef"
    key = ear.generate_key(key_material=material)
    assert key.key_material == material


def test_encrypt_decrypt_roundtrip():
    from ai_generation.security_crypto import EncryptionAtRest
    ear = EncryptionAtRest()
    key = ear.generate_key()
    plaintext = b"Hello, ACOS Platform!"
    payload = ear.encrypt(plaintext, key.key_id)
    assert payload.ciphertext != plaintext
    assert payload.key_id == key.key_id
    assert len(payload.checksum) == 64  # SHA-256 hex
    decrypted = ear.decrypt(payload)
    assert decrypted == plaintext


def test_encrypt_decrypt_fallback():
    from ai_generation.security_crypto import EncryptionAtRest
    ear = EncryptionAtRest()
    key = ear.generate_key()
    ear._has_aes = False
    plaintext = b"Test fallback encryption"
    payload = ear.encrypt(plaintext, key.key_id)
    assert "-fallback" in payload.algorithm
    decrypted = ear.decrypt(payload)
    assert decrypted == plaintext


def test_encrypt_auto_generates_key():
    from ai_generation.security_crypto import EncryptionAtRest
    ear = EncryptionAtRest()
    payload = ear.encrypt(b"test data")
    assert payload.key_id != ""
    assert ear.get_stats()["key_count"] == 1


def test_get_keys():
    from ai_generation.security_crypto import EncryptionAtRest
    ear = EncryptionAtRest()
    ear.generate_key()
    ear.generate_key()
    keys = ear.get_keys()
    assert len(keys) == 2
    assert keys[0]["key_id"] != keys[1]["key_id"]


def test_decrypt_wrong_key():
    from ai_generation.security_crypto import EncryptionAtRest, EncryptedPayload
    ear = EncryptionAtRest()
    key = ear.generate_key()
    payload = ear.encrypt(b"secret", key.key_id)
    ear2 = EncryptionAtRest()
    result = ear2.decrypt(payload)
    assert result is None


# ── EncryptionInTransit Tests ──

def test_encryption_in_transit_init():
    from ai_generation.security_crypto import EncryptionInTransit
    eit = EncryptionInTransit()
    stats = eit.get_stats()
    assert stats["cached_verifications"] == 0


def test_tls_verification_stats():
    from ai_generation.security_crypto import EncryptionInTransit
    eit = EncryptionInTransit()
    result = eit.verify_checksum_match("example.com", 443, "abc")
    assert result["cached"] is False


def test_tls_stats_empty():
    from ai_generation.security_crypto import EncryptionInTransit
    eit = EncryptionInTransit()
    stats = eit.get_stats()
    assert isinstance(stats["hosts_verified"], list)


# ── ModelSecurity Tests ──

def test_model_security_init():
    from ai_generation.security_crypto import ModelSecurity
    ms = ModelSecurity()
    stats = ms.get_stats()
    assert stats["checksums_computed"] == 0
    assert "sha256" in stats["algorithms_supported"]


def test_compute_checksum():
    from ai_generation.security_crypto import ModelSecurity, ChecksumAlgorithm
    ms = ModelSecurity()
    with tempfile.NamedTemporaryFile(delete=False, suffix=".bin") as f:
        f.write(b"test model data")
        path = f.name
    try:
        fc = ms.compute_checksum(path)
        assert fc.checksum != ""
        assert len(fc.checksum) == 64  # SHA-256 hex
        assert fc.file_size == 15
        # compute_checksum does not set verified (that is for verify_checksum)
    finally:
        os.unlink(path)


def test_compute_checksum_file_not_found():
    from ai_generation.security_crypto import ModelSecurity
    ms = ModelSecurity()
    fc = ms.compute_checksum("/nonexistent/file.bin")
    assert fc.to_dict()["checksum"] == ""


def test_register_and_verify_checksum():
    from ai_generation.security_crypto import ModelSecurity
    ms = ModelSecurity()
    with tempfile.NamedTemporaryFile(delete=False, suffix=".bin") as f:
        f.write(b"model weights")
        path = f.name
    try:
        fc = ms.compute_checksum(path)
        ms.register_expected(path, fc.checksum)
        result = ms.verify_checksum(path)
        assert result["verified"] is True
    finally:
        os.unlink(path)


def test_verify_checksum_mismatch():
    from ai_generation.security_crypto import ModelSecurity
    ms = ModelSecurity()
    with tempfile.NamedTemporaryFile(delete=False, suffix=".bin") as f:
        f.write(b"model weights")
        path = f.name
    try:
        ms.register_expected(path, "wrong_checksum_value")
        result = ms.verify_checksum(path)
        assert result["verified"] is False
    finally:
        os.unlink(path)


def test_compute_batch():
    from ai_generation.security_crypto import ModelSecurity
    ms = ModelSecurity()
    files = []
    for i in range(3):
        f = tempfile.NamedTemporaryFile(delete=False, suffix=".bin")
        f.write(f"model_{i}".encode())
        f.close()
        files.append(f.name)
    try:
        results = ms.compute_batch(files)
        assert len(results) == 3
        for r in results:
            assert r["checksum"] != ""
    finally:
        for fp in files:
            os.unlink(fp)


def test_verify_batch():
    from ai_generation.security_crypto import ModelSecurity
    ms = ModelSecurity()
    files = []
    for i in range(3):
        f = tempfile.NamedTemporaryFile(delete=False, suffix=".bin")
        f.write(f"model_{i}".encode())
        f.close()
        files.append(f.name)
    try:
        result = ms.verify_batch(files)
        assert result["total"] == 3
        assert result["verified"] == 3
        assert result["failed"] == 0
    finally:
        for fp in files:
            os.unlink(fp)


def test_checksum_sha512():
    from ai_generation.security_crypto import ModelSecurity, ChecksumAlgorithm
    ms = ModelSecurity()
    with tempfile.NamedTemporaryFile(delete=False, suffix=".bin") as f:
        f.write(b"test")
        path = f.name
    try:
        fc = ms.compute_checksum(path, ChecksumAlgorithm.SHA512)
        assert len(fc.checksum) == 128  # SHA-512 hex
    finally:
        os.unlink(path)


# ── SDK Integration Tests ──

def test_sdk_encryption_at_rest_import():
    from ai_generation.sdk import UncleFrappeAI
    sdk = UncleFrappeAI({"test_mode": True})
    assert sdk.encryption_at_rest is not None


def test_sdk_generate_encryption_key():
    from ai_generation.sdk import UncleFrappeAI
    sdk = UncleFrappeAI({"test_mode": True})
    key = sdk.generate_encryption_key()
    assert key["key_id"].startswith("key-")
    assert key["has_material"] is True


def test_sdk_encrypt_decrypt():
    from ai_generation.sdk import UncleFrappeAI
    sdk = UncleFrappeAI({"test_mode": True})
    key = sdk.generate_encryption_key()
    data = b"test secret data"
    encrypted = sdk.encrypt_data(data, key["key_id"])
    assert encrypted["ciphertext_size"] > 0
    assert encrypted["key_id"] == key["key_id"]


def test_sdk_get_encryption_stats():
    from ai_generation.sdk import UncleFrappeAI
    sdk = UncleFrappeAI({"test_mode": True})
    stats = sdk.get_encryption_stats()
    assert stats["key_count"] == 0
    assert stats["has_aes_support"] is True


def test_sdk_model_security_import():
    from ai_generation.sdk import UncleFrappeAI
    sdk = UncleFrappeAI({"test_mode": True})
    assert sdk.model_security is not None


def test_sdk_compute_file_checksum():
    from ai_generation.sdk import UncleFrappeAI
    sdk = UncleFrappeAI({"test_mode": True})
    with tempfile.NamedTemporaryFile(delete=False, suffix=".bin") as f:
        f.write(b"test data")
        path = f.name
    try:
        result = sdk.compute_file_checksum(path)
        assert result["checksum"] != ""
        assert result["file_size"] == 9
    finally:
        os.unlink(path)


def test_sdk_get_model_security_stats():
    from ai_generation.sdk import UncleFrappeAI
    sdk = UncleFrappeAI({"test_mode": True})
    stats = sdk.get_model_security_stats()
    assert "sha256" in stats["algorithms_supported"]


def test_sdk_encryption_in_transit_import():
    from ai_generation.sdk import UncleFrappeAI
    sdk = UncleFrappeAI({"test_mode": True})
    assert sdk.encryption_in_transit is not None


def test_sdk_get_tls_stats():
    from ai_generation.sdk import UncleFrappeAI
    sdk = UncleFrappeAI({"test_mode": True})
    stats = sdk.get_tls_stats()
    assert stats["cached_verifications"] == 0


# ── MCP Tool Tests ──

def test_mcp_security_crypto_tools_exist():
    from ai_generation.mcp_tools import MCP_GENERATION_TOOLS
    assert "generate_encryption_key" in MCP_GENERATION_TOOLS
    assert "encrypt_data" in MCP_GENERATION_TOOLS
    assert "get_encryption_stats" in MCP_GENERATION_TOOLS
    assert "compute_file_checksum" in MCP_GENERATION_TOOLS
    assert "verify_file_checksum" in MCP_GENERATION_TOOLS
    assert "get_model_security_stats" in MCP_GENERATION_TOOLS
    assert "get_tls_stats" in MCP_GENERATION_TOOLS


def test_mcp_security_crypto_handler_import():
    from ai_generation.mcp_tools import MCPGenerationTools
    tools = MCPGenerationTools()
    assert hasattr(tools, "_handle_generate_encryption_key")
    assert hasattr(tools, "_handle_encrypt_data")
    assert hasattr(tools, "_handle_get_encryption_stats")
    assert hasattr(tools, "_handle_compute_file_checksum")
    assert hasattr(tools, "_handle_verify_file_checksum")
    assert hasattr(tools, "_handle_get_model_security_stats")
    assert hasattr(tools, "_handle_get_tls_stats")
