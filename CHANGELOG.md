# Changelog

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
