# 最终配置 / Final Configs

渲染时读取 `platforms/*/capabilities.yaml`：

| 能力 | 行为 |
|------|------|
| `rule_provider` / `rule_set` = true | 远程 blackmatrix7 规则集 |
| false | `domain_suffix` fallback |

| 客户端 | 规则形态 |
|--------|----------|
| Clash Meta / Clash / Stash | `RULE-SET` + rule-providers |
| Loon | `DOMAIN-SET`（Loon 列表 URL）+ domain_suffix |
| Egern / Shadowrocket | 仅 domain_suffix |

无 GEOSITE / GEOIP。订阅填 `core/proxies/providers.yaml` 后 rebuild。
