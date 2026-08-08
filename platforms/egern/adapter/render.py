#!/usr/bin/env python3
"""
Egern Renderer (P2-12)
Resolved IR → Egern YAML
"""

from typing import Any, Dict, List


def _resolve(opt: str, id_to_display: Dict[str, str]) -> str:
    if opt in ("direct", "DIRECT"):
        return "DIRECT"
    if opt in ("reject", "REJECT"):
        return "REJECT"
    return id_to_display.get(opt, opt)


def render(ir: Any) -> dict:
    id_to_display = dict(getattr(ir, "id_to_display", {}) or {})

    for g in getattr(ir, "base_groups", []) or []:
        name = g.get("name", {})
        display = name.get("zh") if isinstance(name, dict) else str(name)
        id_to_display[g["id"]] = display or g["id"]

    policy_groups: List[dict] = []

    # Base groups
    for g in getattr(ir, "base_groups", []) or []:
        policies = []
        for o in g.get("options") or []:
            if isinstance(o, dict):
                if "ref" in o:
                    policies.append(id_to_display.get(o["ref"], o["ref"]))
                elif "action" in o:
                    act = o["action"]
                    policies.append("DIRECT" if act == "direct" else "REJECT" if act == "reject" else act)
            else:
                policies.append(_resolve(str(o), id_to_display))
        entry = {
            "select": {
                "name": id_to_display.get(g["id"], g["id"]),
                "policies": policies or ["DIRECT"],
                "flatten": True,
            }
        }
        policy_groups.append(entry)

    # Services
    for s in getattr(ir, "services", []) or []:
        if hasattr(s, "id"):
            sid, name_zh = s.id, s.name_zh
            options, default = s.proxy_options, s.proxy_default
        else:
            sid = s["id"]
            name = s.get("name", {})
            name_zh = name.get("zh", sid) if isinstance(name, dict) else str(name)
            proxy_cfg = s.get("proxy") or {}
            options = proxy_cfg.get("options") or []
            default = proxy_cfg.get("default")

        id_to_display[sid] = name_zh
        policies = [_resolve(str(o), id_to_display) for o in options]
        if default:
            dname = _resolve(default, id_to_display)
            if dname in policies:
                policies = [dname] + [p for p in policies if p != dname]

        policy_groups.append({
            "select": {
                "name": name_zh,
                "policies": policies or ["DIRECT"],
                "flatten": True,
            }
        })

    # Rules
    rules: List[dict] = []
    for r in getattr(ir, "rules", []) or []:
        target = id_to_display.get(r.get("_group"), r.get("_group", "其它连接"))
        rtype = r.get("type", "")
        values = r.get("values") or []
        if rtype == "domain-suffix":
            for v in values:
                rules.append({"domain_suffix": {"match": v, "policy": target}})
        elif rtype == "domain-keyword":
            for v in values:
                rules.append({"domain_keyword": {"match": v, "policy": target}})
        elif rtype == "geosite":
            for v in values:
                # Prefer domain_suffix approximation; real rule_set can be added later
                rules.append({"domain_suffix": {"match": v, "policy": target}})
        elif rtype == "geoip":
            for v in values:
                rules.append({
                    "geoip": {
                        "match": v,
                        "policy": target,
                        "no_resolve": bool(r.get("no_resolve", False)),
                    }
                })
        elif rtype == "match":
            rules.append({"default": {"policy": target}})

    if not any("default" in x for x in rules):
        rules.append({"default": {"policy": id_to_display.get("final", "其它连接")}})

    # DNS fragment for Egern-style (simplified)
    resolvers = getattr(ir, "resolvers", {}) or {}
    dns_upstreams = {}
    for rid, r in resolvers.items():
        if r.get("type") == "system":
            continue
        servers = r.get("servers") or []
        if servers:
            dns_upstreams[rid] = servers

    config = {
        "ipv6": True,
        "dns": {
            "upstreams": dns_upstreams,
        },
        "policy_groups": policy_groups,
        "rules": rules,
    }
    return config
