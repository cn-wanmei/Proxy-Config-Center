# Changelog

## [1.1.0] - 2026-08-09

平台契约与 sing-box 扩展 / Platform contract and sing-box expansion。

### Added
- 显式 Platform Registry，Required Platforms 不再散落硬编码。
- Resolved IR 正式增加 Node、ProxyGroup、IconRef 等平台无关模型。
- `engines/utils.py` 集中基础 YAML 加载。
- `engines/fallbacks.py` 集中显式降级策略，避免异常吞噬。
- sing-box 原生 JSON Adapter 与 Capability Profile。
- sing-box selector / urltest 出站组、route rules、显式节点转换。
- Stash、Loon、sing-box Golden/Structural invariants。
- Release 增加 `sing-box.json` 独立资产。

### Changed
- `build.py` 支持 sing-box JSON 输出，并缓存 renderer 加载。
- `check_config.py` 显式接收平台参数并增加 sing-box JSON 校验。
- Semantic Tests 从完整服务硬编码集合改为 Core catalog + critical contract 双层验证。
- `build/` 继续作为正式产物，`final/` 仅作为 legacy compatibility tree。
- 外部规则资源继续统一 7 天刷新；sing-box 对非原生 rule-set 源安全使用域名规则降级，不伪造格式兼容性。
- Release 仍严格 tag-only。

### Compatibility
- 原六端 Core/IR 语义保持不变。
- sing-box 不支持当前 Clash YAML/LIST 规则源的直接复用，因此不会错误声明为原生 sing-box rule-set。

## [1.0.2] - 2026-08-09

客户端规则能力补全与发布流程加固 / Client rule capability completion and release workflow hardening。

### Added
- 节点组与策略组继续通过统一 IR 输出到六端客户端。
- Egern 策略组支持直接挂载启用的远程订阅 URL。
- Egern、Loon、Shadowrocket 补充策略组图标输出，并由 capability 显式控制。
- 六端 Capability Matrix 增加客户端图标能力覆盖测试。
- 外部规则资源统一采用 7 天（604800 秒）刷新周期。
- Clash/Stash 等支持远程代理集的客户端，其外部节点订阅统一采用 7 天刷新周期。
- 修复 Blackmatrix7 ChinaIPs 已移除的 Clash YAML 源，并映射到当前 IP-CIDR 列表格式。

### Fixed
- 正式 Release workflow 不再响应 `release/v*` 分支或 Pull Request。
- PR / release 分支不会再进入正式 Release Job，也不会创建或修改 GitHub Release。
- 正式 Release 只能由 `v*` Git tag 触发，并始终从 tag 对应 commit checkout。
- Release 的 `target_commitish` 改为当前 tag commit，消除旧版本代码与新版本 tag 错配风险。
- 非 Clash 客户端的规则集转换不再保留失效的 `/rule/Clash/` 路径。

### Validation
- Capability、Semantic、Golden、Build、Structural、Rule Source Health 均继续作为正式 Release 的强制门禁。

## [1.0.1] - 2026-08-09

发布交付方式优化 / Release distribution refinement。

### Changed
- 六端配置由 Release 单独文件直接交付，不再要求用户下载 ZIP 后再解压。
- 保留完整 ZIP 作为六端归档与离线备份。
- 增加 `latest/download/<file>` 稳定下载入口，适合客户端长期订阅。
- 固定版本继续使用 `releases/download/vX.Y.Z/<file>`，便于审计、回滚和版本锁定。
- Release workflow 对六端独立文件、完整 ZIP 统一构建、校验、Artifact 发布和 Attestation。

## [1.0.0] - 2026-08-09

首个正式稳定版本 / First Stable Release。
