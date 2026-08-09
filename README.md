# Proxy-Config-Center

**通用代理配置中心 / Universal Proxy Configuration Center**  
**Version: 1.1.0 · Next Stable Release**

支持平台：Clash Meta · Clash · Stash · Egern · Loon · Shadowrocket · sing-box

> **规则、节点组与策略组由 Core 统一维护；节点订阅由 Core 以外部资源方式接入，客户端只负责消费生成结果。**

## 发布方式 / Distribution

本项目采用 **Build Once, Distribute Artifacts**：生成配置不作为源码长期维护，而由 GitHub Actions 从 Core 构建并发布。

```text
Core → Validate → Reference → Capability → Golden
     → Platform Adapter → Seven platform configs
     → Artifact / GitHub Release
```

正式版本只允许通过 `v*` Git tag 触发 Release Workflow。PR、`release/*` 分支和普通 push **不能创建或修改正式 Release**。

每个正式 Release 同时提供 **7 个独立配置文件**和一个完整 ZIP 归档：

| 平台 | 独立下载 / 稳定地址 | Release 文件 |
|------|----------------------|--------------|
| Clash Meta | `releases/latest/download/clash-meta.yaml` | `clash-meta.yaml` |
| Clash | `releases/latest/download/clash.yaml` | `clash.yaml` |
| Stash | `releases/latest/download/stash.yaml` | `stash.yaml` |
| Egern | `releases/latest/download/egern.yaml` | `egern.yaml` |
| Loon | `releases/latest/download/loon.conf` | `loon.conf` |
| Shadowrocket | `releases/latest/download/shadowrocket.conf` | `shadowrocket.conf` |
| sing-box | `releases/latest/download/sing-box.json` | `sing-box.json` |

固定版本下载使用对应 `vX.Y.Z` 路径。`latest/download/*` 适合客户端长期订阅；固定版本适合审计和回滚。ZIP 仅作为完整归档保留。

## 客户端能力 / Client Capabilities

- **节点组 / Node groups**：Core 的基础节点选择组统一映射到各客户端的策略组模型。
- **策略组 / Policy groups**：服务分流组保持稳定 ID，规则只引用策略组，不直接耦合平台语法。
- **图标 / Icons**：支持图标的客户端由 capability 显式开启并输出对应原生字段；不支持的平台不会静默伪造字段。
- **Egern**：策略组可挂载启用的远程订阅 URL，并统一使用 7 天 `update_interval`。
- **sing-box**：输出原生 JSON，使用 selector/urltest 出站组与 route rules；当前 Core 的 Clash YAML/LIST 外部规则源不会被伪装成 sing-box 原生 rule-set，而是安全降级为域名规则。
- **远程规则集 / Rule sources**：外部规则资源统一按 **7 天（168h / 604800 秒）**刷新。
- **节点资源**：显式节点按客户端原生 outbound 类型转换；订阅 URL 保持由原生支持 provider 的客户端处理。

## 核心能力 / Engineering Guarantees

- Strict capability schema + explicit platform registry
- Cross-file reference validation
- `rule_set` / `rule_provider` / `domain_fallback` 独立能力模型
- Node / node-group / policy-group / icon 统一 IR
- Client-native icon emission with explicit capability gating
- Rule-source health check、缓存与可选 SHA-256 integrity pin
- External rule/proxy resources refresh every 7 days
- Rule priority constraints
- Golden regression + platform-specific invariants
- Fail-fast：核心依赖或能力缺失不会静默降级
- CI large-diff safety gate
- Version validation、Release Artifact 与 Attestation
- 7 个独立 Release Asset + ZIP 完整归档
- Formal Release workflow is tag-only

## 本地构建与校验 / Build & Test

```bash
python scripts/validate.py
python tests/test_capabilities.py
python tests/test_semantic.py
python tests/test_golden.py
python scripts/build.py --include-final
python scripts/check_config.py --root build
python scripts/check_config.py --root final
python scripts/check_rule_sources.py
```

生成结果位于 `build/`；`final/` 仅用于 legacy compatibility，**禁止手工修改生成文件**。

## 架构原则 / Principles

1. **Core First** — 业务逻辑只在 `core/`
2. **Capability Driven** — 平台差异由 capability 描述
3. **Reference Safe** — 构建前检查跨文件引用
4. **Golden Protected** — 生成结果受回归保护
5. **Fail Fast** — 错误立即失败，不静默降级
6. **Artifact First** — 生成配置作为 CI Artifact / Release 交付
7. **Adapter First** — 新客户端原则上只增加 adapter + capability，不修改 Core
8. **Stable Distribution** — 独立文件用于实际订阅，ZIP 用于完整归档
9. **Tag-only Release** — 只有 `v*` tag 可以创建正式 Release
10. **Weekly External Refresh** — 外部规则与节点资源默认 7 天刷新

详见 `docs/` 下的架构、IR、Core V1 冻结和发布规范。
