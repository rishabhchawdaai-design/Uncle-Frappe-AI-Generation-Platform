---
type: overview
module: security
status: active
tags: [security, overview]
---

# Security Overview

## Security Components

| Component | Module | Purpose |
|-----------|--------|---------|
| SecurityManager | `security.py` | RBAC, access control |
| ProcessSandbox | `security.py` | Process isolation |
| EncryptionAtRest | `security_crypto.py` | Data encryption |
| EncryptionInTransit | `security_crypto.py` | TLS/SSL |
| ModelSecurity | `security_crypto.py` | Model integrity |
| SecretScanner | `code_analysis.py` | Secret detection |

## Security Scan Results

```dataview
TABLE pattern_name, severity, file_path
FROM "36-Generated"
WHERE type = "secret-finding"
SORT severity DESC
```

## Related

- [[Architecture Overview]]
- [[Quality Engineering Overview]]
- [[Failure Atlas Overview]]
