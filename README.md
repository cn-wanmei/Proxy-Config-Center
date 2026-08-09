# Proxy-Config-Center

**通用代理配置中心 / Universal Proxy Configuration Center**  
**Version: 1.3.4 · Stable Release**

我正在维护这个项目，用它统一生成和发布 Clash Meta、Clash、Stash、Egern、Loon、Shadowrocket、sing-box 七端代理配置。

> **我负责维护 Core、规则、节点组、策略组与发布体系；各客户端只消费我生成并验证过的最终配置。**

## 发布与远程配置

我规定正式 Release 只能由 `v*` tag 触发。只有完整构建、验证和远程发布全部成功后，我才会更新 `latest-rules`。这个分支只保存我最近一次正式发布的完整客户端配置、远程规则和 Manifest。

### 7 个客户端完整配置 Raw URL

下面这些地址是我长期提供给用户的完整客户端远程配置地址。它们直接指向 `raw.githubusercontent.com`，不是 GitHub Release 下载页。

| 平台 | 我提供的 Raw 远程配置 |
|---|---|
| Clash | `https://raw.githubusercontent.com/cn-wanmei/Proxy-Config-Center/latest-rules/clients/clash.yaml` |
| Clash Meta | `https://raw.githubusercontent.com/cn-wanmei/Proxy-Config-Center/latest-rules/clients/clash-meta.yaml` |
| Stash | `https://raw.githubusercontent.com/cn-wanmei/Proxy-Config-Center/latest-rules/clients/stash.yaml` |
| Egern | `https://raw.githubusercontent.com/cn-wanmei/Proxy-Config-Center/latest-rules/clients/egern.yaml` |
| Loon | `https://raw.githubusercontent.com/cn-wanmei/Proxy-Config-Center/latest-rules/clients/loon.conf` |
| Shadowrocket | `https://raw.githubusercontent.com/cn-wanmei/Proxy-Config-Center/latest-rules/clients/shadowrocket.conf` |
| sing-box | `https://raw.githubusercontent.com/cn-wanmei/Proxy-Config-Center/latest-rules/clients/sing-box.json` |

**我建议直接保存这 7 个 Raw URL，不需要随着版本号变化而修改地址。** 我发布新的正式版本后，`latest-rules` 会自动更新，用户继续使用原地址即可。

### Release 归档

- 最新 Release：`https://github.com/cn-wanmei/Proxy-Config-Center/releases/latest`
- 当前版本：`v1.3.4`
- 当前版本 Release：`https://github.com/cn-wanmei/Proxy-Config-Center/releases/tag/v1.3.4`
- 完整 ZIP：`https://github.com/cn-wanmei/Proxy-Config-Center/releases/latest/download/proxy-config-center-v1.3.4.zip`

我保留 Release Asset 用于版本归档、审计、复现和回滚；日常远程使用优先使用上面的 Raw URL。

## Raw 远程分流规则

我统一使用下面的 Raw 基地址发布分流规则：

`https://raw.githubusercontent.com/cn-wanmei/Proxy-Config-Center/latest-rules/rules/`

### 常用规则

| 规则 | YAML Raw | LIST Raw |
|---|---|---|
| AI | `.../rule-ai.yaml` | `.../rule-ai.list` |
| Apple | `.../rule-apple.yaml` | `.../rule-apple.list` |
| China | `.../rule-china.yaml` | `.../rule-china.list` |
| Google | `.../rule-google.yaml` | `.../rule-google.list` |
| Microsoft | `.../rule-microsoft.yaml` | `.../rule-microsoft.list` |
| GitHub / Code Repo | `.../rule-code-repo.yaml` | `.../rule-code-repo.list` |
| Game | `.../rule-game.yaml` | `.../rule-game.list` |
| Netflix | `.../rule-netflix.yaml` | `.../rule-netflix.list` |
| Spotify | `.../rule-spotify.yaml` | `.../rule-spotify.list` |
| Telegram | `.../rule-telegram.yaml` | `.../rule-telegram.list` |
| TikTok | `.../rule-tiktok.yaml` | `.../rule-tiktok.list` |
| Twitter / X | `.../rule-twitter.yaml` | `.../rule-twitter.list` |
| Ad Block | `.../rule-ad-block.yaml` | `.../rule-ad-block.list` |

我会继续维护完整规则集合；上表只列出常用入口。

