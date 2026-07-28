"""
Security Crypto Layer — Encryption at Rest, In Transit, Model Integrity.

Based on ACOS Research: Security Canon §5-6
Provides encryption, TLS verification, and model checksum validation.

SEC-05: Encryption at Rest — AES-256-GCM for data at rest
SEC-06: Encryption in Transit — TLS verification utilities
SEC-12: Model Security — SHA-256 checksum verification
"""
import hashlib
import hmac
import json
import logging
import os
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class EncryptionAlgorithm(str, Enum):
    AES_256_GCM = "aes-256-gcm"
    AES_128_GCM = "aes-128-gcm"
    CHACHA20_POLY1305 = "chacha20-poly1305"


class KeyDerivationMethod(str, Enum):
    PBKDF2 = "pbkdf2"
    ARGON2 = "argon2"
    SCRYPT = "scrypt"


class ChecksumAlgorithm(str, Enum):
    SHA256 = "sha256"
    SHA512 = "sha512"
    SHA3_256 = "sha3-256"
    BLAKE2B = "blake2b"
    MD5 = "md5"


class TLSVersion(str, Enum):
    TLS_1_2 = "tls-1.2"
    TLS_1_3 = "tls-1.3"


@dataclass
class EncryptionKey:
    key_id: str = ""
    algorithm: EncryptionAlgorithm = EncryptionAlgorithm.AES_256_GCM
    key_material: bytes = b""
    created_at: str = ""
    expires_at: str = ""
    rotated: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "key_id": self.key_id,
            "algorithm": self.algorithm.value,
            "created_at": self.created_at,
            "expires_at": self.expires_at,
            "rotated": self.rotated,
            "has_material": len(self.key_material) > 0,
        }


@dataclass
class EncryptedPayload:
    ciphertext: bytes = b""
    nonce: bytes = b""
    tag: bytes = b""
    algorithm: str = ""
    key_id: str = ""
    checksum: str = ""
    timestamp: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "algorithm": self.algorithm,
            "key_id": self.key_id,
            "checksum": self.checksum,
            "timestamp": self.timestamp,
            "ciphertext_size": len(self.ciphertext),
            "nonce_size": len(self.nonce),
            "tag_size": len(self.tag),
        }


@dataclass
class FileChecksum:
    file_path: str = ""
    algorithm: ChecksumAlgorithm = ChecksumAlgorithm.SHA256
    checksum: str = ""
    file_size: int = 0
    computed_at: str = ""
    verified: bool = False
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "file_path": self.file_path,
            "algorithm": self.algorithm.value,
            "checksum": self.checksum,
            "file_size": self.file_size,
            "computed_at": self.computed_at,
            "verified": self.verified,
        }


@dataclass
class TLSVerification:
    host: str = ""
    port: int = 443
    tls_version: TLSVersion = TLSVersion.TLS_1_3
    cipher_suite: str = ""
    certificate_valid: bool = False
    certificate_expired: bool = False
    certificate_issuer: str = ""
    certificate_subject: str = ""
    fingerprint_sha256: str = ""
    verified_at: str = ""
    latency_ms: float = 0.0
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "host": self.host,
            "port": self.port,
            "tls_version": self.tls_version.value,
            "cipher_suite": self.cipher_suite,
            "certificate_valid": self.certificate_valid,
            "certificate_expired": self.certificate_expired,
            "certificate_issuer": self.certificate_issuer,
            "certificate_subject": self.certificate_subject,
            "fingerprint_sha256": self.fingerprint_sha256,
            "verified_at": self.verified_at,
            "latency_ms": round(self.latency_ms, 2),
            "error": self.error,
        }


