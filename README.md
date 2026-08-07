# Proxy-Config-Center

**通用代理配置中心 / Universal Proxy Configuration Center**

支持平台 / Supported Platforms：
- Clash Meta (mihomo)
- Clash
- Loon
- Egern
- Stash
- Shadowrocket

> **节点由 Sub-Store 独立管理，本仓库不包含任何节点订阅。**  
> **Nodes are managed independently via Sub-Store. This repository contains no node subscriptions.**

## 目录结构 / Directory Structure

```
Proxy-Config-Center/
├── core/                       # ★ 核心逻辑（唯一数据源） / Core logic (Single Source of Truth)
│   ├── strategy/               # 统一策略组 / Unified strategy groups
│   ├── rules/                  # 统一规则 / Unified rules
│   ├── dns/                    # 统一 DNS 架构 / Unified DNS architecture
│   ├── advertising/            # 广告拦截逻辑 / Ad blocking logic
│   └── config-base.yaml        # 基础配置 / Base settings (IPv6, TUN, etc.)
├── platforms/                  # 平台适配层 / Platform adapters
│   ├── clash-meta/
│   ├── clash/
│   ├── loon/
│   ├── egern/
│   ├── stash/
│   └── shadowrocket/
├── build/                      # 自动生成配置（禁止手动修改） / Auto-generated configs (do not edit)
├── scripts/                    # 构建与更新脚本 / Build & update scripts
├── common/
│   └── icons/                  # 官方高清图标 / Official high-quality icons
├── docs/                       # 文档（中英双语） / Documentation (Chinese-English)
└── .github/workflows/          # CI / 构建自动化 / CI / Build automation
```

## 设计原则 / Design Principles

1. **Core First** — 所有逻辑只在 `core/` 中维护 / All logic lives only in `core/`
2. **No Nodes** — 节点由 Sub-Store 管理 / Nodes are handled by Sub-Store
3. **Unified Strategy** — 一套策略组适配所有平台 / One set of strategy groups for all platforms
4. **Easy Maintenance** — 修改 Core 一次，重建即可更新全部平台 / Change core once, rebuild all platforms

## 当前状态 / Current Status

骨架已创建完成，下一步将编写核心策略组定义。  
Skeleton created. Next step: write core strategy group definitions.
