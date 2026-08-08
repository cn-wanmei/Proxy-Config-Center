# 最终配置

分流规则**仅**来自 [blackmatrix7/ios_rule_script](https://github.com/blackmatrix7/ios_rule_script)。

- **无** GEOSITE / GEOIP
- Clash Meta / Clash / Stash：`rule-providers` + `RULE-SET`
- 中国：`China.yaml` + `ChinaIPs.yaml`
- 绅士漫画等无 BM 集：少量 `DOMAIN-SUFFIX` 补丁

| 客户端 | 文件 |
|--------|------|
| Clash Meta | `clash-meta/config.yaml` |
| Clash | `clash/config.yaml` |
| Stash | `stash/config.yaml` |
| Egern | `egern/config.yaml` |
| Loon | `loon/config.conf` |
| Shadowrocket | `shadowrocket/config.conf` |
