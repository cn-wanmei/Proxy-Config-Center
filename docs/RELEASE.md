# Release v1.0.0 / 发布规范

## 正式发布模型

项目采用 **Artifact-first** 发布：`main` 保存源码、Core、Adapter、测试与发布工作流；六端生成配置由 GitHub Actions 构建后作为 Artifact 和 GitHub Release 资产交付。

```text
Core → Validate → Reference → Capability → Golden
     → Renderer → Build → Structural Check
     → ZIP Artifact → GitHub Release
```

## 正常发布

具备 Git Tag 写权限时：

```bash
bash scripts/release.sh 1.0.0
```

脚本会完成校验、构建、提交 `VERSION` 并推送 `v1.0.0`；Release workflow 随 tag 自动运行。

## 无 Tag 写权限时

仓库提供受控的 `release/vX.Y.Z` 发布分支作为 bootstrap 入口。该分支由维护者/自动化创建，Release workflow 可从该分支构建并创建对应 `vX.Y.Z` Release；发布完成后再将发布分支合并回 `main`。

该机制只用于解决 GitHub App 无法创建 Tag 的权限限制，不改变正常的 Tag 发布模型。

## Release 产物

正式 Release ZIP 内固定包含：

```text
configs/
├── clash-meta/config.yaml
├── clash/config.yaml
├── stash/config.yaml
├── egern/config.yaml
├── loon/config.conf
└── shadowrocket/config.conf
```

同时上传 Actions Artifact，并生成 Artifact Attestation。

## 版本规则

- 唯一版本源：根目录 `VERSION`
- Release Tag：`v<version>`
- Tag 版本必须与 `VERSION` 一致
- Release 不直接接受手工修改的生成配置
