# Proxy-Config-Center

**通用代理配置中心 / Universal Proxy Configuration Center**  
**Version: 1.0.2 · Stable Release**

支持平台：Clash Meta · Clash · Stash · Egern · Loon · Shadowrocket

> **规则、节点组与策略组由 Core 统一维护；节点订阅由 Core 以外部资源方式接入，客户端只负责消费生成结果。**

## 发布方式 / Distribution

本项目采用 **Build Once, Distribute Artifacts**：生成配置不作为源码长期维护，而由 GitHub Actions 从 Core 构建并发布。

```text
Core → Validate → Reference → Capability → Golden
     → Platform Adapter → Six platform configs
     → Artifact / GitHub Release
```

正式版本只允许通过 `v*` Git tag 触发 Release Workflow。PR、`release/*` 分支和普通 push **不能创建或修改正式 Release**。

每个正式 Release 同时提供 **6 个独立配置文件**和一个完整 ZIP 归档：

| 平台 | 独立下载 / 稳定地址 | Release 文件 |
|------|----------------------|--------------|
| Clash Meta | `releases/latest/download/clash-meta.yaml` | `clash-meta.yaml` |
| Clash | `releases/latest/download/clash.yaml` | `clash.yaml` |
| Stash | `releases/latest/download/stash.yaml` | `stash.yaml` |
| Egern | `releases/latest/download/egern.yaml` | `egern.yaml` |
| Loon | `releases/latest/download/loon.conf` | `loon.conf` |
| Shadowrocket | `releases/latest/download/shadowrocket.conf` | `shadowrocket.conf` |

固定版本下载使用：

```text
https://github.com/cn-wanmei/Proxy-Config-Center/releases/download/v1.0.2/clash-meta.yaml
https://github.com/cn-wanmei/Proxy-Config-Center/releases/download/v1.0.2/clash.yaml
https://github.com/cn-wanmei/Proxy-Config-Center/releases/download/v1.0.2/stash.yaml
https://github.com/cn-wanmei/Proxy-Config-Center/releases/download/v1.0.2/egern.yaml
https://github.com/cn-wanmei/Proxy-Config-Center/releases/download/v1.0.2/loon.conf
https://github.com/cn-wanmei/Proxy-Config-Center/releases/download/v1.0.2/shadowrocket.conf
```

`latest/download/*` 适合客户端长期订阅；`vX.Y.Z` 适合固定版本、审计和回滚。ZIP 仅作为完整六端归档保留。

## 客户端能力 / Client Capabilities

- **节点组 / Node groups**：Core 的基础节点选择组统一映射到各客户端的策略组模型。
- **策略组 / Policy groups**：服务分流组保持稳定 ID，规则只引用策略组，不直接耦合平台语法。
- **图标 / Icons**：支持图标的客户端由 capability 显式开启并输出对应原生字段；不支持的平台不会静默伪造字段。
- **Egern**：策略组可挂载启用的远程订阅 URL，并统一使用 7 天 `update_interval`。
- **远程规则集 / Rule sources**：外部规则资源统一按 **7 天（604800 秒）**刷新。
- **Clash/Stash/其他支持 provider 的客户端**：远程节点资源同样使用 7 天刷新周期。

## 节点接入 / Node Sources

节点不进入规则匹配 Core；订阅与静态节点位于 `core/proxies/providers.yaml`，启用后由各平台 Adapter 转换。

```yaml
subscriptions:
  - id: airport-1
    name: { zh: 机场订阅1, en: Airport Sub 1 }
    url: "https://example.com/subscribe"
    enabled: true
```

默认生成器不会输出占位订阅。

## 核心能力 / Engineering Guarantees

- Strict capability schema
- Cross-file reference validation
- `rule_set` / `rule_provider` / `domain_fallback` 独立能力模型
- Node group / policy group 统一 IR
- Client-native icon emission with explicit capability gating
- Rule-source health check、缓存与可选 SHA-256 integrity pin
- External rule/proxy resources refresh every 7 days
- Rule priority constraints
- 六端完整 Golden Snapshot
- Fail-fast：核心依赖或能力缺失不会静默降级
- CI large-diff safety gate
- Version validation、Release Artifact 与 Attestation
- 六端独立 Release Asset + ZIP 完整归档
- Formal Release workflow is tag-only

## 规则覆盖 / Rules

广告、中国、Apple、AI、Google、YouTube、Spotify、Telegram、Twitter、Netflix、TikTok、游戏、E-Hentai 等；策略组与 DNS 策略统一由 Core 管理。

## 本地构建与校验 / Build & Test

```bash
python scripts/validate.py
python tests/test_capabilities.py
python tests/test_semantic.py
python tests/test_golden.py
python scripts/build.py
python scripts/check_config.py
python scripts/check_rule_sources.py
```

生成结果位于 `build/`，**禁止手工修改生成文件**。

## 架构原则 / Principles

1. **Core First** — 业务逻辑只在 `core/`
2. **Capability Driven** — 平台差异由 capability 描述
3. **Reference Safe** — 构建前检查跨文件引用
4. **Golden Protected** — 六端生成结果受回归保护
5. **Fail Fast** — 错误立即失败，不静默降级
6. **Artifact First** — 生成配置作为 CI Artifact / Release 交付
7. **Adapter First** — 新客户端原则上只增加 adapter + capability，不修改 Core
8. **Stable Distribution** — 独立文件用于实际订阅，ZIP 用于完整归档
9. **Tag-only Release** — 只有 `v*` tag 可以创建正式 Release
10. **Weekly External Refresh** — 外部规则与节点资源默认 7 天刷新

详见 `docs/` 下的架构、IR、Core V1 冻结和发布规范。
