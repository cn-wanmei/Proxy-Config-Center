# Proxy-Config-Center

**通用代理配置中心 / Universal Proxy Configuration Center**  
**Version: 1.6.2**

统一生成并发布 Clash Meta、Clash、Stash、Egern、Loon、Shadowrocket、sing-box 七端代理配置。

Core、规则、策略组与发布体系在本仓库维护；各客户端只消费经过验证的最终配置。

---

## 快速使用

### 七端完整配置 Raw URL（推荐）

直接保存以下地址，版本更新后无需修改：

| 平台 | Raw URL |
|------|---------|
| Clash | https://raw.githubusercontent.com/cn-wanmei/Proxy-Config-Center/latest-rules/clients/clash.yaml |
| Clash Meta | https://raw.githubusercontent.com/cn-wanmei/Proxy-Config-Center/latest-rules/clients/clash-meta.yaml |
| Stash | https://raw.githubusercontent.com/cn-wanmei/Proxy-Config-Center/latest-rules/clients/stash.yaml |
| Egern | https://raw.githubusercontent.com/cn-wanmei/Proxy-Config-Center/latest-rules/clients/egern.yaml |
| Loon | https://raw.githubusercontent.com/cn-wanmei/Proxy-Config-Center/latest-rules/clients/loon.conf |
| Shadowrocket | https://raw.githubusercontent.com/cn-wanmei/Proxy-Config-Center/latest-rules/clients/shadowrocket.conf |
| sing-box | https://raw.githubusercontent.com/cn-wanmei/Proxy-Config-Center/latest-rules/clients/sing-box.json |

### 分流规则基地址

```
https://raw.githubusercontent.com/cn-wanmei/Proxy-Config-Center/latest-rules/rules/
```

常用规则：

| 规则 | YAML | LIST |
|------|------|------|
| AI | rule-ai.yaml | rule-ai.list |
| Apple | rule-apple.yaml | rule-apple.list |
| China | rule-china.yaml | rule-china.list |
| Google | rule-google.yaml | rule-google.list |
| Microsoft | rule-microsoft.yaml | rule-microsoft.list |
| GitHub / Code Repo | rule-code-repo.yaml | rule-code-repo.list |
| Game | rule-game.yaml | rule-game.list |
| Netflix | rule-netflix.yaml | rule-netflix.list |
| Spotify | rule-spotify.yaml | rule-spotify.list |
| Telegram | rule-telegram.yaml | rule-telegram.list |
| TikTok | rule-tiktok.yaml | rule-tiktok.list |
| Twitter / X | rule-twitter.yaml | rule-twitter.list |
| Ad Block | rule-ad-block.yaml | rule-ad-block.list |

### 手工维护规则

| 文件 | 语义 | Raw URL |
|------|------|---------|
| direct.list | 明确直连 | .../rule-direct.list |
| proxy.list | 明确代理 | .../rule-proxy.list |
| ehentai.list | 仅匹配集合，跟随策略组 | .../rule-ehentai.list |

源文件位于 `rules/manual/`。生成器不会修改这些文件的具体域名、IP 或 CIDR。

### Manifest 与校验

- Manifest：https://raw.githubusercontent.com/cn-wanmei/Proxy-Config-Center/latest-rules/release-manifest.json
- SHA256：https://raw.githubusercontent.com/cn-wanmei/Proxy-Config-Center/latest-rules/SHA256SUMS

---

## 架构

采用 **Core First + IR + Capability + Adapter + Artifact** 架构。

```
Core
 ↓ Schema / Semantic Validation
 ↓ Reference Graph
 ↓ Resolved IR
 ↓ Capability Engine
 ↓ Platform Adapter / Renderer
 ↓ 七端配置
 ↓ Golden + Structural Check
 ↓ Artifact / Release
```

