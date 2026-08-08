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
│   ├── config/
│   │   ├── base.yaml           # 基础设置 / Base settings
│   │   ├── dns.yaml            # DNS 架构 / DNS architecture
│   │   └── runtime.yaml        # 运行时设置 / Runtime settings
│   ├── proxy-groups/
│   │   ├── base.yaml           # 代理模式等基础策略组 / Base strategy groups
│   │   └── service.yaml        # 分流策略组 / Service strategy groups
│   ├── rules/
│   │   ├── priority.yaml       # 规则优先级 / Rule priority
│   │   └── services/           # 按服务拆分的规则 / Service-specific rules
│   └── advertising/            # 广告拦截逻辑 / Ad blocking logic
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
│   ├── icons/                  # 官方高清图标 / Official high-quality icons
│   ├── assets/
│   └── schemas/                # JSON Schema 验证 / JSON Schema validation
├── docs/                       # 文档（中英双语） / Documentation (Chinese-English)
└── .github/workflows/          # CI / 构建自动化 / CI / Build automation
```

## 设计原则 / Design Principles

1. **Core First** — 所有逻辑只在 `core/` 中维护 / All logic lives only in `core/`
2. **Platform-agnostic** — Core 只存语义，不存任何平台语法 / Core stores only semantics, no platform syntax
3. **No Nodes** — 节点由 Sub-Store 管理 / Nodes are handled by Sub-Store
4. **Unified Strategy** — 一套策略组适配所有平台 / One set of strategy groups for all platforms
5. **Easy Maintenance** — 修改 Core 一次，重建即可更新全部平台 / Change core once, rebuild all platforms

## 当前状态 / Current Status

- platforms/ 结构已完成
- core/ 已按最新设计重建
- 基础策略组与分流策略组语义已写入
- 下一步：完善规则与 DNS，开始编写 Adapter
