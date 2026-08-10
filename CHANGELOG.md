# Changelog

## [2.0.0] - 2026-08-10

### Core V2 / DNS leak-resistant baseline

Breaking version cut from the 1.7.0 stack. Pre-2.0 release notes are retired.

**DNS**
- DNS Engine V2 is the only Clash-family DNS builder
- `nameserver-policy` emitted from domain → policy map
- `default-nameserver` bootstrap-only (`223.5.5.5`, `1.1.1.1`)
- `proxy-server-nameserver` forces DoH for node hostnames
- `fallback` + `fallback-filter` (geoip CN)
- Foreign / secure / google / cloudflare / selectable policies: no `system` option
- Removed deprecated `core/config/dns.yaml`

**Engineering (carried from 1.6–1.7)**
- Cached YAML load (`engines.utils`)
- `DEFAULT_PRIORITY` / `FALLBACK_PRIORITY` / `get_priority_map`
- `engines.proxies_optional` facade
- rule_audit dual-source notes + structured errors
- Neutral technical documentation

**Platforms**
- Clash / Clash-Meta / Stash share leak-resistant DNS block
- Egern skips system upstreams
- Loon / Shadowrocket / sing-box keep capability-native emission

### Migration

1. Pull `main` @ 2.0.0
2. Re-run `make ci` or full validate/build
3. Re-subscribe Raw client URLs under `latest-rules` after the next formal tag release
