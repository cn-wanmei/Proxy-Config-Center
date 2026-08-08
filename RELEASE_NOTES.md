# v1.0.0 Release Notes

## 中文

首个正式稳定版本。

- 六平台最终配置：Clash Meta / Clash / Stash / Egern / Loon / Shadowrocket
- Core V1 DNS 三层模型与统一策略组
- 完整分流规则：广告、中国、Apple、AI、Google、YouTube、Spotify、Telegram、Twitter、Netflix、TikTok、游戏、E-Hentai 等
- 六端 Golden Snapshot、Capability Matrix、Reference Validator
- Rule-source 健康检查、缓存与可选 SHA-256 完整性校验
- CI 从 Core 构建并发布六端 Artifact / Release
- 节点仍由 Sub-Store 独立管理

## English

First stable release.

- Final configurations for Clash Meta / Clash / Stash / Egern / Loon / Shadowrocket
- Core V1 DNS model and unified strategy groups
- Complete routing rules for ads, China, Apple, AI, Google, YouTube, Spotify, Telegram, Twitter, Netflix, TikTok, games, E-Hentai and more
- Full six-platform Golden Snapshot, capability matrix and reference validation
- Rule-source health checks, cache and optional SHA-256 integrity pins
- CI builds and distributes six-platform artifacts/releases from Core
- Nodes remain managed independently by Sub-Store

## Release Artifact

The official release archive contains:

```text
configs/
├── clash-meta/config.yaml
├── clash/config.yaml
├── stash/config.yaml
├── egern/config.yaml
├── loon/config.conf
└── shadowrocket/config.conf
```

Generated configs are not maintained as source files on `main`.
