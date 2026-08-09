# Proxy-Config-Center

**通用代理配置中心 / Universal Proxy Configuration Center**  
**Version: 1.7.0**

统一生成并发布 Clash Meta、Clash、Stash、Egern、Loon、Shadowrocket、sing-box 七端代理配置。

Core、规则、策略组与发布体系在本仓库维护；各客户端只消费经过验证的最终配置。

**v1.7.0 重点：DNS 免泄露**（DoH 优先、proxy-server-nameserver、nameserver-policy、fallback）。

---

## 快速使用

### 七端完整配置 Raw URL（推荐）

| 平台 | Raw URL |
|------|---------|
| Clash | https://raw.githubusercontent.com/cn-wanmei/Proxy-Config-Center/latest-rules/clients/clash.yaml |
| Clash Meta | https://raw.githubusercontent.com/cn-wanmei/Proxy-Config-Center/latest-rules/clients/clash-meta.yaml |
| Stash | https://raw.githubusercontent.com/cn-wanmei/Proxy-Config-Center/latest-rules/clients/stash.yaml |
| Egern | https://raw.githubusercontent.com/cn-wanmei/Proxy-Config-Center/latest-rules/clients/egern.yaml |
| Loon | https://raw.githubusercontent.com/cn-wanmei/Proxy-Config-Center/latest-rules/clients/loon.conf |
| Shadowrocket | https://raw.githubusercontent.com/cn-wanmei/Proxy-Config-Center/latest-rules/clients/shadowrocket.conf |
| sing-box | https://raw.githubusercontent.com/cn-wanmei/Proxy-Config-Center/latest-rules/clients/sing-box.json |

### 分流规则基地址

```
https://raw.githubusercontent.com/cn-wanmei/Proxy-Config-Center/latest-rules/rules/
```

### Manifest

- https://raw.githubusercontent.com/cn-wanmei/Proxy-Config-Center/latest-rules/release-manifest.json
- https://raw.githubusercontent.com/cn-wanmei/Proxy-Config-Center/latest-rules/SHA256SUMS

---

## DNS 免泄露（v1.7）

Clash / Clash-Meta / Stash 生成配置包含：

- `enhanced-mode: fake-ip`
- `default-nameserver`：仅 bootstrap IP
- `nameserver`：DoH 为主
- `proxy-server-nameserver`：节点域名 DoH 解析
- `fallback` + `fallback-filter`
- `nameserver-policy`：domain → policy
- 国外/安全 Policy 不再提供 system 选项

---

## 本地构建

```bash
make ci
```

详见 [CHANGELOG.md](CHANGELOG.md) 与 `docs/架构说明.md`。
