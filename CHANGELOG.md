# Changelog

## 4.1.0

- 建立总服务 → 单服务的层级策略模型，补充 Apple、Google 等服务族的独立子策略。
- Apple 补充 Apple Account、App Store、iCloud、Music、TV、Maps、Push、系统更新、Apple Intelligence、Developer 等服务入口。
- Google 补充 Android、Drive、FCM、Gmail、Maps、Photos、Google Play、YouTube 等服务入口。
- 刷新 Microsoft 核心域名，并预留官方发布 IP 段自动同步。
- GitHub 接入官方 Meta API，用于同步公开 IP 段与服务域名；GitHub 官方文档明确建议通过 Meta API 定期监控 IP 变化。citeturn2search1turn2search0
- 增加每日 08:00 / 20:00（Asia/Tokyo 对应 GitHub Actions UTC 23:00 / 11:00）在线规则智能更新。
- 在线更新器支持域名、IPv4 CIDR、IPv6 CIDR；不主动通过 DNS 解析结果学习动态 IP。
- 更新失败时 fail-closed，不删除现有规则。
- 过期规则采用连续 3 次成功源检查后再清理，仅清理更新器历史上实际拥有的条目。
- 在线数据更新后重新执行 Core Boundary、Audit Gate、全客户端 RAW 编译和 `git diff --check`。
- 增加 4.1 在线更新单元测试。

## 4.0.0

- 收缩项目为纯分流规则 Core。
- 规则按策略生成稳定在线 RAW 文件：`rules/<policy>.yaml`。
- 移除旧手工规则输出和客户端/网络配置职责。
- 编译器升级为确定性 RAW 编译器。
- 审计输出改为本地临时产物，不作为在线规则发布包。
- 增加 RAW 发布工作流，仅在审计通过后更新 `rules/`。
- 增加 4.0 语义与确定性编译回归测试。
- 禁止规则 ZIP/TAR/Release Package 作为项目分发方式。
