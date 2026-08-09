# Proxy-Config-Center

**通用代理配置中心 / Universal Proxy Configuration Center**  
**Version: 1.3.2 · Stable Release**

支持平台：Clash Meta · Clash · Stash · Egern · Loon · Shadowrocket · sing-box

> **规则、节点组与策略组由 Core 统一维护；客户端只消费生成结果。**

## 发布与远程配置

正式 Release 只由 `v*` tag 触发。发布成功并完成全部验证后，Release Workflow 才会更新 `latest-rules`。该分支只保存最近一次正式发布的完整客户端配置、远程规则和 Manifest。

### 7 个客户端完整配置 Raw URL

以下地址可以直接作为客户端的远程配置/订阅配置地址，内容为完整生成配置，不是 GitHub 下载页：

| 平台 | Raw 远程配置 |
|---|---|
| Clash | `https://raw.githubusercontent.com/cn-wanmei/Proxy-Config-Center/latest-rules/clients/clash.yaml` |
| Clash Meta | `https://raw.githubusercontent.com/cn-wanmei/Proxy-Config-Center/latest-rules/clients/clash-meta.yaml` |
| Stash | `https://raw.githubusercontent.com/cn-wanmei/Proxy-Config-Center/latest-rules/clients/stash.yaml` |
| Egern | `https://raw.githubusercontent.com/cn-wanmei/Proxy-Config-Center/latest-rules/clients/egern.yaml` |
| Loon | `https://raw.githubusercontent.com/cn-wanmei/Proxy-Config-Center/latest-rules/clients/loon.conf` |
| Shadowrocket | `https://raw.githubusercontent.com/cn-wanmei/Proxy-Config-Center/latest-rules/clients/shadowrocket.conf` |
| sing-box | `https://raw.githubusercontent.com/cn-wanmei/Proxy-Config-Center/latest-rules/clients/sing-box.json` |

**长期使用这 7 个 Raw URL 即可。** 新正式版本发布后，`latest-rules` 自动更新，客户端无需修改地址。

### Release 归档

- 最新 Release：`https://github.com/cn-wanmei/Proxy-Config-Center/releases/latest`
- 当前版本：`v1.3.2`
- 当前版本 Release：`https://github.com/cn-wanmei/Proxy-Config-Center/releases/tag/v1.3.2`
- 完整 ZIP：`https://github.com/cn-wanmei/Proxy-Config-Center/releases/latest/download/proxy-config-center-v1.3.2.zip`

Release Asset 用于版本归档、审计、复现和回滚；客户端长期订阅使用上面的 Raw URL。

## Raw 远程分流规则

统一基地址：

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

将上表中的 `...` 替换为统一基地址即可。

### 用户维护的 3 个分流文件

这三个文件由用户自己维护内容，Release 时原样同步到 `latest-rules`：

| 文件 | 固定策略语义 | Raw URL |
|---|---|---|
| `direct.list` | **DIRECT：写死直连** | `https://raw.githubusercontent.com/cn-wanmei/Proxy-Config-Center/latest-rules/rules/rule-direct.list` |
| `proxy.list` | **PROXY：写死代理** | `https://raw.githubusercontent.com/cn-wanmei/Proxy-Config-Center/latest-rules/rules/rule-proxy.list` |
| `ehentai.list` | **跟随其它策略组：不写死 DIRECT/PROXY** | `https://raw.githubusercontent.com/cn-wanmei/Proxy-Config-Center/latest-rules/rules/rule-ehentai.list` |

源文件位置：`rules/manual/direct.list`、`rules/manual/proxy.list`、`rules/manual/ehentai.list`。

其中 `direct` 与 `proxy` 的目标语义固定；`ehentai` 只提供匹配集合，命中后沿用 Core 的策略组选择逻辑。三个文件的具体域名/IP 内容不由生成器擅自补充。

### Manifest / 校验

- Remote Rule Manifest：`https://raw.githubusercontent.com/cn-wanmei/Proxy-Config-Center/latest-rules/release-manifest.json`
- SHA256：`https://raw.githubusercontent.com/cn-wanmei/Proxy-Config-Center/latest-rules/SHA256SUMS`

Manifest 同时记录 7 个客户端 Raw URL、全部规则 Raw URL、SHA-256、大小及发布版本。

## 客户端能力

- **节点组**：Core 统一定义，按客户端 capability 映射。
- **策略组**：服务分流组使用稳定 ID，规则不直接耦合平台语法。
- **图标**：由 capability 显式控制，不支持的平台不伪造字段。
- **Egern**：远程资源默认 7 天更新。
- **sing-box**：输出原生 JSON；不把 Clash YAML/LIST 源伪装成原生 rule-set。
- **外部规则与节点资源**：默认 7 天（168h / 604800 秒）刷新。

## 发布完整性

Release Workflow 必须完成：

1. 7 端完整配置构建
2. 全部分流规则构建
3. `direct / proxy / ehentai` 用户规则存在性检查
4. Rule Audit / Capability / Semantic / Golden / Structural
5. Release Asset 完整性检查
6. 更新 `latest-rules/clients/`
7. 更新 `latest-rules/rules/`
8. 更新 `release-manifest.json`
9. Raw 客户端配置 HTTP 200 + SHA256 校验
10. Raw 全部规则 HTTP 200 + SHA256 校验

**Release 失败、普通 push、PR 均不得更新 `latest-rules`。**

## 本地构建与校验

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

生成结果位于 `build/`；`final/` 仅用于 legacy compatibility，禁止手工修改生成文件。

## 架构原则

1. **Core First** — 业务逻辑只在 `core/`
2. **Capability Driven** — 平台差异由 capability 描述
3. **Reference Safe** — 构建前检查跨文件引用
4. **Golden Protected** — 生成结果受回归保护
5. **Fail Fast** — 错误立即失败，不静默降级
6. **Artifact First** — 配置作为 CI Artifact / Release 交付
7. **Adapter First** — 新客户端原则上只增加 adapter + capability
8. **Raw Distribution** — 客户端完整配置与全部分流规则均提供 `latest-rules` Raw URL
9. **Tag-only Release** — 只有 `v*` tag 可以创建正式 Release
10. **Weekly External Refresh** — 外部规则与节点资源默认 7 天刷新
11. **Release Gate** — 只有正式 Release 全部验证成功后才能更新 `latest-rules`
