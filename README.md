# Proxy-Config-Center

**在线分流规则源、审计与确定性编译中心**  
**Version: 4.0.0**

## 4.0 定位

4.0 不再把“策略”当成单一扁平文件，而是采用：

```text
独立客户端
└── 总规则集
    ├── Google 总策略
    │   ├── Google
    │   ├── YouTube
    │   ├── GooglePlay
    │   ├── GoogleFCM
    │   └── YouTubeMusic
    ├── Apple 总策略
    ├── Microsoft 总策略
    ├── GitHub 总策略
    └── ...
```

**客户端、总规则集、总策略、子策略四层完全分离。**

例如 Loon 的正式 RAW 输出：

```text
rules/
└── Loon/
    └── Global/
        ├── Global.list
        ├── Google/
        │   ├── Google.list
        │   ├── YouTube.list
        │   ├── GooglePlay.list
        │   ├── GoogleFcm.list
        │   └── YoutubeMusic.list
        ├── Apple/
        │   └── Apple.list
        ├── Microsoft/
        │   └── Microsoft.list
        └── ...
```

### RAW URL 示例

```text
https://raw.githubusercontent.com/cn-wanmei/Proxy-Config-Center/main/rules/Loon/Global/Google/Google.list
https://raw.githubusercontent.com/cn-wanmei/Proxy-Config-Center/main/rules/Loon/Global/Google/YouTube.list
https://raw.githubusercontent.com/cn-wanmei/Proxy-Config-Center/main/rules/Loon/Global/Google/GooglePlay.list
```

这种目录组织参考了 `blackmatrix7/ios_rule_script` 对不同客户端独立生成规则、按服务分类并通过 RAW URL 消费的模式；其 Loon 规则目录本身也是以具体服务目录和 `.list` 文件为核心。citeturn0view0turn1search1

## Core 职责

Core 只负责：

- 规则源
- 服务规则
- 总策略关系
- 总规则集关系
- 规范化
- 语义审计
- 确定性编译
- 客户端格式输出
- 在线 RAW 发布

Core 不负责：

- DNS
- DNS 防泄露
- 节点
- Proxy Group
- TUN
- Fake-IP
- Resolver
- 完整客户端配置
- 客户端网络策略

## 4.0 数据模型

```text
core/
├── clients/
│   └── loon.yaml
│
└── rules/
    ├── services/
    │   ├── google.yaml
    │   ├── youtube.yaml
    │   ├── google-play.yaml
    │   └── ...
    │
    ├── policies/
    │   └── google.yaml
    │
    └── collections/
        └── global.yaml
```

### Service

最底层规则单元，例如：

```text
YouTube
GooglePlay
GoogleFCM
```

### Policy

把多个 Service 组成一个总策略：

```text
Google
├── Google
├── YouTube
├── GooglePlay
├── GoogleFCM
└── YouTubeMusic
```

### Collection

把多个总策略组成一个总规则集：

```text
Global
├── Google
├── Apple
├── Microsoft
├── GitHub
└── ...
```

### Client

只定义**输出格式**，不改变 Core 规则语义：

```text
Loon
└── .list
```

4.0 首个正式客户端输出为 Loon。

## Loon RAW 格式

Loon 的 Remote Rule 使用独立 `.list` 文件，策略由客户端的 Remote Rule 配置指定，因此 RAW 文件只保存匹配规则，不把代理节点、策略组、DNS 等客户端配置塞进规则文件。公开的 Loon 配置示例也采用 RAW `.list` 作为 Remote Rule 数据源。citeturn1search2turn1search9

示例：

```text
# NAME: Google
# TOTAL: 2
DOMAIN-SUFFIX,google.com
DOMAIN-SUFFIX,googleapis.com
```

## 发布原则

```text
Rule Source
    ↓
Semantic Audit
    ↓
Fail-Closed Gate
    ↓
Client Compiler
    ↓
Loon RAW
    ↓
GitHub main
    ↓
客户端在线引用
```

**不发布 ZIP / TAR / 完整客户端配置。**

## 稳定 URL 原则

客户端使用稳定路径：

```text
rules/Loon/Global/Google/Google.list
rules/Loon/Global/Google/YouTube.list
rules/Loon/Global/Google/GooglePlay.list
```

版本升级不改变 URL；Git 历史负责版本追踪，需要固定历史版本时使用对应 Git commit，而不是重新生成版本目录。

## 开发

```bash
make audit
make compile
make verify
make test
make ci
```

任何阻断级审计错误都会阻止 RAW 生成。相同 Core 输入必须产生字节级一致的 RAW 输出。
