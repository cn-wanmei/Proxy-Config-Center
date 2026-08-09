# Proxy-Config-Center

**通用代理配置中心 / Universal Proxy Configuration Center**  
**Version: 1.3.2 · Stable Release**

支持平台：Clash Meta · Clash · Stash · Egern · Loon · Shadowrocket · sing-box

> **规则、节点组与策略组由 Core 统一维护；节点订阅由 Core 以外部资源方式接入，客户端只负责消费生成结果。**

## 发布与配置地址 / Distribution

本项目采用 **Build Once, Distribute Artifacts**：配置由 GitHub Actions 从 Core 构建并发布。正式版本只允许通过 `v*` Git tag 触发 Release Workflow；PR、普通 push 和 `release/*` 分支不能创建正式 Release。

### 7 端完整配置地址

以下地址均指向 **GitHub 最新正式 Release**，适合客户端长期订阅。发布新正式版本后，`latest` 会自动切换到新版本，客户端无需修改地址。

| 平台 | 文件 | 最新正式配置地址 |
|------|------|------------------|
| Clash Meta | `clash-meta.yaml` | `https://github.com/cn-wanmei/Proxy-Config-Center/releases/latest/download/clash-meta.yaml` |
| Clash | `clash.yaml` | `https://github.com/cn-wanmei/Proxy-Config-Center/releases/latest/download/clash.yaml` |
| Stash | `stash.yaml` | `https://github.com/cn-wanmei/Proxy-Config-Center/releases/latest/download/stash.yaml` |
| Egern | `egern.yaml` | `https://github.com/cn-wanmei/Proxy-Config-Center/releases/latest/download/egern.yaml` |
| Loon | `loon.conf` | `https://github.com/cn-wanmei/Proxy-Config-Center/releases/latest/download/loon.conf` |
| Shadowrocket | `shadowrocket.conf` | `https://github.com/cn-wanmei/Proxy-Config-Center/releases/latest/download/shadowrocket.conf` |
| sing-box | `sing-box.json` | `https://github.com/cn-wanmei/Proxy-Config-Center/releases/latest/download/sing-box.json` |

> **说明：** 上表是客户端“完整配置”的长期订阅地址，属于 Release Asset 地址，不是 Raw 地址。规则资源则统一使用下面的 `raw.githubusercontent.com/latest-rules` 地址。

### 当前正式版本

- 当前版本：`v1.3.2`
- 最新 Release：`https://github.com/cn-wanmei/Proxy-Config-Center/releases/latest`
- 当前版本 Release：`https://github.com/cn-wanmei/Proxy-Config-Center/releases/tag/v1.3.2`
- 完整 ZIP：`https://github.com/cn-wanmei/Proxy-Config-Center/releases/latest/download/proxy-config-center-v1.3.2.zip`
- Remote Rule Manifest：`https://raw.githubusercontent.com/cn-wanmei/Proxy-Config-Center/latest-rules/release-manifest.json`

固定版本用于审计、复现和回滚；`latest` 用于客户端长期订阅。ZIP 仅作为完整归档保留。

## Raw 远程规则 / Raw Remote Rules

远程规则不使用 Release 下载地址，而使用专用 `latest-rules` 分支提供 Raw 内容。该分支只允许正式 Release Workflow 更新。

**统一 Raw 基地址：**

`https://raw.githubusercontent.com/cn-wanmei/Proxy-Config-Center/latest-rules/rules/`

常用规则地址：

