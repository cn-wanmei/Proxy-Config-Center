# Proxy-Config-Center

**Universal Proxy Configuration Compiler**  
**Version: 2.1.0**

```text
CORE → Schema → Canonical IR → Security + Rule Engine → Optimizer
  → Capability → Platform IR → Emit → Reverse Validate → Golden
  → Release Tag Gate (immutable) → Release Artifact
```

## 2.1 Modules

| Module | Path |
|--------|------|
| Security Policy | `core/security/policy.yaml` |
| Platform IR | `scripts/platform_ir.py` |
| Compiler | `scripts/compiler.py` |
| Rule Normalize | `engines/rule_normalize.py` |
| Optimizer | `engines/optimizer.py` |
| Release Tag Gate | `scripts/release_tag_gate.py` |
| Artifact Pins | `scripts/artifact_immutability.py` |
| Integration | `tests/test_integration_2_1.py` |

```bash
make compile
make release_tag_gate
make ci
```

Release: tag must match VERSION; existing tags are immutable.
