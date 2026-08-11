# Proxy-Config-Center

**在线分流规则源、审计与确定性编译中心**  
**Version: 4.0.0**

## 定位

Core 只负责分流规则：规则源、规范化、语义分析、审计、确定性编译与在线 RAW 发布。

Core **不负责** DNS、节点、代理组、TUN、Fake-IP、完整客户端配置、客户端网络策略或客户端适配。

客户端只引用稳定的 RAW 规则 URL；项目不发布规则压缩包，不生成完整客户端配置。

```text
Core Rule Source
  ↓
Canonical Rule
  ↓
Semantic Engine
  ↓
Fail-Closed Audit
  ↓
Deterministic Compile
  ↓
rules/<policy>.yaml
  ↓
GitHub RAW
  ↓
客户端自行引用
```

## 4.0 核心原则

- **RAW First**：每个策略独立文件，稳定路径，在线直接消费。
- **Client Agnostic**：Core 永远不进入客户端配置和网络策略。
- **Canonical Identity**：Global Rule ID、Policy Scoped Rule ID、完整 SHA-256 分离。
- **Semantic Audit**：duplicate / conflict / shadow / overlap / invalid / pollution。
- **Fail-Closed**：任何阻断级审计失败都禁止发布。
- **Deterministic Build**：相同规则源必须产生字节级一致的 RAW 文件。
- **Provenance**：每条规则保留来源、策略和内容身份。
- **No Package Release**：规则不打包分发；Git 仓库本身就是在线规则源。

## RAW 规则

稳定路径采用：

```text
rules/<policy>.yaml
```

例如：

```text
https://raw.githubusercontent.com/cn-wanmei/Proxy-Config-Center/main/rules/google.yaml
```

客户端应直接引用对应策略文件，不依赖项目中的 Manifest、构建产物或完整客户端配置。

## 开发

```bash
make audit
make compile
make verify
make ci
```

本地编译默认生成到临时目录；生产 RAW 文件由通过 CI 的主分支变更生成并提交到 `rules/`。CI 会验证生成结果是否确定性、是否通过审计，以及工作区是否存在未提交的生成差异。

## 明确排除

本项目不实现：

- DNS / DNS 防泄露
- Proxy / Proxy Group
- 节点订阅与测速
- TUN / Fake-IP
- 完整客户端配置
- 客户端专用网络策略
- 规则 ZIP / TAR / Release Package
