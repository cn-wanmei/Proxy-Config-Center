# 最终配置 / Final Configs

由 `python scripts/build.py` 从 Core IR 生成。

| 客户端 | 文件 |
|--------|------|
| Clash Meta | [clash-meta/config.yaml](./clash-meta/config.yaml) |
| Clash | [clash/config.yaml](./clash/config.yaml) |
| Stash | [stash/config.yaml](./stash/config.yaml) |
| Egern | [egern/config.yaml](./egern/config.yaml) |
| Loon | [loon/config.conf](./loon/config.conf) |
| Shadowrocket | [shadowrocket/config.conf](./shadowrocket/config.conf) |

## 说明

- **策略组**：六端均含完整 22 组（代理模式 + 分流）
- **规则**：GEOSITE/GEOIP → blackmatrix7 RULE-SET → MATCH（Clash 系）
- **无订阅占位符**：填 `core/proxies/providers.yaml` 后 rebuild 才会出现 proxy-providers
- **DNS**：多上游列表，不写死单域名
