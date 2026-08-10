# Release Notes — v2.0.0

## Highlights

- **Core V2 semantic baseline** based on the 1.7 DNS leak-resistant stack
- **DNS Engine V2** as the single Clash-family DNS builder (fake-ip, DoH-first, proxy-server-nameserver, fallback, nameserver-policy)
- Foreign/secure DNS policies no longer expose `system` resolver
- Engineering polish from 1.6.x retained (cached YAML, priority constants, proxies_optional, neutral docs)
- Deprecated `core/config/dns.yaml` removed; DNS lives only under `core/dns/`

## Platforms

Clash Meta · Clash · Stash · Egern · Loon · Shadowrocket · sing-box

## Breaking / intentional

- Pre-2.0 changelog narrative retired; start from 2.0.0
- System DNS only on explicit china/system/Apple paths
- Clients should re-fetch Raw configs after upgrading to 2.0