| 规则 | YAML Raw | LIST Raw |
|------|----------|----------|
| AI | `https://raw.githubusercontent.com/cn-wanmei/Proxy-Config-Center/latest-rules/rules/rule-ai.yaml` | `https://raw.githubusercontent.com/cn-wanmei/Proxy-Config-Center/latest-rules/rules/rule-ai.list` |
| Apple | `https://raw.githubusercontent.com/cn-wanmei/Proxy-Config-Center/latest-rules/rules/rule-apple.yaml` | `https://raw.githubusercontent.com/cn-wanmei/Proxy-Config-Center/latest-rules/rules/rule-apple.list` |
| China | `https://raw.githubusercontent.com/cn-wanmei/Proxy-Config-Center/latest-rules/rules/rule-china.yaml` | `https://raw.githubusercontent.com/cn-wanmei/Proxy-Config-Center/latest-rules/rules/rule-china.list` |
| Google | `https://raw.githubusercontent.com/cn-wanmei/Proxy-Config-Center/latest-rules/rules/rule-google.yaml` | `https://raw.githubusercontent.com/cn-wanmei/Proxy-Config-Center/latest-rules/rules/rule-google.list` |
| Microsoft | `https://raw.githubusercontent.com/cn-wanmei/Proxy-Config-Center/latest-rules/rules/rule-microsoft.yaml` | `https://raw.githubusercontent.com/cn-wanmei/Proxy-Config-Center/latest-rules/rules/rule-microsoft.list` |
| Code Repo / GitHub | `https://raw.githubusercontent.com/cn-wanmei/Proxy-Config-Center/latest-rules/rules/rule-code-repo.yaml` | `https://raw.githubusercontent.com/cn-wanmei/Proxy-Config-Center/latest-rules/rules/rule-code-repo.list` |
| Game | `https://raw.githubusercontent.com/cn-wanmei/Proxy-Config-Center/latest-rules/rules/rule-game.yaml` | `https://raw.githubusercontent.com/cn-wanmei/Proxy-Config-Center/latest-rules/rules/rule-game.list` |
| Netflix | `https://raw.githubusercontent.com/cn-wanmei/Proxy-Config-Center/latest-rules/rules/rule-netflix.yaml` | `https://raw.githubusercontent.com/cn-wanmei/Proxy-Config-Center/latest-rules/rules/rule-netflix.list` |
| Spotify | `https://raw.githubusercontent.com/cn-wanmei/Proxy-Config-Center/latest-rules/rules/rule-spotify.yaml` | `https://raw.githubusercontent.com/cn-wanmei/Proxy-Config-Center/latest-rules/rules/rule-spotify.list` |
| Telegram | `https://raw.githubusercontent.com/cn-wanmei/Proxy-Config-Center/latest-rules/rules/rule-telegram.yaml` | `https://raw.githubusercontent.com/cn-wanmei/Proxy-Config-Center/latest-rules/rules/rule-telegram.list` |
| TikTok | `https://raw.githubusercontent.com/cn-wanmei/Proxy-Config-Center/latest-rules/rules/rule-tiktok.yaml` | `https://raw.githubusercontent.com/cn-wanmei/Proxy-Config-Center/latest-rules/rules/rule-tiktok.list` |
| Twitter / X | `https://raw.githubusercontent.com/cn-wanmei/Proxy-Config-Center/latest-rules/rules/rule-twitter.yaml` | `https://raw.githubusercontent.com/cn-wanmei/Proxy-Config-Center/latest-rules/rules/rule-twitter.list` |
| Ad Block | `https://raw.githubusercontent.com/cn-wanmei/Proxy-Config-Center/latest-rules/rules/rule-ad-block.yaml` | `https://raw.githubusercontent.com/cn-wanmei/Proxy-Config-Center/latest-rules/rules/rule-ad-block.list` |

完整规则清单及 SHA-256：

`https://raw.githubusercontent.com/cn-wanmei/Proxy-Config-Center/latest-rules/release-manifest.json`

校验文件：

`https://raw.githubusercontent.com/cn-wanmei/Proxy-Config-Center/latest-rules/SHA256SUMS`

> `latest-rules` 只在正式 Release 成功并完成完整资产校验后更新。Release 失败、PR 或普通 push 不会污染该分支。

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
- Rule conflict / unreachable-rule audit
- Golden regression + platform-specific invariants
- Fail-fast：核心依赖或能力缺失不会静默降级
- CI large-diff safety gate
- Version validation、Release Artifact 与 Attestation
- 7 个独立 Release Asset + ZIP 完整归档
- `latest-rules` Raw remote rule distribution
- Raw HTTP 200 + SHA-256 consistency verification
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
8. **Stable Distribution** — 客户端完整配置使用 `releases/latest/download/*`；远程规则使用 `latest-rules` Raw
9. **Tag-only Release** — 只有 `v*` tag 可以创建正式 Release
10. **Weekly External Refresh** — 外部规则与节点资源默认 7 天刷新
11. **Raw Release Gate** — 只有正式 Release 完成后才能更新 `latest-rules`

详见 `docs/` 下的架构、IR、Core V1 冻结和发布规范。
