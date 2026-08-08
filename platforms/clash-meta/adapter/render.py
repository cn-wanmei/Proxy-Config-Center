#!/usr/bin/env python3
"""
Clash Meta Renderer (P1-8/9/10/11)
Resolved IR → Clash Meta YAML including DNS nameserver-policy
"""

from typing import Any, Dict, List


def _resolve_proxy_ref(opt: str, id_to_display: Dict[str, str]) -> str:
    if opt in ("direct", "DIRECT"):
        return "DIRECT"
    if opt in ("reject", "REJECT"):
        return "REJECT"
    return id_to_display.get(opt, opt)


def _resolver_to_clash(resolver_id: str, resolvers: dict) -> List[str]:
    """Convert a resolver id to Clash DNS server list."""
    r = resolvers.get(resolver_id) or {}
    rtype = r.get("type", "system")
    if rtype == "system":
        return ["system"]
    servers = r.get("servers") or []
    return list(servers) if servers else ["system"]


def render(ir: Any) -> dict:
    id_to_display = dict(getattr(ir, "id_to_display", {}) or {})

    # Ensure base group names
    for g in getattr(ir, "base_groups", []) or []:
        name = g.get("name", {})
        display = name.get("zh") if isinstance(name, dict) else str(name)
        id_to_display[g["id"]] = display or g["id"]

    proxy_groups: List[dict] = []

    # ---- Base groups ----
    for g in getattr(ir, "base_groups", []) or []:
        entry = {
            "name": id_to_display.get(g["id"], g["id"]),
            "type": g.get("type", "select"),
        }
        if g.get("include-all-nodes"):
            entry["include-all-providers"] = True
        if g.get("filter"):
            entry["filter"] = g["filter"]

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
        if g.get("icon"):
            entry["icon"] = g["icon"]
        proxy_groups.append(entry)

    # ---- Service groups (use ResolvedService) ----
    for s in getattr(ir, "services", []) or []:
        # Support both ResolvedService dataclass and plain dict
        if hasattr(s, "id"):
            sid, name_zh = s.id, s.name_zh
            options, default = s.proxy_options, s.proxy_default
            icon = s.icon
            gtype = s.type
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

        # Put default first for better UX
        if default:
            dname = _resolve_proxy_ref(default, id_to_display)
            if dname in proxies:
                proxies = [dname] + [p for p in proxies if p != dname]

        entry = {
            "name": name_zh,
            "type": gtype,
            "proxies": proxies or ["DIRECT"],
        }
        if icon:
            entry["icon"] = icon
        proxy_groups.append(entry)

    # ---- Rules ----
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

    # ---- DNS (from Resolved IR) ----
    resolvers = getattr(ir, "resolvers", {}) or {}
    dns_policies = getattr(ir, "dns_policies", {}) or {}

    # nameserver: use foreign/cloudflare default
    default_servers = _resolver_to_clash("cloudflare", resolvers)
    if default_servers == ["system"]:
        default_servers = ["https://cloudflare-dns.com/dns-query"]

    nameserver_policy = {}
    # Map domains from service rules that have domain-suffix to their DNS policy default resolver
    for s in getattr(ir, "services", []) or []:
        if not hasattr(s, "dns_policy_id"):
            continue
        policy = dns_policies.get(s.dns_policy_id) or {}
        resolver_id = policy.get("default") or s.dns_default_resolver
        servers = _resolver_to_clash(resolver_id, resolvers)
        # We attach policy via domain keys in a simplified way:
        # Full domain mapping comes from rules; here we set common known sets
        pass

    # Build nameserver-policy from a static mapping aligned with core/dns design
    # (Apple → system, China → alidns, Google → google, etc.)
    policy_domain_map = {
        "dns-system": ["+.apple.com", "+.icloud.com", "+.push.apple.com", "+.mzstatic.com", "+.itunes.apple.com"],
        "dns-china": ["+.cn", "+.baidu.com", "+.qq.com", "+.tencent.com", "+.alipay.com"],
        "dns-google": ["+.google.com", "+.googleapis.com", "+.gstatic.com", "+.youtube.com"],
        "dns-foreign": ["+.openai.com", "+.anthropic.com", "+.x.ai", "+.telegram.org", "+.twitter.com", "+.x.com"],
        "dns-cloudflare": ["+.netflix.com", "+.spotify.com", "+.github.com"],
    }
    for policy_id, domains in policy_domain_map.items():
        policy = dns_policies.get(policy_id) or {}
        resolver_id = policy.get("default", "cloudflare")
        servers = _resolver_to_clash(resolver_id, resolvers)
        for d in domains:
            nameserver_policy[d] = servers if len(servers) > 1 else (servers[0] if servers else "system")

    dns_block = {
        "enable": True,
        "ipv6": True,
        "enhanced-mode": "fake-ip",
        "fake-ip-range": "198.18.0.1/16",
        "nameserver": default_servers,
        "nameserver-policy": nameserver_policy,
    }

    config = {
        "mixed-port": 7890,
        "allow-lan": True,
        "mode": "rule",
        "log-level": "info",
        "ipv6": True,
        "dns": dns_block,
        "proxy-groups": proxy_groups,
        "rules": rules,
    }
    return config
