# Changelog

## [1.3.4] - 2026-08-09

这是我对远程客户端配置与远程规则发布体系的一次正式收口。我这次重点解决的是“Release 有文件，但客户端真正访问 Raw 地址时不一定能拿到完整配置”的发布链路问题。

### Fixed
- 我修复了 Release Workflow 无法可靠创建或更新 `latest-rules` 分支的问题。
- 我确保正式 Release 成功后，7 个完整客户端配置实际同步到 `latest-rules/clients/`。
- 我为 7 个客户端补齐 `latest_url`、SHA256 和文件大小。
- 我让七端客户端配置统一引用 `latest-rules/rules/` 的稳定 Raw 分流规则地址。
- 我增加发布后的 Raw HTTP 200 校验，避免出现 Release 成功但远程地址不可用的情况。
- 我增加 Raw 内容 SHA256 与本次 Release 构建产物的一致性校验。
- 我增加 Raw Manifest 与本次构建 Manifest 的最终一致性校验。
- 我修复了 `latest-rules` 已经包含相同发布内容时，Workflow 因 `nothing to commit` 而错误失败的问题。

### Added
- 我正式提供 7 个客户端稳定 Raw 远程配置入口：Clash、Clash Meta、Stash、Egern、Loon、Shadowrocket、sing-box。
- 我让 Manifest 同时描述客户端和全部分流规则的 Raw URL。
- 我增加并纳入发布体系的用户维护规则：`direct.list`、`proxy.list`、`ehentai.list`。

### Manual Rules
- `direct.list`：我将它定义为固定 DIRECT。
- `proxy.list`：我将它定义为固定 PROXY。
- `ehentai.list`：我不在文件中写死 DIRECT/PROXY，让它沿用 Core 的策略组逻辑。
- 这三个文件的具体域名、IP、CIDR 内容由我手工维护，生成器不会擅自补充或覆盖。

### Validation
- 我要求 Release 必须生成 7 个客户端完整配置。
- 我要求 Release 必须生成完整规则集合和 Manifest。
- 我要求 `latest-rules/clients/*` 与 `latest-rules/rules/*` 全部通过 HTTP 200。
- 我要求所有 Raw 内容 SHA256 与本次 Release 构建产物完全一致。
- 我要求 Raw Manifest 与本次构建 Manifest 完全一致。

## [1.3.2] - 2026-08-09

我建立了 `latest-rules` 专用发布分支，让正式版本与稳定远程规则分发彻底分离。

### Added
- 我新增 `latest-rules` 专用发布分支，仅承载经过正式 Release 验证的最终规则资源。
- 我把七端客户端远程规则统一改为 `raw.githubusercontent.com` Raw 地址，不再依赖 GitHub Release `latest/download`。
- 我让 Release Workflow 只在正式 Release 成功后刷新 `latest-rules`。
- 我新增 Raw Remote Rule Manifest，记录规则资产、Raw URL、SHA256、大小与来源版本。
- 我让 Release 后逐个 HTTP 200 检查 Raw 远程规则，并校验远程内容 SHA256 与发布资产一致。

## [1.3.1] - 2026-08-09

我继续完善远程规则分发链路，解决独立规则资产无法稳定远程使用的问题。

### Added
- 我让 Release Workflow 将完整生成规则逐个作为 GitHub Release Asset 发布。
- 我让 `release-manifest.json` 为客户端与规则资产生成稳定地址、SHA256 与文件大小。
- 我新增远程规则 HTTP 200 验证器，并在正式 Release 后逐一检查 latest 资产。
- 我补充远程规则发布规范，明确 latest 只跟随正式 Release。

### Changed
- 我将支持远程规则集的平台改为引用 GitHub Releases latest asset。
- 我继续保持远程规则缓存周期为 7 天。
- 我保留完整发行包，包括 7 端客户端、完整规则、Manifest、SHA256 与 ZIP。

### Fixed
- 我修复了 1.3.0 发布后规则虽然进入 ZIP / Release，却没有形成可直接订阅的独立 latest 远程规则资产的问题。
- 我让 Release 成功后只要任一 latest 客户端或规则 URL 不是 HTTP 200，发布 Job 就明确失败。

## [1.3.0] - 2026-08-09

我完成了第一版完整客户端与远程规则发布体系。

### Added
- 我正式发布全部 7 个客户端完整配置：Clash、Clash Meta、Stash、Egern、Loon、Shadowrocket、sing-box。
- 我正式发布完整规则资源目录，包括规则服务文件、优先级定义、规则源定义及相关规则元数据。
- 我让 Release Artifact 与 GitHub Release 同时保留客户端配置、完整规则目录、Manifest、SHA256 校验信息和 ZIP 归档。
