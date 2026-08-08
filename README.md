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
    url: "https://example.com/your-subscribe-link"   # ⬅️ 改这里
    interval: 86400
    enabled: true

nodes:
  - name: "我家VPS"
    type: ss
    server: "1.2.3.4"
    port: 443
    cipher: aes-128-gcm
    password: "pass"
    enabled: true   # ⬅️ 打开后进入配置
```

然后重新构建：

```bash
pip install pyyaml
python scripts/build.py
```

---

## 最终配置目录 / Final configs

构建后直接使用：

```
final/
├── README.md
├── clash-meta/config.yaml
├── clash/config.yaml
├── stash/config.yaml
├── egern/config.yaml
├── loon/config.conf
└── shadowrocket/config.conf
```

（`build/` 为同内容中间产物，`final/` 为交付目录）

| 客户端 | 路径 |
|--------|------|
| Clash Meta | `final/clash-meta/config.yaml` |
| Clash | `final/clash/config.yaml` |
| Stash | `final/stash/config.yaml` |
| Egern | `final/egern/config.yaml` |
| Loon | `final/loon/config.conf` |
| Shadowrocket | `final/shadowrocket/config.conf` |

Clash / Meta / Stash 配置内已预留：

- `proxy-providers` ← 订阅链接（`YOUR_SUBSCRIBE_URL_*` 占位）
- `proxies` ← 单/多节点列表
- `proxy-groups` 中「手动选择 / 自动选择 / 定向免流」自动引用上述节点与订阅

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
python tests/test_semantic.py
python tests/test_golden.py
python scripts/build.py
python scripts/check_config.py
```

## 设计原则

1. Core First — 逻辑只在 `core/`
2. 订阅/节点与策略分离 — `core/proxies/providers.yaml`
3. 改一次 Core，六端一起重建
