# Changelog

## [1.6.2] - 2026-08-09

### Fix incomplete push & stabilize engineering polish

- Re-pushed optimized `scripts/ir.py`, `scripts/rule_audit.py`, `scripts/validate.py` that were missing from earlier partial commits.
- Confirmed remote `main` now uses `DEFAULT_PRIORITY` / `FALLBACK_PRIORITY` / `get_priority_map` and cached `load_yaml`.
- Confirmed `engines.proxies_optional` facade and structured error suggestions are live.
- Documentation remains neutral technical language (zero first-person narrative).

## [1.6.1] - 2026-08-09

### Engineering polish (post-audit)

- Cached YAML loading in `engines.utils` (path + mtime keyed `lru_cache`) to eliminate repeated I/O during audit → build → validate.
- Extracted priority magic numbers (`500` / `999`) into `DEFAULT_PRIORITY` / `FALLBACK_PRIORITY` constants and `get_priority_map()` helper.
- Introduced explicit `engines.proxies_optional` facade so platform adapters no longer scatter soft-dependency try/except blocks.
- `rule_audit` now surfaces dual-source `domain_suffix` overlaps (sources.yaml ↔ services/*.yaml) as informational notes instead of silent drift.
- Validation and audit error messages now include concrete fix suggestions.
- Type hints and structured `CoreLoadError` improved for Core file loading failures.
- Documentation rewritten to neutral technical language (removed first-person narrative style).

## [1.6.0] - 2026-08-09

v1.3–v1.6 路线的最终工程化收口。重点从增加客户端数量转向发布确定性、规则工程化、AI Provider 管理和供应链完整性，统一到同一条可验证流水线。

### v1.3 稳定化
- Release 从当前 `main` 自动解析唯一 source commit，发布入口只接受版本号。
- 取消 Tag Push 自动发布，避免历史 Tag/SHA 进入旧代码。
- 正式 Release 设置为不可覆盖；已存在版本会直接触发 immutable gate。
- 最终客户端配置重新执行 Remote Config Semantic Validation，并在发布后做 Raw HTTP 200 + SHA256 E2E 校验。
- 增加 Build Report、Source Snapshot、Release Manifest 和供应链报告。

### v1.4 规则工程化
- 建立 Rule Index 与 Rule Graph 的机器可读输出。
- 加入 Rule Explain 基础能力，可按精确 match 查询规则来源。
- 加入重复/冲突候选检测与 unreachable 候选报告。
- 保留七端 Semantic Matrix，并将平台原生语义作为发布门禁。
- Domain → Rule → Match 的关系可被机器索引和后续可视化工具直接消费。

### v1.5 AI Provider 平台化
- 建立 AI Provider Registry，将 Provider、Service、Domain、Strategy 解耦。
- 加入 AI Coverage Matrix 输出。
- 将 Google / Microsoft / GitHub 的服务边界作为独立 Provider 维度，避免按顶级域名粗暴归类。
- 为 Provider Diff 保留稳定的机器可读 Registry 数据基础。

### v1.6 供应链
- 增加 Rule Source Snapshot，记录规则源内容 SHA256 和大小。
- 增加可复现构建基础：锁定依赖、固定 source commit、统一 `SOURCE_DATE_EPOCH`。
- 增加 CycloneDX 风格 SBOM。
- 增加 Schema Version Manifest，为后续 Schema v2 演进保留兼容边界。
- Release Manifest 同时记录 source commit、generator commit、schema version 和远程资源完整性。

### Release Gate
- 要求 Validate → Capability → Semantic → Seven-platform Semantic → Build → Golden → Structural → Source Health → Engineering Reports → Release Distribution Contract → Immutable Release → latest-rules → Raw E2E Integrity 全链路通过后才能发布。
- 7 个客户端、全部分流规则、Manifest、Raw URL 和 SHA256 必须保持一致。
