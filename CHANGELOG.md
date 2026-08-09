# Changelog

## [1.3.0] - 2026-08-09

完整客户端与远程规则发布体系 / Complete client and remote-rule release distribution。

### Added
- 正式 Release 同步发布全部 7 个客户端完整配置：Clash、Clash Meta、Stash、Egern、Loon、Shadowrocket、sing-box。
- 正式 Release 同步发布完整规则资源目录，包括规则服务文件、优先级定义、规则源定义及相关规则元数据。
- Release Artifact 与 GitHub Release 同时保留客户端配置、完整规则目录、Manifest、SHA256 校验信息和 ZIP 归档。
- 远程订阅统一使用 GitHub Releases 的 `latest/download/<asset>` 语义，客户端无需绑定固定版本号。
- 历史版本仍通过 `vX.Y.Z` Release 归档，可用于审计与回滚；远程自动更新仅跟随最新正式 Release。
- Release 增加完整规则资产存在性、非空及目录完整性检查。

### Changed
- Release 不再只验证 7 个客户端入口文件，改为同时验证客户端配置与完整规则资产。
- ZIP 从仅包含客户端配置升级为包含完整客户端、完整规则、Manifest 与校验文件的完整发行包。
- 发布模型明确区分“版本归档”和“远程自动更新”：版本号用于历史发布，`latest` 用于客户端远程更新。
- `latest` 只允许由正式 `v*` Tag 触发的成功 Release 更新，PR、分支和失败构建不得成为远程更新来源。

### Validation
- Core / Reference Validator                         ✅
- Rule Coverage Audit                                ✅
- Capability Tests                                   ✅
- Semantic Tests                                     ✅
- Seven-platform Semantic Equivalence                ✅
- Golden Snapshot                                    ✅
- Build / Structural / Final Artifact                ✅
- Client Asset Completeness                          ✅
- Remote Rule Asset Completeness                     ✅
- Manifest / SHA256                                 ✅

## [1.2.1] - 2026-08-09

发布资产完整性修复 / Release asset integrity fix。

### Fixed
- Release workflow 增加正式资产预检，七端独立配置文件与 ZIP 任一缺失都会直接失败。
- Release assets 改为显式文件清单上传，避免仅上传 ZIP 或目录导致客户端独立文件缺失。
- Release Artifact 同时保留七端独立配置、完整配置目录与 ZIP 归档。
- 增加发布资产名称与非空文件校验，防止构建成功但 Release 资产不完整。
- 版本号统一切换至 `1.2.1`，并继续要求 Git tag 与 `VERSION` 严格一致。

### Validation
- Core / Reference Validator                         ✅
- Rule Coverage Audit                                ✅
- Capability Tests                                   ✅
- Semantic Tests                                     ✅
- Seven-platform Semantic Equivalence                ✅
- Golden Snapshot                                    ✅
- Build / Structural / Final Artifact                ✅
- Release Asset Completeness                         ✅

## [1.2.0] - 2026-08-09

分流质量体系与 AI Provider Registry / Routing quality and AI provider registry。

### Added
- Rule → Strategy Group 机器索引与 Markdown 可视化审计报告。
- Duplicate、Conflict、Unreachable Rule 自动检测并纳入 CI 门禁。
- AI Provider Registry，按 LLM、Coding、Image、Video、Music、Audio、Search、Gateway、Inference 等语义分类维护主流 AI 服务。
- AI 服务覆盖扩展至 Groq、Together AI、Replicate、Fireworks AI、Cohere、AI21、Stability AI、Midjourney、Suno、ElevenLabs、Runway、Character AI、Leonardo AI、Krea 等主流服务。
- AI / Google / Microsoft / GitHub 分流边界重新整理，GitHub Copilot 按 AI 语义优先处理。
- Rule Trace 命中解释能力，支持查看首个命中规则、priority、strategy group、source 与 shadowed candidates。
- 七端深度 Semantic Equivalence Test，覆盖 Clash、Clash Meta、Stash、Egern、Loon、Shadowrocket、sing-box。
- 历史 `sys.path` 运行时注入清理，并增加 CI 防回归检查。

### Changed
- 分流审计从静态检查升级为 Rule Coverage Quality Gate。
- AI Provider Registry 作为语义目录与覆盖约束，不直接成为第二套规则执行源，避免与 `ai.yaml` 漂移。
- 七端验证从文件结构一致性升级为跨平台路由语义一致性验证。
- 分流规则继续遵循显式 priority，AI、Google、Microsoft、GitHub 等边界通过优先级和覆盖关系明确表达。
- Makefile / PYTHONPATH 统一开发与 CI 入口，减少测试环境路径副作用。

### Validation
- Core / Reference Validator                                ✅
- Rule Coverage Audit                                       ✅
- Duplicate / Conflict / Unreachable Detection              ✅
- AI Provider Registry Regression                            ✅
- Rule Trace Regression                                     ✅
- Seven-platform Semantic Equivalence                       ✅
- Golden Snapshot                                           ✅
- Rule Source Health                                        ✅
- Build / Structural / Final Artifact                       ✅

### Compatibility
- 保持 v1.1.x Core / IR 语义兼容。
- 七端继续输出独立正式配置文件。
- sing-box 继续遵循真实 capability，不伪造当前 Clash YAML/LIST 源的原生 rule-set 兼容性。
