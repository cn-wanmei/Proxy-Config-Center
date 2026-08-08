# 最终配置 / Final Configs

> `python scripts/build.py` 自动生成

## 订阅怎么加（不会出现占位符）

编辑 `core/proxies/providers.yaml`：

```yaml
subscriptions:
  - id: airport-1
    name: { zh: 我的机场 }
    url: "https://真实订阅链接"
    enabled: true
```

再执行 `python scripts/build.py`。  
**未填写真实 URL 时，配置里不会出现 proxy-providers / YOUR_***。

## 规则来源

1. **GEOSITE / GEOIP**（优先）
2. **blackmatrix7/ios_rule_script** 的 `rule-providers` 补全

## DNS

`nameserver` 为多上游列表（阿里 / 腾讯 / Google / CF），**不写死**单域名绑定，可自行调整顺序或增删。

## 文件

| 客户端 | 路径 |
|--------|------|
| Clash Meta | `clash-meta/config.yaml` |
| Clash | `clash/config.yaml` |
| Stash | `stash/config.yaml` |
| Egern | `egern/config.yaml` |
| Loon | `loon/config.conf` |
| Shadowrocket | `shadowrocket/config.conf` |
