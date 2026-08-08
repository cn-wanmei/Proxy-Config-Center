# Release v1.0.2 / 发布规范

## 正式发布模型

项目采用 **Artifact-first** 发布：`main` 保存源码、Core、Adapter、测试与发布工作流；六端生成配置由 GitHub Actions 构建后作为 Artifact 和 GitHub Release 资产交付。

```text
Core → Validate → Reference → Capability → Golden
     → Renderer → Build → Structural Check → Rule Source Health
     → Six independent assets + ZIP archive
     → GitHub Release + Attestation
```

## 正式 Release 触发边界

正式 Release Workflow **只接受 `v*` Git tag push**：

```text
Pull Request       → 普通 CI 验证，不创建 Release
release/* branch   → 普通 CI 验证，不创建 Release
main push          → 普通 CI 验证，不创建 Release
v1.0.2 tag         → Release Workflow → Build → Release
```

Release Job 会从触发它的 tag commit checkout，并首先验证：

```text
Tag vX.Y.Z
    ==
VERSION X.Y.Z
```

版本不一致时立即 Fail-fast，后续 Build / Pack / Release 全部停止。

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

## 外部资源更新周期

规则源和远程节点订阅默认统一采用 **7 天（604800 秒）**刷新周期。

- Rule Set / Rule Provider：7 天
- Clash / Stash 等远程 Proxy Provider：7 天
- Egern policy group 外部订阅：7 天
- 客户端自身的节点测速/健康检查仍由客户端能力模型独立控制，不与资源下载周期混用

## 客户端规则能力

- Core 统一生成节点组与策略组语义。
- Clash Meta / Stash 使用原生 `icon` 字段。
- Egern 使用 policy group 原生 `icon`。
- Loon 使用 Proxy Group 原生 `img-url`。
- Shadowrocket 使用 Proxy Group 原生 `icon-url`。
- 不支持某能力的平台由 Capability 显式关闭，禁止静默输出无效字段。

## 版本规则

- 唯一版本源：根目录 `VERSION`
- Release Tag：`v<version>`
- Tag 版本必须与 `VERSION` 一致
- Release 不直接接受手工修改的生成配置
- 独立文件与 ZIP 必须来自同一次 CI Build
- Release Artifact 必须经过结构检查、Rule Source Health 与 Attestation
