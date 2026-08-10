# Proxy-Config-Center

**通用代理配置中心 / Universal Proxy Configuration Center**  
**Version: 2.0.0**

统一生成并发布 Clash Meta、Clash、Stash、Egern、Loon、Shadowrocket、sing-box 七端代理配置。

Core、规则、策略组与发布体系在本仓库维护；各客户端只消费经过验证的最终配置。

**2.0.0 基线：DNS 免泄露 + Core V2 语义。**

---

## 快速使用

### 七端完整配置 Raw URL

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

## 架构（Core V2）

```
Core
 → Schema / Semantic Validation
 → Reference Graph
 → Resolved IR
 → Capability Engine
 → Platform Adapter
 → Artifact / Release
```

- `core/` — 唯一业务语义（规则、DNS、策略组）
- `scripts/ir.py` — 平台无关 IR
- `scripts/engines/` — capability / DNS / rule 约束
- `platforms/` — 各端 renderer
- `build/` — 生成物（非源码接口）

节点由 Sub-Store 独立管理。

---

## DNS 免泄露（2.0）

Clash / Clash-Meta / Stash：

- `enhanced-mode: fake-ip`
- bootstrap-only `default-nameserver`
- DoH `nameserver` + `proxy-server-nameserver`
- `fallback` + `fallback-filter`
- `nameserver-policy`
- 国外路径不提供 system DNS

---

## 本地构建

```bash
make install
make ci
```

---

## 架构原则

1. Core First  
2. Capability Driven  
3. Fail Fast  
4. Tag-only Release  
5. Semantic Raw Distribution  
6. DNS Leak Resistant（2.0）  

详见 [CHANGELOG.md](CHANGELOG.md) · [docs/架构说明.md](docs/架构说明.md)
