# Changelog

## [1.3.4] - 2026-08-09

Raw 客户端配置与远程规则发布架构修复 / Raw client configuration and remote-rule distribution fix。

### Fixed
- 修复 Release Workflow 无法可靠创建或更新 `latest-rules` 分支的问题。
- 正式 Release 后实际同步 7 个完整客户端配置到 `latest-rules/clients/`。
- Manifest 为 7 个客户端补齐 `latest_url`、SHA256 与文件大小。
- 发布后逐项验证客户端与全部分流规则 Raw URL HTTP 200。
- 发布后逐项校验 Raw 内容 SHA256 与 Release 构建产物一致。
- 七端客户端配置统一引用 `latest-rules/rules/` 的稳定 Raw 分流规则地址。

### Added
- 7 个客户端稳定 Raw 远程配置入口：Clash、Clash Meta、Stash、Egern、Loon、Shadowrocket、sing-box。
- Manifest 同时描述客户端与全部分流规则 Raw URL。
- 用户维护规则：`direct.list`、`proxy.list`、`ehentai.list`。

### Manual Rules
- `direct.list`：固定 DIRECT。
- `proxy.list`：固定 PROXY。
- `ehentai.list`：不写死 DIRECT/PROXY，沿用 Core 策略组逻辑。

### Validation
- Release 构建必须生成 7 个客户端文件。
- Release 必须生成完整规则集合与 Manifest。
- `latest-rules/clients/*` 与 `latest-rules/rules/*` 必须全部 HTTP 200。
- Raw 内容 SHA256 必须与本次 Release 构建产物完全一致。
- Raw Manifest 必须与本次构建 Manifest 完全一致。

## [1.3.2] - 2026-08-09

Raw 远程规则分发架构 / Raw remote-rule distribution architecture。

### Added
- 新增 `latest-rules` 专用发布分支，仅承载经过正式 Release 验证的最终规则资源。
- 七端客户端远程规则统一改用 `raw.githubusercontent.com` Raw 地址，不再使用 GitHub Release `latest/download` 下载地址。
- Release Workflow 在正式 Release 成功后自动刷新 `latest-rules`，确保远程规则只跟随最新正式版本。
- 新增 Raw Remote Rule Manifest，记录规则资产、Raw URL、SHA256、大小与来源版本。
- Release 后逐个 HTTP 200 检查 Raw 远程规则，并校验远程内容 SHA256 与本次发布资产一致。

## [1.3.1] - 2026-08-09

远程规则分发修复 / Latest remote-rule distribution fix。

### Added
- Release Workflow 将完整生成规则逐个作为 GitHub Release Asset 发布。
- `release-manifest.json` 为每个客户端与规则资产生成 `latest/download/<asset>` 稳定地址、SHA256 与文件大小。
- 新增远程规则 HTTP 200 验证器，正式 Release 创建后逐一检查所有 latest 资产。
- 新增远程规则发布规范文档，明确 latest 只跟随正式 Release。

### Changed
- 支持远程规则集的平台改为引用 GitHub Releases latest asset。
- 远程规则缓存周期继续保持 7 天。
- 完整发行包仍保留 7 端客户端、完整规则、Manifest、SHA256 与 ZIP。

### Fixed
- 修复 1.3.0 发布后规则虽然进入 ZIP / Release，却没有形成可直接订阅的独立 latest 远程规则资产的问题。
- Release 成功后若任一 latest 客户端或规则 URL 非 HTTP 200，发布 Job 明确失败，避免产生不可用的远程订阅。

## [1.3.0] - 2026-08-09

完整客户端与远程规则发布体系 / Complete client and remote-rule release distribution。

### Added
- 正式 Release 同步发布全部 7 个客户端完整配置：Clash、Clash Meta、Stash、Egern、Loon、Shadowrocket、sing-box。
- 正式 Release 同步发布完整规则资源目录，包括规则服务文件、优先级定义、规则源定义及相关规则元数据。
- Release Artifact 与 GitHub Release 同时保留客户端配置、完整规则目录、Manifest、SHA256 校验信息和 ZIP 归档。
