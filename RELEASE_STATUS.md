# v1.0.0 Release Status

**目标：首个正式稳定版本 / First Stable Release**

## 发布链

```text
release/v1.0.0
    ↓
GitHub Actions
    ↓
Validate → Tests → Build → Structural Check
    ↓
Six-platform ZIP Artifact
    ↓
GitHub Release v1.0.0
```

正式 Release 包含：

- Clash Meta
- Clash
- Stash
- Egern
- Loon
- Shadowrocket

## 发布原则

- `main` 不长期保存生成配置
- Release Artifact 是六端正式配置的交付来源
- Release 必须由同一套 CI 构建链生成
- 版本号以根目录 `VERSION` 为唯一来源
- 发布产物生成后通过 Artifact Attestation 保护来源与完整性

## v1.0.0

代码基线：Core V1 + P0–P3 工程化升级。

六端构建、Golden Snapshot、Capability、Reference、Semantic、Structural Check 已通过。
