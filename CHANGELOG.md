# Changelog

## [1.3.5] - 2026-08-09

这是我对 1.3.4 发布链路和七端客户端兼容性的全面收口。我这次重点解决两类问题：Release 不能因为旧 Tag/SHA 进入旧代码，以及 Egern 远程配置在客户端实际解析时出现 `rule_set.match` 缺失的问题。

### Fixed
- 我移除了 Release Workflow 的 `target_sha` / SHA 手工输入，发布时只需要填写版本号。
- 我取消 Tag Push 自动发布，避免历史 Tag 意外触发旧代码发布。
- 我让手动 Release 始终从当前 `main` 解析发布 Commit，SHA 只作为 Workflow 内部实现细节。
- 我严格校验 Release 版本号与仓库 `VERSION` 一致后才允许继续。
- 我修复 Egern `rule_set` 使用错误 `url` 字段的问题，统一生成原生要求的 `match` 字段。
- 我禁止 Release 客户端配置中残留 BlackMatrix 上游规则 URL。
- 我保留 `sources.yaml` 等规则源元数据中的真实 upstream provenance，不再错误地将其当作客户端配置改写。

### Validation
- 我将 Egern Golden Snapshot 提升为硬性语义门禁：`rule_set.match` 必须存在，`rule_set.url` 必须禁止，`policy` 必须属于已声明策略组。
- 我将 Egern 原生语义检查纳入七端 Semantic Matrix。
- 我要求最终 `dist/egern.yaml` 通过发布前语义验证后才能进入 Release。
- 我继续要求七端完整配置、完整规则、Manifest、Raw HTTP 200 与 SHA256 全部通过后才能完成发布。

### Release Architecture
- 我将发布入口收敛为“版本号驱动”，不再要求用户处理 Commit SHA。
- 我让 `latest-rules` 只接收经过完整 Release Gate 验证的客户端与规则。
- 我保持 7 个客户端 Raw URL、全部分流规则 Raw URL 与 Remote Rule Manifest 的稳定发布架构。
