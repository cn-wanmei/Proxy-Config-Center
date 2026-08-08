# Changelog

## [1.0.1] - 2026-08-09

发布交付方式优化 / Release distribution refinement。

### Changed
- 六端配置由 Release 单独文件直接交付，不再要求用户下载 ZIP 后再解压。
- 保留完整 ZIP 作为六端归档与离线备份。
- 增加 `latest/download/<file>` 稳定下载入口，适合客户端长期订阅。
- 固定版本继续使用 `releases/download/vX.Y.Z/<file>`，便于审计、回滚和版本锁定。
- Release workflow 对六端独立文件、完整 ZIP 统一构建、校验、Artifact 发布和 Attestation。
- Release tag 在 bootstrap 发布分支场景下指向实际发布分支提交，避免 Release 指向旧的 `main` 提交。

### Release Assets
- `clash-meta.yaml`
- `clash.yaml`
- `stash.yaml`
- `egern.yaml`
- `loon.conf`
- `shadowrocket.conf`
- `proxy-config-center-v1.0.1.zip`

### Platforms
- Clash Meta
- Clash
- Stash
- Egern
- Loon
- Shadowrocket

## [1.0.0] - 2026-08-09

首个正式稳定版本 / First Stable Release。

### Added
- Core V1：DNS 三层模型、统一策略组、规则优先级
- Strict capability schema 与完整 capability matrix
- Cross-file reference graph validation
- `rule_set` / `rule_provider` / `domain_fallback` 独立能力模型
- 六平台完整 Golden Snapshot
- Rule-source health check、缓存与可选 SHA-256 integrity pin
- Rule priority constraints 与 CI large-diff safety gate
- 六端构建 Artifact、版本校验与 Release Artifact Attestation
- GitHub Release 自动生成六端配置压缩包

### Changed
- capability engine 改为 fail-fast，不再静默降级
- Core → IR → Adapter 架构保持平台无关
- 生成的 `build/` / `final/` 不再由 CI 自动提交到 `main`
- 发布产物统一由 CI 从源码重新构建

### Platforms
- Clash Meta
- Clash
- Stash
- Egern
- Loon
- Shadowrocket

### Notes
- 节点由 Sub-Store 独立管理
- 规则与策略由 Core 统一维护
- Release Artifact 是正式六端配置的交付来源
