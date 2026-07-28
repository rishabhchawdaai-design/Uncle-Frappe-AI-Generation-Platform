---
module: "security_crypto"
type: module-doc
status: active
owner: ""
lines: 444
classes: 11
functions: 0
tags: [module, documentation]
generated: "2026-07-28"
---

# security_crypto

> Security Crypto Layer — Encryption at Rest, In Transit, Model Integrity.

Based on ACOS Research: Security Canon §5-6
Provides encryption, TLS verification, and model checksum validation.

SEC-05: Enc

## Overview

- **File**: `ai_generation/security_crypto.py`
- **Lines**: 444
- **Classes**: 11
- **Public Functions**: 0

## Classes

- `{{EncryptionAlgorithm}}`
- `{{KeyDerivationMethod}}`
- `{{ChecksumAlgorithm}}`
- `{{TLSVersion}}`
- `{{EncryptionKey}}`
- `{{EncryptedPayload}}`
- `{{FileChecksum}}`
- `{{TLSVerification}}`
- `{{EncryptionAtRest}}`
- `{{EncryptionInTransit}}`
- `{{ModelSecurity}}`

## Integration

- Part of the [[Architecture Overview|Unified AI Generation Platform]]
- Exposed via [[05-SDK/SDK Overview|SDK]] and [[06-MCP-Ecosystem/MCP Ecosystem Overview|MCP Tools]]
- Verified in [[02-Capability-Registry/Capability Registry Overview|Capability Registry]]

## Related

- [[Architecture Overview]]
- [[Capability Registry Overview]]
