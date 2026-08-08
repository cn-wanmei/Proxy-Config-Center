# Proxy-Config-Center

**通用代理配置中心 / Universal Proxy Configuration Center**  
**Version: 1.0.0**

支持平台 / Supported Platforms：
- Clash Meta (mihomo)
- Clash
- Loon
- Egern
- Stash
- Shadowrocket

> **节点由 Sub-Store 独立管理，本仓库不包含任何节点订阅。**  
> **Nodes are managed independently via Sub-Store.**

## 快速获取配置 / Get configs

```bash
git clone https://github.com/cn-wanmei/Proxy-Config-Center.git
cd Proxy-Config-Center
pip install pyyaml
python scripts/build.py
```

生成目录 / Output：

| 平台 | 文件 |
|------|------|
| Clash Meta | `build/clash-meta/config.yaml` |
| Clash | `build/clash/config.yaml` |
| Stash | `build/stash/config.yaml` |
| Egern | `build/egern/config.yaml` |
| Loon | `build/loon/config.conf` |
| Shadowrocket | `build/shadowrocket/config.conf` |

也可从 GitHub Actions Artifact 下载（每次 push 自动构建）。

## 已包含 / Included

- 16 个分流策略组 + 代理模式（手动/自动/免流/直连/阻断）
- 完整规则：广告、中国、苹果、AI、谷歌、油管、Spotify、Telegram、Twitter、Netflix、TikTok、游戏、E-Hentai 等
- 图标：ClashTools 高清 CDN（22 组）
- DNS 策略：苹果→系统、中国→阿里、谷歌→Google、流媒体→CF 等
- CI：validate + semantic/golden test + build + release

## 构建与校验 / Build & Test

```bash
python scripts/validate.py
python tests/test_semantic.py
python tests/test_golden.py
python scripts/build.py
python scripts/check_config.py
```

## 发版 / Release

```bash
git tag v1.0.0
git push origin v1.0.0
```

## 设计原则 / Principles

1. Core First — 逻辑只在 `core/`
2. Platform-agnostic — Core 无平台语法
3. No Nodes — Sub-Store 管节点
4. Unified Strategy — 一套策略全平台