### 我自己维护的 3 个分流文件

下面三个文件由我手工维护内容，发布时原样同步到 `latest-rules`：

| 文件 | 我的策略定义 | Raw URL |
|---|---|---|
| `direct.list` | **DIRECT：我明确写死直连** | `https://raw.githubusercontent.com/cn-wanmei/Proxy-Config-Center/latest-rules/rules/rule-direct.list` |
| `proxy.list` | **PROXY：我明确写死代理** | `https://raw.githubusercontent.com/cn-wanmei/Proxy-Config-Center/latest-rules/rules/rule-proxy.list` |
| `ehentai.list` | **跟随其它策略组：我不在规则文件里写死 DIRECT/PROXY** | `https://raw.githubusercontent.com/cn-wanmei/Proxy-Config-Center/latest-rules/rules/rule-ehentai.list` |

源文件位置：`rules/manual/direct.list`、`rules/manual/proxy.list`、`rules/manual/ehentai.list`。

我不会让生成器擅自修改这三个文件的具体域名、IP 或 CIDR 内容。`direct` 和 `proxy` 的目标语义由我固定；`ehentai` 只提供匹配集合，命中后继续沿用 Core 的策略组逻辑。

### Manifest / 校验

- 我提供的 Remote Rule Manifest：`https://raw.githubusercontent.com/cn-wanmei/Proxy-Config-Center/latest-rules/release-manifest.json`
- 我提供的 SHA256：`https://raw.githubusercontent.com/cn-wanmei/Proxy-Config-Center/latest-rules/SHA256SUMS`

Manifest 同时记录我发布的 7 个客户端 Raw URL、全部分流规则 Raw URL、SHA-256、文件大小及发布版本。

## 新增：规则智能审计

我现在把规则系统当成可审计的数据图，而不是单纯的文本生成器。

### Rule → Strategy Group Index

我在构建时生成：

```text
build/audit/rule-strategy-index.json
build/audit/rule-strategy-index.md
```

它可以回答：

- 哪条规则来自哪个源文件；
- 哪条规则实际进入哪个策略组；
- 策略组优先级是多少；
- 每个策略组当前有多少规则。

### Rule Graph

我同时生成：

```text
build/audit/rule-graph.json
```

它记录 Rule → Strategy、duplicate、conflict、unreachable、invalid target 等关系。

出现策略冲突、不可达规则或非法策略目标时，我会直接阻止 Build，而不是把问题带进 Release。

### Rule Explain

我提供：

```bash
python scripts/explain_rule.py openai.com
```

我会直接告诉你命中的规则、源文件、优先级和最终策略组。

### 七端 Domain Semantic Matrix

我会对 Core 中的代表性服务域名建立七端语义矩阵：

```text
Clash
Clash Meta
Stash
Egern
Loon
Shadowrocket
sing-box
```

并要求同一个 Core 服务在七端仍然落到同一个语义策略组。

生成结果：

```text
build/audit/domain-semantic-matrix.json
```

## 新增：Remote Config Semantic Validation

我不再把“Raw HTTP 200”当成客户端配置有效的充分条件。

我现在同时检查：

1. 配置格式能够解析；
2. 策略组存在；
3. 规则存在；
4. 规则目标策略组存在；
5. FINAL / MATCH 兜底存在；
6. rule-provider / rule-set URL 指向 `latest-rules/rules/`；
7. sing-box `route.final` 必须指向真实 outbound；
8. 七端全部通过语义校验。

生成结果：

```text
build/audit/remote-config-semantic.json
```

## 新增：Build Report / Config Diff

每次构建我都会生成：

```text
build/audit/build-report.json
build/audit/config-diff.json
```

Build Report 记录：

- 构建时间；
- Commit；
- 7 个客户端；
- 每个生成文件 SHA256；
- 文件大小；
- Rule Audit；
- Semantic Matrix；
- Remote Config Semantic Validation。

Config Diff 用于阻止 Core / Platform 源文件出现异常大范围变化，同时保留机器可读的变更报告。

## 新增：Rule Source Cache / Integrity

我对外部规则源增加了：

```text
Retry
 ↓
24h 本地 Cache
 ↓
SHA256
 ↓
Integrity Report
```

构建时生成：

```text
build/audit/rule-source-lock.json
```

它记录实际抓取的 URL、SHA256、大小、HTTP 状态和是否命中 Cache。

