# Changelog

## [1.3.2] - 2026-08-09

Raw 远程规则分发架构 / Raw remote-rule distribution architecture。

### Added
- 新增 `latest-rules` 专用发布分支，仅承载经过正式 Release 验证的最终规则资源。
- 七端客户端远程规则统一改用 `raw.githubusercontent.com` Raw 地址，不再使用 GitHub Release `latest/download` 下载地址。
- Release Workflow 在正式 Release 成功后自动刷新 `latest-rules`，确保远程规则只跟随最新正式版本。
- 新增 Raw Remote Rule Manifest，记录规则资产、Raw URL、SHA256、大小与来源版本。
- Release 后逐个 HTTP 200 检查 Raw 远程规则，并校验远程内容 SHA256 与本次发布资产一致。

### Changed
- 远程规则基地址统一为：`https://raw.githubusercontent.com/cn-wanmei/Proxy-Config-Center/latest-rules/rules/`。
- Release Asset 继续保留完整规则与版本归档，但客户端订阅不再依赖 Release Asset 下载行为。
- `latest-rules` 只能由正式 `v*` Release Workflow 更新，PR、普通分支和失败构建不得更新远程规则。
- 版本 Release 与远程订阅彻底解耦：`vX.Y.Z` 用于历史归档，`latest-rules` 用于自动更新。

### Validation
- Core / Reference Validator                         ✅
- Rule Coverage Audit                                ✅
- Capability Tests                                   ✅
- Semantic Tests                                     ✅
- Seven-platform Semantic Equivalence                ✅
- Golden Snapshot                                    ✅
- Build / Structural / Final Artifact                ✅
- Release Asset Completeness                         ✅
- Raw Rule Manifest                                  ✅
- Raw Rule HTTP 200                                  ✅
- Raw Rule SHA256 Integrity                          ✅

### Compatibility
- 不具备原生远程 rule-set 能力的平台继续遵循真实 capability，不伪造平台能力。
- 具备远程规则能力的平台使用 `latest-rules` Raw 地址。
- Shadowrocket 与 sing-box 保持各自真实 capability，不因发布层强行注入不兼容的 rule-set。

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
- 历史 `vX.Y.Z` Release 继续用于版本归档；客户端远程规则只追踪最新正式 Release。

### Fixed
- 修复 1.3.0 发布后规则虽然进入 ZIP / Release，却没有形成可直接订阅的独立 latest 远程规则资产的问题。
- Release 成功后若任一 latest 客户端或规则 URL 非 HTTP 200，发布 Job 明确失败，避免产生不可用的远程订阅。

## [1.3.0] - 2026-08-09

完整客户端与远程规则发布体系 / Complete client and remote-rule release distribution。

### Added
- 正式 Release 同步发布全部 7 个客户端完整配置：Clash、Clash Meta、Stash、Egern、Loon、Shadowrocket、sing-box。
- 正式 Release 同步发布完整规则资源目录，包括规则服务文件、优先级定义、规则源定义及相关规则元数据。
- Release Artifact 与 GitHub Release 同时保留客户端配置、完整规则目录、Manifest、SHA256 校验信息和 ZIP 归档。

### Changed
- Release 不再只验证 7 个客户端入口文件，改为同时验证客户端配置与完整规则资产。
- ZIP 从仅包含客户端配置升级为包含完整客户端、完整规则、Manifest 与校验文件的完整发行包。
- 发布模型明确区分“版本归档”和“远程自动更新”。

## [1.2.1] - 2026-08-09

发布资产完整性修复 / Release asset integrity fix。

### Fixed
- Release workflow 增加正式资产预检，七端独立配置文件与 ZIP 任一缺失都会直接失败。
- Release assets 改为显式文件清单上传，避免仅上传 ZIP 或目录导致客户端独立文件缺失。
- Release Artifact 同时保留七端独立配置、完整配置目录与 ZIP 归档。
- 增加发布资产名称与非空文件校验，防止构建成功但 Release 资产不完整。
