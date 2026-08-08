#!/usr/bin/env python3
"""Clash Meta Renderer — subscriptions + single/multi nodes + icons + DNS."""

import sys
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))

try:
    from engines.icons import icon_url
except Exception:
    def icon_url(name):
        return name if name and str(name).startswith("http") else None

try:
    from engines.proxies import (
        load_providers,
        clash_proxy_providers,
        clash_inline_proxies,
        provider_names,
    )
except Exception:
    def load_providers():
        return {}
    def clash_proxy_providers(data=None):
        return {
            "机场订阅1": {
                "type": "http",
                "url": "YOUR_SUBSCRIBE_URL_1",
                "interval": 86400,
                "path": "./providers/airport-1.yaml",
                "health-check": {
                    "enable": True,
                    "url": "http://www.gstatic.com/generate_204",
                    "interval": 300,
                },
            }
        }
    def clash_inline_proxies(data=None):
        return []
    def provider_names(data=None):
        return ["机场订阅1"]


def _resolve_proxy_ref(opt: str, id_to_display: Dict[str, str]) -> str:
    if opt in ("direct", "DIRECT"):
        return "DIRECT"
    if opt in ("reject", "REJECT"):
        return "REJECT"
    return id_to_display.get(opt, opt)


def _resolver_to_clash(resolver_id: str, resolvers: dict) -> List[str]:
    r = resolvers.get(resolver_id) or {}
    if r.get("type") == "system":
        return ["system"]
    return list(r.get("servers") or []) or ["system"]


def render(ir: Any) -> dict:
    id_to_display = dict(getattr(ir, "id_to_display", {}) or {})
    pdata = load_providers()
    pnames = provider_names(pdata)
    inline_proxies = clash_inline_proxies(pdata)
    providers = clash_proxy_providers(pdata)

    for g in getattr(ir, "base_groups", []) or []:
        name = g.get("name", {})
        display = name.get("zh") if isinstance(name, dict) else str(name)
        id_to_display[g["id"]] = display or g["id"]

    proxy_groups: List[dict] = []

    for g in getattr(ir, "base_groups", []) or []:
        entry = {
            "name": id_to_display.get(g["id"], g["id"]),
            "type": g.get("type", "select"),
        }
        # Node-bearing groups: use providers + inline proxies
        if g.get("include-all-nodes") or g["id"] in ("manual-select", "auto-select", "free-flow"):
            entry["include-all-providers"] = True
            if pnames:
                entry["use"] = list(pnames)
            # include inline node names if any
            if inline_proxies:
                entry.setdefault("proxies", [])
                for n in inline_proxies:
                    if n.get("name"):
                        entry["proxies"].append(n["name"])
            if not entry.get("proxies") and not pnames:
                entry["proxies"] = ["DIRECT"]
            if g.get("filter"):
                entry["filter"] = g["filter"]
            if g.get("type") == "url-test":
                entry["url"] = "http://www.gstatic.com/generate_204"
                entry["interval"] = 300
        else:
            proxies = []
            for o in g.get("options") or []:
                if isinstance(o, dict):
                    if "ref" in o:
                        proxies.append(id_to_display.get(o["ref"], o["ref"]))
                    elif "action" in o:
                        act = o["action"]
                        proxies.append(
                            "DIRECT" if act == "direct" else "REJECT" if act == "reject" else act
                        )
                else:
                    proxies.append(_resolve_proxy_ref(str(o), id_to_display))
            if proxies:
                entry["proxies"] = proxies

        iu = icon_url(g.get("icon"))
        if iu:
            entry["icon"] = iu
        proxy_groups.append(entry)

    for s in getattr(ir, "services", []) or []:
        if hasattr(s, "id"):
            sid, name_zh = s.id, s.name_zh
            options, default = s.proxy_options, s.proxy_default
            icon, gtype = s.icon, s.type
        else:
            sid = s["id"]
            name = s.get("name", {})
            name_zh = name.get("zh", sid) if isinstance(name, dict) else str(name)
            proxy_cfg = s.get("proxy") or {}
            options = proxy_cfg.get("options") or []
            default = proxy_cfg.get("default") or (options[0] if options else "proxy-mode")
            icon = s.get("icon", "")
            gtype = s.get("type", "select")

        id_to_display[sid] = name_zh
        proxies = [_resolve_proxy_ref(o, id_to_display) for o in options]
        if default:
            dname = _resolve_proxy_ref(default, id_to_display)
            if dname in proxies:
                proxies = [dname] + [p for p in proxies if p != dname]

        entry = {"name": name_zh, "type": gtype, "proxies": proxies or ["DIRECT"]}
        iu = icon_url(icon)
        if iu:
            entry["icon"] = iu
        proxy_groups.append(entry)

    rules: List[str] = []
    for r in getattr(ir, "rules", []) or []:
        target = id_to_display.get(r.get("_group"), r.get("_group", "其它连接"))
        rtype = r.get("type", "")
        values = r.get("values") or []
        if rtype == "domain-suffix":
            for v in values:
                rules.append(f"DOMAIN-SUFFIX,{v},{target}")
        elif rtype == "domain-keyword":
            for v in values:
                rules.append(f"DOMAIN-KEYWORD,{v},{target}")
        elif rtype == "geosite":
            for v in values:
                rules.append(f"GEOSITE,{v},{target}")
        elif rtype == "geoip":
            for v in values:
                no_res = ",no-resolve" if r.get("no_resolve") else ""
                rules.append(f"GEOIP,{v},{target}{no_res}")
        elif rtype == "match":
            rules.append(f"MATCH,{target}")

    if not any(x.startswith("MATCH,") for x in rules):
        rules.append(f"MATCH,{id_to_display.get('final', '其它连接')}")

    resolvers = getattr(ir, "resolvers", {}) or {}
    default_servers = _resolver_to_clash("cloudflare", resolvers)
    if default_servers == ["system"]:
        default_servers = ["https://cloudflare-dns.com/dns-query"]

    try:
        from engines.dns_engine import DNSEngine
        nsp = DNSEngine().build_nameserver_policy()
    except Exception:
        nsp = {"+.apple.com": "system", "+.icloud.com": "system"}

    config = {
        "mixed-port": 7890,
        "allow-lan": True,
        "mode": "rule",
        "log-level": "info",
        "ipv6": True,
        "dns": {
            "enable": True,
            "ipv6": True,
            "enhanced-mode": "fake-ip",
            "fake-ip-range": "198.18.0.1/16",
            "nameserver": default_servers,
            "nameserver-policy": nsp,
        },
        # ⬇️ 订阅占位 — 修改 core/proxies/providers.yaml 后重新 build
        "proxy-providers": providers,
        # ⬇️ 单节点/多节点手写占位（enabled: true 的节点会进入）
        "proxies": inline_proxies,
        "proxy-groups": proxy_groups,
        "rules": rules,
    }
    # Clash dislikes empty proxies key sometimes — keep list (may be empty)
    if not config["proxies"]:
        config["proxies"] = []
    return config
