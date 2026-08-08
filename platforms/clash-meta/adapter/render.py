#!/usr/bin/env python3
"""
Clash Meta Renderer
Translates IR into Clash Meta (mihomo) YAML config.
"""

from typing import Any

def _name(g: dict) -> str:
    name = g.get("name", {})
    if isinstance(name, dict):
        return name.get("zh") or name.get("en") or g.get("id", "unknown")
    return str(name)

def _resolve_option(opt: str, id_to_name: dict) -> str:
    if opt in ("direct",):
        return "DIRECT"
    if opt in ("reject",):
        return "REJECT"
    return id_to_name.get(opt, opt)

def render(ir: Any) -> dict:
    """Return a dict ready to be dumped as Clash Meta YAML."""
    id_to_name = {}

    # Collect all group display names
    for g in ir.proxy_base + ir.proxy_service:
        id_to_name[g["id"]] = _name(g)

    proxy_groups = []

    # Base groups
    for g in ir.proxy_base:
        gid = g["id"]
        entry = {
            "name": _name(g),
            "type": g.get("type", "select"),
        }
        if g.get("include-all-nodes"):
            entry["include-all-providers"] = True
        if g.get("filter"):
            entry["filter"] = g["filter"]
        if "options" in g:
            entry["proxies"] = [_resolve_option(o if isinstance(o, str) else o.get("ref") or o.get("action"), id_to_name) for o in g["options"]]
        # Handle nested options from semantic form
        opts = g.get("options", [])
        proxies = []
        for o in opts:
            if isinstance(o, dict):
                if "ref" in o:
                    proxies.append(id_to_name.get(o["ref"], o["ref"]))
                elif "action" in o:
                    act = o["action"]
                    proxies.append("DIRECT" if act == "direct" else "REJECT" if act == "reject" else act)
            else:
                proxies.append(_resolve_option(str(o), id_to_name))
        if proxies:
            entry["proxies"] = proxies
        if g.get("icon"):
            entry["icon"] = g["icon"]
        proxy_groups.append(entry)

    # Service groups
    for g in ir.proxy_service:
        proxy_cfg = g.get("proxy", {})
        options = proxy_cfg.get("options", [])
        default = proxy_cfg.get("default")
        proxies = []
        for o in options:
            proxies.append(_resolve_option(str(o), id_to_name))
        entry = {
            "name": _name(g),
            "type": g.get("type", "select"),
            "proxies": proxies or ["DIRECT"],
        }
        if g.get("icon"):
            entry["icon"] = g["icon"]
        proxy_groups.append(entry)
        id_to_name[g["id"]] = _name(g)

    # Rules
    rules = []
    for r in ir.rules:
        target = id_to_name.get(r.get("_group"), r.get("_group", "FINAL"))
        rtype = r.get("type", "")
        values = r.get("values", [])
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

    # Ensure MATCH at end
    if not any(x.startswith("MATCH,") for x in rules):
        final_name = id_to_name.get("final", "其它连接")
        rules.append(f"MATCH,{final_name}")

    config = {
        "mixed-port": 7890,
        "allow-lan": True,
        "mode": "rule",
        "log-level": "info",
        "ipv6": True,
        "proxy-groups": proxy_groups,
        "rules": rules,
    }
    return config
