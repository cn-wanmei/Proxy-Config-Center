# 最终配置 / Final Configs

> 由 `python scripts/build.py` 自动生成，请勿手改。

## 使用前

1. 编辑 `core/proxies/providers.yaml`
   - `subscriptions[].url` → 机场订阅链接
   - `nodes[]` → 单节点/多节点（`enabled: true`）
2. 重新执行 `python scripts/build.py`
3. 从本目录复制对应客户端配置

| 客户端 | 文件 |
|--------|------|
| Clash Meta | `clash-meta/config.yaml` |
| Clash | `clash/config.yaml` |
| Stash | `stash/config.yaml` |
| Egern | `egern/config.yaml` |
| Loon | `loon/config.conf` |
| Shadowrocket | `shadowrocket/config.conf` |