class EncryptionAtRest:
    """
    SEC-05: Encryption at Rest — AES-256-GCM for data at rest.

    Provides symmetric encryption for model weights, metadata,
    benchmarks, logs, and backups using AES-256-GCM.

    Falls back to PBKDF2-HMAC when AES libraries are unavailable.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._keys: Dict[str, EncryptionKey] = {}
        self._key_counter: int = 0
        self._has_aes: bool = self._check_aes_support()
        self._default_algorithm = EncryptionAlgorithm.AES_256_GCM

    def _check_aes_support(self) -> bool:
        try:
            from cryptography.hazmat.primitives.ciphers.aead import AESGCM
            return True
        except ImportError:
            return False

    def generate_key(self, key_material: Optional[bytes] = None,
                      algorithm: EncryptionAlgorithm = EncryptionAlgorithm.AES_256_GCM) -> EncryptionKey:
        self._key_counter += 1
        key_id = f"key-{self._key_counter}-{int(time.time())}"
        if key_material is None:
            if self._has_aes:
                key_material = os.urandom(32)
            else:
                key_material = os.urandom(32)

        key = EncryptionKey(
            key_id=key_id,
            algorithm=algorithm,
            key_material=key_material,
            created_at=datetime.now().isoformat(),
        )
        self._keys[key_id] = key
        logger.info(f"Generated encryption key: {key_id}")
        return key

    def encrypt(self, plaintext: bytes, key_id: Optional[str] = None) -> EncryptedPayload:
        if key_id is None:
            key = self.generate_key()
        else:
            key = self._keys.get(key_id)
            if key is None:
                raise ValueError(f"Key not found: {key_id}")

        if self._has_aes:
            return self._encrypt_aes(plaintext, key)
        else:
            return self._encrypt_fallback(plaintext, key)

    def _encrypt_aes(self, plaintext: bytes, key: EncryptionKey) -> EncryptedPayload:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        nonce = os.urandom(12)
        aesgcm = AESGCM(key.key_material)
        ciphertext = aesgcm.encrypt(nonce, plaintext, None)
        tag = ciphertext[-16:]
        ciphertext = ciphertext[:-16]
        return EncryptedPayload(
            ciphertext=ciphertext,
            nonce=nonce,
            tag=tag,
            algorithm=key.algorithm.value,
            key_id=key.key_id,
            checksum=hashlib.sha256(plaintext).hexdigest(),
            timestamp=datetime.now().isoformat(),
        )

    def _encrypt_fallback(self, plaintext: bytes, key: EncryptionKey) -> EncryptedPayload:
        nonce = os.urandom(16)
        cipher_key = hashlib.pbkdf2_hmac("sha256", key.key_material, nonce, 100000)
        encrypted = bytes(a ^ b for a, b in zip(plaintext, cipher_key * (len(plaintext) // len(cipher_key) + 1)))
        tag = hashlib.sha256(encrypted).digest()[:16]
        return EncryptedPayload(
            ciphertext=encrypted,
            nonce=nonce,
            tag=tag,
            algorithm=key.algorithm.value + "-fallback",
            key_id=key.key_id,
            checksum=hashlib.sha256(plaintext).hexdigest(),
            timestamp=datetime.now().isoformat(),
        )

    def decrypt(self, payload: EncryptedPayload, key_id: Optional[str] = None) -> Optional[bytes]:
        key = self._keys.get(payload.key_id or key_id or "")
        if key is None:
            return None

        if self._has_aes and "-fallback" not in payload.algorithm:
            return self._decrypt_aes(payload, key)
        else:
            return self._decrypt_fallback(payload, key)

    def _decrypt_aes(self, payload: EncryptedPayload, key: EncryptionKey) -> Optional[bytes]:
        try:
            from cryptography.hazmat.primitives.ciphers.aead import AESGCM
            aesgcm = AESGCM(key.key_material)
            nonce = payload.nonce
            tag = payload.tag
            ciphertext = payload.ciphertext + tag
            plaintext = aesgcm.decrypt(nonce, ciphertext, None)
            return plaintext
        except Exception as e:
            logger.error(f"AES decryption failed: {e}")
            return None

    def _decrypt_fallback(self, payload: EncryptedPayload, key: EncryptionKey) -> Optional[bytes]:
        nonce = payload.nonce
        cipher_key = hashlib.pbkdf2_hmac("sha256", key.key_material, nonce, 100000)
        plaintext = bytes(a ^ b for a, b in zip(payload.ciphertext, cipher_key * (len(payload.ciphertext) // len(cipher_key) + 1)))
        return plaintext

    def encrypt_file(self, file_path: str, key_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        try:
            with open(file_path, "rb") as f:
                data = f.read()
            payload = self.encrypt(data, key_id)
            result = payload.to_dict()
            result["original_size"] = len(data)
            return result
        except Exception as e:
            return {"error": str(e)}

    def get_stats(self) -> Dict[str, Any]:
        return {
            "key_count": len(self._keys),
            "has_aes_support": self._has_aes,
            "keys_generated": self._key_counter,
            "active_keys": sum(1 for k in self._keys.values() if not k.rotated),
        }

    def get_keys(self) -> List[Dict[str, Any]]:
        return [k.to_dict() for k in self._keys.values()]


class EncryptionInTransit:
    """
    SEC-06: Encryption in Transit — TLS verification utilities.

    Provides TLS certificate verification, fingerprinting,
    and connection health checking for secure endpoints.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._verification_cache: Dict[str, TLSVerification] = {}
        self._cache_ttl: float = self.config.get("cache_ttl", 300.0)

    async def verify_tls(self, host: str, port: int = 443) -> TLSVerification:
        result = TLSVerification(host=host, port=port, verified_at=datetime.now().isoformat())
        try:
            import ssl
            import socket
            context = ssl.create_default_context()
            start = time.time()
            with socket.create_connection((host, port), timeout=5.0) as sock:
                with context.wrap_socket(sock, server_hostname=host) as ssock:
                    latency = (time.time() - start) * 1000
                    result.latency_ms = latency
                    cert = ssock.getpeercert()
                    result.tls_version = TLSVersion(ssock.version().replace("TLSv", "tls-"))
                    result.cipher_suite = ssock.cipher()[0]
                    result.certificate_valid = True
                    if cert:
                        result.certificate_issuer = dict(x[0] for x in cert.get("issuer", [])).get("organizationName", "")
                        result.certificate_subject = dict(x[0] for x in cert.get("subject", [])).get("commonName", "")
                        if cert.get("notAfter"):
                            result.certificate_expired = datetime.strptime(
                                cert["notAfter"], "%b %d %H:%M:%S %Y %Z"
                            ) < datetime.now(timezone.utc)
                    result.fingerprint_sha256 = hashlib.sha256(
                        ssock.getpeercert(binary_form=True) or b""
                    ).hexdigest()
        except ImportError:
            result.error = "ssl module not available"
        except Exception as e:
            result.error = str(e)

        self._verification_cache[f"{host}:{port}"] = result
        return result

    def verify_checksum_match(self, host: str, port: int, expected_fingerprint: str) -> Dict[str, Any]:
        cache_key = f"{host}:{port}"
        cached = self._verification_cache.get(cache_key)
        if cached and (time.time() - self._parse_ts(cached.verified_at)) < self._cache_ttl:
            match = cached.fingerprint_sha256 == expected_fingerprint
            return {"host": host, "port": port, "match": match, "cached": True,
                    "actual": cached.fingerprint_sha256, "expected": expected_fingerprint}
        return {"host": host, "port": port, "match": False, "cached": False,
                "error": "Not cached, run verify_tls first"}

    def _parse_ts(self, ts: str) -> float:
        try:
            return datetime.fromisoformat(ts).timestamp()
        except Exception:
            return 0.0

    def get_stats(self) -> Dict[str, Any]:
        return {
            "cached_verifications": len(self._verification_cache),
            "hosts_verified": list(self._verification_cache.keys()),
        }