这样我可以追溯某次构建到底使用了哪一份远程规则内容。

## 新增：Supply Chain / 多版本 Schema

我正式维护：

```text
common/schemas/release-manifest.schema.json
common/schemas/remote-config.schema.json
```

并生成：

```text
build/audit/supply-chain.json
```

Supply Chain Report 记录：

```text
VERSION
Commit SHA
Release Tag
Artifact SHA256
Manifest
```

目标是让任意一个正式发布的 Raw 配置都可以追溯到具体 Release 和 Git Commit。

## 客户端能力

- **节点组**：我在 Core 统一定义，再根据客户端 capability 做映射。
- **策略组**：我使用稳定服务 ID 管理分流，避免客户端规则直接耦合平台语法。
- **图标**：我通过 capability 显式控制，不支持的平台不伪造字段。
- **Egern**：我将远程资源默认刷新周期设为 7 天。
- **sing-box**：我输出原生 JSON，不把 Clash YAML/LIST 源伪装成原生 rule-set。
- **外部规则与节点资源**：我默认使用 7 天（168h / 604800 秒）刷新周期。

## 发布完整性

每次正式发布时，我要求 Release Workflow 完成：

1. 我构建 7 端完整客户端配置
2. 我构建全部已定义分流规则
3. 我检查 `direct / proxy / ehentai` 用户维护规则
4. 我执行 Rule Audit / Capability / Semantic / Golden / Structural
5. 我执行 Remote Config Semantic Validation
6. 我执行 Rule Conflict / Unreachable Graph
7. 我执行七端 Domain Semantic Matrix
8. 我生成 Build Report / Source Integrity / Supply Chain Report
9. 我检查 Release Asset 完整性
10. 我更新 `latest-rules/clients/`
11. 我更新 `latest-rules/rules/`
12. 我更新 `release-manifest.json`
13. 我逐个验证客户端 Raw HTTP 200，并校验 SHA256
14. 我逐个验证全部规则 Raw HTTP 200，并校验 SHA256
15. 我验证 Raw Manifest 与本次构建 Manifest 完全一致

**任何 Release 失败、普通 push 或 PR，都不能污染我的 `latest-rules`。**

## 本地构建与校验

我在本地使用下面的命令完成核心验证：

```bash
python scripts/validate.py
python scripts/rule_audit.py --write
python scripts/rule_graph.py --write
python tests/test_rule_intelligence.py
python tests/test_capabilities.py
python tests/test_semantic.py
python tests/test_platform_semantics.py
python scripts/build.py --include-final
python scripts/validate_remote_configs.py --root build --write
python scripts/semantic_matrix.py --root build --write
python scripts/check_config.py --root build
python scripts/check_config.py --root final
python scripts/check_rule_sources.py --write
python scripts/build_report.py
python scripts/supply_chain.py --root build --write
python scripts/config_diff.py --write
python tests/test_remote_configs.py
python tests/test_golden.py
```

我将生成结果放在 `build/`；`final/` 只用于 legacy compatibility，我不允许手工修改生成文件。

## 我的架构原则

1. **Core First** — 我把业务逻辑集中在 `core/`
2. **Capability Driven** — 我用 capability 描述平台差异
3. **Reference Safe** — 我在构建前检查跨文件引用
4. **Golden Protected** — 我用 Golden 保护生成结果
5. **Fail Fast** — 我要求错误立即失败，不接受静默降级
6. **Artifact First** — 我把配置作为 CI Artifact / Release 交付
7. **Adapter First** — 我新增客户端时优先只增加 adapter + capability
8. **Raw Distribution** — 我同时提供完整客户端配置和全部分流规则的 `latest-rules` Raw URL
9. **Semantic Distribution** — 我要求远程配置不仅可下载，还必须语义有效
10. **Rule Intelligence** — 我让规则具备索引、解释、冲突和可达性分析能力
11. **Seven-platform Equivalence** — 我要求七端保持 Core 语义一致
12. **Supply Chain Traceability** — 我让 Release、Manifest、Artifact、SHA256 和 Commit 可以相互追溯
13. **Tag-only Release** — 我只允许 `v*` tag 创建正式 Release
14. **Weekly External Refresh** — 我将外部规则与节点资源默认刷新周期设为 7 天
15. **Release Gate** — 我只有在正式 Release 全部验证成功后才更新 `latest-rules`