- `core/`：唯一业务语义来源（规则、DNS、策略组、服务、优先级）
- `scripts/ir.py`：编译为平台无关 ResolvedIR
- `scripts/engines/`：capability、规则源、引用约束
- `platforms/`：各端 capability 与 renderer
- `build/`：临时生成目录，非稳定接口

节点由 Sub-Store 独立管理，本仓库不负责节点订阅生命周期。

详细说明见 `docs/架构说明.md`。

---

## 规则智能审计

构建时生成：

```
build/audit/rule-strategy-index.json
build/audit/rule-strategy-index.md
build/audit/rule-graph.json
```

可查询：

- 规则来源文件
- 最终策略组
- 优先级
- 重复 / 冲突 / 不可达 / 非法目标

```bash
python scripts/explain_rule.py openai.com
```

出现策略冲突、不可达规则或非法目标时直接阻止 Build。

七端 Domain Semantic Matrix 确保同一 Core 服务在各端落到相同语义策略组。

---

## Remote Config 语义校验

不仅检查 Raw HTTP 200，还验证：

1. 配置可解析
2. 策略组存在
3. 规则存在且目标策略组有效
4. FINAL / MATCH 兜底存在
5. rule-provider / rule-set 指向 `latest-rules/rules/`
6. sing-box `route.final` 指向真实 outbound
7. 七端全部通过语义校验

---

## 发布流程

正式 Release 仅由 `v*` tag 触发。

Release Workflow 必须完成：

1. 构建七端完整客户端配置
2. 构建全部分流规则
3. 检查 direct / proxy / ehentai 手工规则
4. Rule Audit / Capability / Semantic / Golden / Structural
5. Remote Config Semantic Validation
6. Rule Conflict / Unreachable Graph
7. 七端 Domain Semantic Matrix
8. Build Report / Source Integrity / Supply Chain Report
9. Release Asset 完整性检查
10. 更新 `latest-rules/clients/` 与 `latest-rules/rules/`
11. 更新 `release-manifest.json`
12. 客户端与规则 Raw HTTP 200 + SHA256 校验
13. Manifest 一致性校验

任何失败、普通 push 或 PR 都不会污染 `latest-rules`。

Release Asset 用于归档、审计、复现和回滚；日常使用优先 Raw URL。

---

## 本地构建与校验

```bash
make install          # 安装依赖
make validate         # Core + capability + reference + rule audit
make audit            # 规则审计并写 index
make test             # 单元测试
make golden           # Golden 测试
make check            # 结构检查
make ci               # 完整 CI 链路
```

或手动：

```bash
python scripts/validate.py
python scripts/rule_audit.py --write
python scripts/build.py --include-final
python scripts/check_config.py --root build
python tests/test_golden.py
```

生成结果位于 `build/`。`final/` 仅作 legacy 兼容，禁止手工修改。

---

## 架构原则

1. **Core First** — 业务逻辑集中在 `core/`
2. **Capability Driven** — 平台差异由 capability 描述
3. **Reference Safe** — 构建前检查跨文件引用
4. **Golden Protected** — Golden 保护生成结果
5. **Fail Fast** — 错误立即失败，不接受静默降级
6. **Artifact First** — 配置作为 CI Artifact / Release 交付
7. **Adapter First** — 新客户端优先只增加 adapter + capability
8. **Raw Distribution** — 同时提供完整客户端与分流规则 Raw URL
9. **Semantic Distribution** — 远程配置必须语义有效
10. **Rule Intelligence** — 规则具备索引、解释、冲突与可达性分析
11. **Seven-platform Equivalence** — 七端保持 Core 语义一致
12. **Supply Chain Traceability** — Release / Manifest / Artifact / SHA256 / Commit 可相互追溯
13. **Tag-only Release** — 仅 `v*` tag 触发正式发布
14. **Weekly External Refresh** — 外部规则与节点资源默认 7 天刷新
15. **Release Gate** — 全部验证通过后才更新 `latest-rules`

---

## 版本与变更

详见 [CHANGELOG.md](CHANGELOG.md)。
