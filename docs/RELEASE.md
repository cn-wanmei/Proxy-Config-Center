# Release v1.0.1 / 发布规范

## 正式发布模型

项目采用 **Artifact-first** 发布：`main` 保存源码、Core、Adapter、测试与发布工作流；六端生成配置由 GitHub Actions 构建后作为 Artifact 和 GitHub Release 资产交付。

```text
Core → Validate → Reference → Capability → Golden
     → Renderer → Build → Structural Check
     → Six independent assets + ZIP archive
     → GitHub Release + Attestation
```

## Release 产物

每个正式 Release 固定提供六个独立文件，作为实际使用和订阅入口：

```text
clash-meta.yaml
clash.yaml
stash.yaml
egern.yaml
loon.conf
shadowrocket.conf
```

同时保留完整 ZIP：

```text
proxy-config-center-vX.Y.Z.zip
└── configs/
    ├── clash-meta/config.yaml
    ├── clash/config.yaml
    ├── stash/config.yaml
    ├── egern/config.yaml
    ├── loon/config.conf
    └── shadowrocket/config.conf
```

独立文件的固定版本地址格式：

```text
https://github.com/cn-wanmei/Proxy-Config-Center/releases/download/vX.Y.Z/clash-meta.yaml
https://github.com/cn-wanmei/Proxy-Config-Center/releases/download/vX.Y.Z/clash.yaml
https://github.com/cn-wanmei/Proxy-Config-Center/releases/download/vX.Y.Z/stash.yaml
https://github.com/cn-wanmei/Proxy-Config-Center/releases/download/vX.Y.Z/egern.yaml
https://github.com/cn-wanmei/Proxy-Config-Center/releases/download/vX.Y.Z/loon.conf
https://github.com/cn-wanmei/Proxy-Config-Center/releases/download/vX.Y.Z/shadowrocket.conf
```

长期订阅使用 `latest`：

```text
https://github.com/cn-wanmei/Proxy-Config-Center/releases/latest/download/clash-meta.yaml
https://github.com/cn-wanmei/Proxy-Config-Center/releases/latest/download/clash.yaml
https://github.com/cn-wanmei/Proxy-Config-Center/releases/latest/download/stash.yaml
https://github.com/cn-wanmei/Proxy-Config-Center/releases/latest/download/egern.yaml
https://github.com/cn-wanmei/Proxy-Config-Center/releases/latest/download/loon.conf
https://github.com/cn-wanmei/Proxy-Config-Center/releases/latest/download/shadowrocket.conf
```

## 正常发布

具备 Git Tag 写权限时：

```bash
bash scripts/release.sh X.Y.Z
```

脚本会完成校验、构建、提交 `VERSION` 并推送 `vX.Y.Z`；Release workflow 随 tag 自动运行。

## 无 Tag 写权限时

仓库提供受控的 `release/vX.Y.Z` 发布分支作为 bootstrap 入口。该分支由维护者/自动化创建，Release workflow 从发布分支构建并创建对应 `vX.Y.Z` Release，Release tag 指向发布分支实际提交；发布完成后再将发布分支合并回 `main`。

该机制只用于解决 GitHub App 无法创建 Tag 的权限限制，不改变正常的 Tag 发布模型。

## 版本规则

- 唯一版本源：根目录 `VERSION`
- Release Tag：`v<version>`
- Tag 版本必须与 `VERSION` 一致
- Release 不直接接受手工修改的生成配置
- 独立文件与 ZIP 必须来自同一次 CI Build
- Release Artifact 必须经过结构检查与 Attestation
