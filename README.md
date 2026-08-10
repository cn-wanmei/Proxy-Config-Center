# Proxy-Config-Center

**通用代理配置编译器 / Universal Proxy Configuration Compiler**  
**Version: 2.0.0**

从「配置文件仓库」升级为：

```text
Policy → Canonical IR → Security Engine + Capability Engine → Compiler → Platforms
```

输出 Clash Meta / Clash / Stash / Egern / Loon / Shadowrocket / sing-box。

---

## 编译管线（Core V2）

```text
                 Policy (core/)
                      │
                      ▼
                Canonical IR
                      │
           ┌──────────┴──────────┐
           ▼                     ▼
    Security Engine        Capability Engine
           │                     │
           └──────────┬──────────┘
                      ▼
                   Compiler
                      │
        ┌────────────┴────────────┐
        ▼             ▼             ▼
      Clash         Loon          Egern  …
```

- **Security Engine**：禁止 System DNS、禁止明文 UDP/53 nameserver、强制 fake-ip / DoH
- **Capability Engine**：平台能力不足时禁止静默降级
- **Compiler**：生成后二次解析校验（`verify_emit`）
- **DNS Leak CI**：`tests/test_dns_leak.py` + `make security`

---

## DNS 安全策略（强制）

| 规则 | 要求 |
|------|------|
| System DNS | **禁止** |
| 明文 DNS / UDP 53 作为 nameserver | **禁止**（bootstrap IP 仅用于解析 DoH 主机名） |
| enhanced-mode | **fake-ip** |
| proxy-server-nameserver | **必须**（DoH） |
| fallback + fallback-filter | **必须** |
| nameserver-policy | **必须** |
| IPv4 / IPv6 | bootstrap 与 `dns.ipv6` 显式处理 |

---

## 本地 CI

```bash
make install
make security
make validate
make test
make ci
```

`make ci` = security → validate → audit → test → golden → check → verify_emit

---

## 架构原则

1. Policy First
2. Security Before Compile
3. No Silent Degradation
4. Capability Driven
5. Tag-only Release
6. DNS Leak Resistant
