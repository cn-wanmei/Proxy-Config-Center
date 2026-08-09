# Changelog

## [1.7.0] - 2026-08-09

### DNS 免泄露 / Leak-resistant DNS

- DNS Engine V2：统一生成 Clash 系防泄露 DNS 块。
- 渲染层真正输出 `nameserver-policy`（domain → policy 映射）。
- `default-nameserver` 仅保留必要 bootstrap IP（223.5.5.5 / 1.1.1.1）。
- 新增 `proxy-server-nameserver`（节点域名解析走 DoH）。
- 新增 `fallback` + `fallback-filter`（geoip CN + 污染段）。
- 国外/安全类 Policy 移除 `system` 选项，降低误选系统 DNS 泄露风险。
- Clash / Clash-Meta / Stash 共用同一套防泄露 DNS 构建逻辑。
- Apple / 中国路径仍允许 system（兼容性需要）。

## [1.6.2] - 2026-08-09

### Fix incomplete push & stabilize engineering polish

- Re-pushed optimized `scripts/ir.py`, `scripts/rule_audit.py`, `scripts/validate.py`.
- Confirmed remote uses `DEFAULT_PRIORITY` / cached `load_yaml` / `proxies_optional`.

## [1.6.1] - 2026-08-09

### Engineering polish (post-audit)

- Cached YAML loading, priority constants, proxies_optional facade, dual_source notes, structured errors, neutral docs.

## [1.6.0] - 2026-08-09

v1.3–v1.6 engineering consolidation (release determinism, rule intelligence, AI provider, supply chain).
