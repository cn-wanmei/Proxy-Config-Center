# 最终配置 / Final Configs

> 由 `python scripts/build.py` 自动生成，请勿手改。

## 使用前

1. 编辑 `core/proxies/providers.yaml`
   - `subscriptions[].url` → **机场订阅链接**（支持多个）
   - `nodes[]` → **单节点 / 多节点**（设 `enabled: true`）
2. 重新执行：`python scripts/build.py`
3. 从本目录复制对应客户端配置导入

## 文件一览

| 客户端 | 文件 |
|--------|------|
| Clash Meta | `clash-meta/config.yaml` |
| Clash | `clash/config.yaml` |
| Stash | `stash/config.yaml` |
| Egern | `egern/config.yaml` |
| Loon | `loon/config.conf` |
| Shadowrocket | `shadowrocket/config.conf` |

## 配置内占位说明

### Clash Meta / Clash / Stash

```yaml
proxy-providers:
  机场订阅1:
    type: http
    url: YOUR_SUBSCRIBE_URL_1   # ⬅️ 改成真实订阅
    ...
proxies: []                     # 单/多节点写入 core/proxies/providers.yaml 后出现在此
```

「手动选择 / 自动选择 / 定向免流」会自动 `use` 上述订阅，并包含手写节点。

### Egern

```yaml
proxy_providers:
- name: 机场订阅1
  url: YOUR_SUBSCRIBE_URL_1
```

也可继续用 Sub-Store 注入节点。
