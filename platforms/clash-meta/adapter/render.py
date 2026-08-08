#!/usr/bin/env python3
"""Clash Meta family renderer — capability-driven platform routing."""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))

from engines.capability import supports, supports_remote_rules, platform_from_adapter_file
from engines.rules_emit import emit_clash_style

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

DEFAULT_PLATFORM = platform_from_adapter_file(__file__)


def _resolve_proxy_ref(opt: str, id_to_display: Dict[str, str]) -> str:
    if opt in ("direct", "DIRECT"):
        return "DIRECT"
    if opt in ("reject", "REJECT"):
        return "REJECT"
    return id_to_display.get(opt, opt)


def render(ir: Any, platform: Optional[str] = None) -> dict:
    """Render Clash-family syntax using the platform capability profile."""
    plat = platform or DEFAULT_PLATFORM
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
        if supports(plat, "icons"):
            iu = icon_url(g.get("icon"))
            if iu:
                entry["icon"] = iu
        proxy_groups.append(entry)

    for s in getattr(ir, "services", []) or []:
        id_to_display[s.id] = s.name_zh
        proxies = [_resolve_proxy_ref(o, id_to_display) for o in s.proxy_options]
        dname = _resolve_proxy_ref(s.proxy_default, id_to_display)
        if dname in proxies:
            proxies = [dname] + [p for p in proxies if p != dname]
        entry = {"name": s.name_zh, "type": s.type, "proxies": proxies or ["DIRECT"]}
        if supports(plat, "icons"):
            iu = icon_url(s.icon)
            if iu:
                entry["icon"] = iu
        proxy_groups.append(entry)

    resolvers = getattr(ir, "resolvers", {}) or {}
    nameserver = []
    for rid in ("alidns", "tencent", "google", "cloudflare"):
        for srv in (resolvers.get(rid) or {}).get("servers") or []:
            if srv not in nameserver:
                nameserver.append(srv)
    if not nameserver:
        nameserver = ["https://dns.alidns.com/dns-query", "https://cloudflare-dns.com/dns-query"]

    use_rs = supports_remote_rules(plat)
    rule_providers, rules = emit_clash_style(ir, id_to_display, use_rs)

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
        "rules": rules,
    }
    if use_rs and rule_providers:
        config["rule-providers"] = rule_providers
    if providers:
        config["proxy-providers"] = providers
    if inline_proxies:
        config["proxies"] = inline_proxies

    if supports(plat, "profile_store_selected"):
        config.setdefault("profile", {})
        if isinstance(config["profile"], dict):
            config["profile"]["store-selected"] = True

    return config
