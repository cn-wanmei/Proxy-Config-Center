# Proxy-Config-Center

Universal proxy configuration center.

Core rules & strategies for:
- Clash Meta (mihomo)
- Clash
- Loon
- Egern
- Stash
- Shadowrocket

**Nodes are managed independently via Sub-Store. This repository contains no node subscriptions.**

## Directory Structure

```
Proxy-Config-Center/
├── core/                       # ★ Core logic (single source of truth)
│   ├── strategy/               # Unified strategy groups
│   ├── rules/                  # Unified rules
│   ├── dns/                    # Unified DNS architecture
│   ├── advertising/            # Ad blocking logic
│   └── config-base.yaml        # Base settings (IPv6, TUN, etc.)
├── platforms/                  # Platform adapters
│   ├── clash-meta/
│   ├── clash/
│   ├── loon/
│   ├── egern/
│   ├── stash/
│   └── shadowrocket/
├── build/                      # Auto-generated configs (do not edit)
├── scripts/                    # Build & update scripts
├── common/
│   └── icons/                  # Official high-quality icons
├── docs/                       # Documentation
└── .github/workflows/          # CI / Build automation
```

## Design Principles

1. **Core First** — All logic lives in `core/`. Platforms only render.
2. **No Nodes** — Nodes are handled by Sub-Store.
3. **Unified Strategy** — One set of strategy groups for all platforms.
4. **Easy Maintenance** — Change core once, rebuild all platforms.

## Status

Skeleton created. Core strategy definition coming next.