class ModelSecurity:
    """
    SEC-12: Model Security — SHA-256 checksum verification.

    Provides model file integrity validation via cryptographic checksums.
    Supports SHA-256, SHA-512, SHA3-256, and BLAKE2b.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._checksums: Dict[str, FileChecksum] = {}
        self._expected_checksums: Dict[str, str] = {}

    def compute_checksum(self, file_path: str,
                          algorithm: ChecksumAlgorithm = ChecksumAlgorithm.SHA256) -> FileChecksum:
        try:
            import pathlib
            path = pathlib.Path(file_path)
            if not path.exists():
                fc = FileChecksum(file_path=file_path, algorithm=algorithm)
                fc.error = f"File not found: {file_path}"
                return fc

            file_size = path.stat().st_size
            h = hashlib.new(algorithm.value)
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    h.update(chunk)
            checksum = h.hexdigest()

            fc = FileChecksum(
                file_path=file_path,
                algorithm=algorithm,
                checksum=checksum,
                file_size=file_size,
                computed_at=datetime.now().isoformat(),
            )
            self._checksums[file_path] = fc
            return fc
        except Exception as e:
            fc = FileChecksum(file_path=file_path, algorithm=algorithm)
            fc.error = str(e)
            return fc

    def register_expected(self, file_path: str, expected_checksum: str,
                           algorithm: ChecksumAlgorithm = ChecksumAlgorithm.SHA256):
        self._expected_checksums[file_path] = expected_checksum

    def verify_checksum(self, file_path: str,
                         algorithm: ChecksumAlgorithm = ChecksumAlgorithm.SHA256) -> Dict[str, Any]:
        fc = self.compute_checksum(file_path, algorithm)
        if fc.error:
            return fc.to_dict()
        expected = self._expected_checksums.get(file_path)
        if expected:
            fc.verified = fc.checksum == expected
        else:
            fc.verified = True
        return fc.to_dict()

    def compute_batch(self, file_paths: List[str],
                       algorithm: ChecksumAlgorithm = ChecksumAlgorithm.SHA256) -> List[Dict[str, Any]]:
        return [self.compute_checksum(fp, algorithm).to_dict() for fp in file_paths]

    def verify_batch(self, file_paths: List[str],
                      algorithm: ChecksumAlgorithm = ChecksumAlgorithm.SHA256) -> Dict[str, Any]:
        results = []
        verified = 0
        failed = 0
        for fp in file_paths:
            r = self.verify_checksum(fp, algorithm)
            results.append(r)
            if r.get("verified"):
                verified += 1
            else:
                failed += 1
        return {
            "total": len(file_paths),
            "verified": verified,
            "failed": failed,
            "results": results,
        }

    def get_stats(self) -> Dict[str, Any]:
        return {
            "checksums_computed": len(self._checksums),
            "expected_registered": len(self._expected_checksums),
            "algorithms_supported": [a.value for a in ChecksumAlgorithm],
        }
