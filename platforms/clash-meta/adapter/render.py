#!/usr/bin/env python3
"""Clash Meta Renderer — reads ONLY IR (rule_sources)."""

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
    from engines.proxies import load_providers, clash_proxy_providers, clash_inline_proxies, provider_names
except Exception:
    def load_providers():
        return {}
    def clash_proxy_providers(data=None):
        return {}
    def clash_inline_proxies(data=None):
        return []
    def provider_names(data=None):
        return []


def _resolve_proxy_ref(opt: str, id_to_display: Dict[str, str]) -> str:
    if opt in ("direct", "DIRECT"):
        return "DIRECT"
    if opt in ("reject", "REJECT"):
        return "REJECT"
    return id_to_display.get(opt, opt)


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
        entry = {"name": id_to_display.get(g["id"], g["id"]), "type": g.get("type", "select")}
        if g.get("include-all-nodes") or g["id"] in ("manual-select", "auto-select", "free-flow"):
            if pnames:
                entry["include-all-providers"] = True
                entry["use"] = list(pnames)
            if inline_proxies:
                entry["proxies"] = [n["name"] for n in inline_proxies if n.get("name")]
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
                        proxies.append("DIRECT" if act == "direct" else "REJECT" if act == "reject" else act)
                else:
                    proxies.append(_resolve_proxy_ref(str(o), id_to_display))
            if proxies:
                entry["proxies"] = proxies
        iu = icon_url(g.get("icon"))
        if iu:
            entry["icon"] = iu
        proxy_groups.append(entry)

    for s in getattr(ir, "services", []) or []:
        sid, name_zh = s.id, s.name_zh
        id_to_display[sid] = name_zh
        proxies = [_resolve_proxy_ref(o, id_to_display) for o in s.proxy_options]
        dname = _resolve_proxy_ref(s.proxy_default, id_to_display)
        if dname in proxies:
            proxies = [dname] + [p for p in proxies if p != dname]
        entry = {"name": name_zh, "type": s.type, "proxies": proxies or ["DIRECT"]}
        iu = icon_url(s.icon)
        if iu:
            entry["icon"] = iu
        proxy_groups.append(entry)

    # DNS multi-upstream (not hardcoded per-domain)
    resolvers = getattr(ir, "resolvers", {}) or {}
    nameserver = []
    for rid in ("alidns", "tencent", "google", "cloudflare"):
        for s in (resolvers.get(rid) or {}).get("servers") or []:
            if s not in nameserver:
                nameserver.append(s)
    if not nameserver:
        nameserver = ["https://dns.alidns.com/dns-query", "https://cloudflare-dns.com/dns-query"]

    # ---- Rules ONLY from IR.rule_sources ----
    # Order: GEOSITE/GEOIP → BlackMatrix7 RULE-SET → domain → MATCH
    rule_providers = {}
    rules: List[str] = []

    for rs in getattr(ir, "rule_sources", []) or []:
        if rs.is_match:
            continue
        target = id_to_display.get(rs.target_service, rs.target_service)

        for gs in rs.geosite:
            rules.append(f"GEOSITE,{gs},{target}")
        for gi in rs.geoip:
            rules.append(f"GEOIP,{gi},{target},no-resolve")

        if rs.blackmatrix7_url:
            pname = rs.id
            rule_providers[pname] = {
                "type": "http",
                "behavior": rs.blackmatrix7_behavior or "classical",
                "url": rs.blackmatrix7_url,
                "path": f"./ruleset/{pname}.yaml",
                "interval": 86400,
            }
            rules.append(f"RULE-SET,{pname},{target}")

        for d in rs.domain_suffix:
            rules.append(f"DOMAIN-SUFFIX,{d},{target}")
        for d in rs.domain_keyword:
            rules.append(f"DOMAIN-KEYWORD,{d},{target}")

    rules.append(f"MATCH,{id_to_display.get('final', '其它连接')}")

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
            "nameserver": nameserver,
            "default-nameserver": ["223.5.5.5", "119.29.29.29", "1.1.1.1"],
        },
        "proxy-groups": proxy_groups,
        "rule-providers": rule_providers,
        "rules": rules,
    }
    if providers:
        config["proxy-providers"] = providers
    if inline_proxies:
        config["proxies"] = inline_proxies
    return config
