# Proxy-Config-Center

**Universal Proxy Configuration Compiler**  
**Version: 2.2.0**

> Architecture: **cannot emit insecure configuration**.

```text
CORE → Schema → IR → Security + Rule → Optimizer
  → Capability → Platform IR → Secure Adapter Emit → Artifact
```

## 2.2 Kernel

| Capability | Module |
|------------|--------|
| Secure-by-construction DNS | `engines/secure_types.py` |
| Dynamic policy | `engines/dynamic_policy.py` |
| Resolver scheduler | `engines/resolver_scheduler.py` |
| Incremental compile | `engines/incremental.py` |
| Platform abstraction | `engines/platform_adapter.py` |

```bash
make compile
PROXY_POLICY_PROFILE=strict make compile
PROXY_FORCE_BUILD=1 make compile
make ci
```
