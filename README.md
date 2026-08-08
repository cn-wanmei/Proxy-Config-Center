# Proxy-Config-Center

**通用代理配置中心 / Universal Proxy Configuration Center**  
**Version: 1.0.0 · 首个正式版本 / First Stable Release**

支持平台：Clash Meta · Clash · Stash · Egern · Loon · Shadowrocket

> **规则与策略由 Core 统一维护；节点由 Sub-Store 独立管理。**

## 发布方式 / Distribution

本项目采用 **Build Once, Distribute Artifacts**：生成配置不作为源码长期维护，而由 GitHub Actions 从 Core 构建并发布。

```text
Core → Validate → Reference → Capability → Golden
     → Platform Adapter → Six platform configs
     → Artifact / GitHub Release
```

正式版本使用 `v*` 标签发布。Release 包包含六个平台的最终配置：

| 平台 | Release 内文件 |
|------|----------------|
| Clash Meta | `configs/clash-meta/config.yaml` |
| Clash | `configs/clash/config.yaml` |
| Stash | `configs/stash/config.yaml` |
| Egern | `configs/egern/config.yaml` |
| Loon | `configs/loon/config.conf` |
| Shadowrocket | `configs/shadowrocket/config.conf` |

CI 同时保留构建 Artifact，正式 Release 由同一构建链生成，避免源码与发布产物漂移。

## 节点接入 / Node Sources

节点不进入 Core 规则系统，由 Sub-Store 或客户端自行管理。

本地构建：

```bash
pip install -r requirements.txt
python scripts/validate.py
python scripts/build.py
```

## 核心能力 / Engineering Guarantees

- Strict capability schema
- Cross-file reference validation
- `rule_set` / `rule_provider` / `domain_fallback` 独立能力模型
- Rule-source health check、缓存与可选 SHA-256 integrity pin
- Rule priority constraints
- 六端完整 Golden Snapshot
- Fail-fast：核心依赖或能力缺失不会静默降级
- CI large-diff safety gate
- Version validation、Release Artifact 与 Attestation

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

详见 `docs/` 下的架构、IR、Core V1 冻结和发布规范。
