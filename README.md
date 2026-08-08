# Proxy-Config-Center

**通用代理配置中心 / Universal Proxy Configuration Center**  
**Version: 1.0.0**

支持平台：Clash Meta · Clash · Stash · Egern · Loon · Shadowrocket

---

## 三种节点接入方式 / Node sources

| 方式 | 说明 | 配置位置 |
|------|------|----------|
| **机场订阅** | 一个或多个订阅链接 | `core/proxies/providers.yaml` → `subscriptions` |
| **单节点** | 手写一个节点 | `core/proxies/providers.yaml` → `nodes`（`enabled: true`） |
| **多节点** | 手写多个节点 | 同上，追加多条 |
| **Sub-Store** | 外部注入（可选） | 客户端 / Sub-Store 自行对接 |

### 填写示例

编辑 `core/proxies/providers.yaml`：

```yaml
subscriptions:
  - id: airport-1
    name: { zh: 机场订阅1, en: Airport Sub 1 }
    url: "https://example.com/your-subscribe-link"
    interval: 86400
    enabled: true

nodes:
  - name: "我家VPS"
    type: ss
    server: "1.2.3.4"
    port: 443
    cipher: aes-128-gcm
    password: "pass"
    enabled: true
```

然后重新构建：

```bash
pip install -r requirements.txt
python scripts/validate.py
python scripts/build.py
```

---

## 构建与交付 / Build & Distribution

`build/` 和 `final/` 是生成目录，不再由 CI 自动提交回仓库。

```text
Core → Validate → IR → Platform Adapter → build/ → Artifact / Release
```

本地如仍需要旧的 `final/` 交付目录，可执行：

```bash
python scripts/build.py --include-final
```

GitHub Actions 会在验证通过后上传 `build/` Artifact；正式版本通过 `v*` 标签生成 Release，并自动生成 Release Notes。

| 客户端 | 构建文件 |
|--------|----------|
| Clash Meta | `build/clash-meta/config.yaml` |
| Clash | `build/clash/config.yaml` |
| Stash | `build/stash/config.yaml` |
| Egern | `build/egern/config.yaml` |
| Loon | `build/loon/config.conf` |
| Shadowrocket | `build/shadowrocket/config.conf` |

---

## 策略与规则

- 16 个分流策略组 + 代理模式（手动 / 自动 / 免流 / 直连 / 阻断）
- 中国连接、苹果服务默认 **直连**；广告默认 **REJECT**
- 规则覆盖：AI、谷歌、油管、Spotify、Telegram、Twitter、Netflix、TikTok、游戏、E-Hentai 等
- 图标：ClashTools CDN
- DNS：苹果→系统、中国→阿里、谷歌→Google、流媒体→CF

---

## 构建与校验

```bash
python scripts/validate.py
python tests/test_capabilities.py
python tests/test_semantic.py
python tests/test_golden.py
python scripts/build.py
python scripts/check_config.py
python scripts/check_rule_sources.py
```

## 设计原则

1. **Core First** — 业务逻辑只在 `core/`
2. **Capability Driven** — 平台差异由 `capabilities.yaml` 描述，不在 Core 中硬编码
3. **Reference Safe** — 构建前验证跨文件引用和规则优先级
4. **Golden Protected** — 六个平台的完整生成结果受 Golden Snapshot 保护
5. **Fail Fast** — 缺失能力、引用断链或构建异常直接失败，不静默降级
6. **Build Once, Distribute Artifacts** — CI 构建并发布 Artifact，不回写生成配置
7. **改一次 Core，六端一起重建**
