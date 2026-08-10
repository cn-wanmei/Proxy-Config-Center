# Proxy-Config-Center

**通用代理配置编译器 / Universal Proxy Configuration Compiler**  
**Version: 2.1.0**

```text
                  CORE
                   |
                   v
             Schema Validation
                   |
                   v
             Canonical IR
                   |
          +--------+--------+
          v                 v
   Security Engine    Rule Engine
          |                 |
          +--------+--------+
                   v
             Optimizer
                   |
                   v
          Capability Resolver
                   |
                   v
             Platform IR
                   |
     Clash / Loon / Egern / SR / sing-box
                   |
                   v
           Reverse Validation
                   |
                   v
             Golden Test
                   |
                   v
            Release Artifact
```

## 2.1

| Module | Path |
|--------|------|
| Security Policy | `core/security/policy.yaml` |
| Platform IR | `scripts/platform_ir.py` |
| Compiler Pipeline | `scripts/compiler.py` |
| Rule Normalization | `scripts/engines/rule_normalize.py` |
| Artifact Immutability | `scripts/artifact_immutability.py` |
| Integration Test | `tests/test_integration_2_1.py` |

```bash
make compile
make ci
```
