# Changelog

## [1.6.0] - 2026-08-09

这是我对整个项目 v1.3–v1.6 路线的最终工程化收口。我这次不再继续堆叠客户端数量，而是把发布确定性、规则工程化、AI Provider 管理和供应链完整性统一到同一条可验证流水线上。

### v1.3 稳定化
- 我让 Release 从当前 `main` 自动解析唯一 source commit，发布入口只接受版本号。
- 我取消 Tag Push 自动发布，避免历史 Tag/SHA 进入旧代码。
- 我将正式 Release 设置为不可覆盖；已存在版本会直接触发 immutable gate。
- 我将最终客户端配置重新执行 Remote Config Semantic Validation，并在发布后做 Raw HTTP 200 + SHA256 E2E 校验。
- 我增加 Build Report、Source Snapshot、Release Manifest 和供应链报告。

### v1.4 规则工程化
- 我建立 Rule Index 与 Rule Graph 的机器可读输出。
- 我加入 Rule Explain 基础能力，可按精确 match 查询规则来源。
- 我加入重复/冲突候选检测与 unreachable 候选报告。
- 我保留七端 Semantic Matrix，并将平台原生语义作为发布门禁。
- 我让 Domain → Rule → Match 的关系可以被机器索引和后续可视化工具直接消费。

### v1.5 AI Provider 平台化
- 我建立 AI Provider Registry，将 Provider、Service、Domain、Strategy 解耦。
- 我加入 AI Coverage Matrix 输出。
- 我将 Google / Microsoft / GitHub 的服务边界作为独立 Provider 维度，避免按顶级域名粗暴归类。
- 我为 Provider Diff 保留稳定的机器可读 Registry 数据基础。

### v1.6 供应链
- 我增加 Rule Source Snapshot，记录规则源内容 SHA256 和大小。
- 我增加可复现构建基础：锁定依赖、固定 source commit、统一 `SOURCE_DATE_EPOCH`。
- 我增加 CycloneDX 风格 SBOM。
- 我增加 Schema Version Manifest，为后续 Schema v2 演进保留兼容边界。
- 我让 Release Manifest 同时记录 source commit、generator commit、schema version 和远程资源完整性。

### Release Gate
- 我要求 Validate → Capability → Semantic → Seven-platform Semantic → Build → Golden → Structural → Source Health → Engineering Reports → Release Distribution Contract → Immutable Release → latest-rules → Raw E2E Integrity 全链路通过后才能发布。
- 我坚持 7 个客户端、全部分流规则、Manifest、Raw URL 和 SHA256 必须保持一致。
