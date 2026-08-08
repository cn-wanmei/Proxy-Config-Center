# Generated Platform Configs / 生成的全平台配置

> AUTO-GENERATED — run `python scripts/build.py` to regenerate.
> 禁止手动修改。节点请用 Sub-Store 注入。

## Files

| Platform | Path |
|----------|------|
| Clash Meta | `clash-meta/config.yaml` |
| Clash | `clash/config.yaml` |
| Stash | `stash/config.yaml` |
| Egern | `egern/config.yaml` |
| Loon | `loon/config.conf` |
| Shadowrocket | `shadowrocket/config.conf` |

## Features
- 16 service strategy groups + base proxy mode
- Full rule set (31+ rules) including game / tiktok / ehentai
- Icons from ClashTools image CDN
- DNS nameserver-policy (Apple→system, China→AliDNS, etc.)

## Build
```bash
pip install pyyaml
python scripts/validate.py
python scripts/build.py
python scripts/check_config.py
```
