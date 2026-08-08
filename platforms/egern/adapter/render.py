#!/usr/bin/env python3
"""
Egern Renderer
Translates IR into Egern YAML config (policy_groups + rules style).
"""

from typing import Any

def _name(g: dict) -> str:
    name = g.get("name", {})
    if isinstance(name, dict):
        return name.get("zh") or name.get("en") or g.get("id", "unknown")
    return str(name)

def _resolve(opt: str, id_to_name: dict) -> str:
    if opt == "direct":
        return "DIRECT"
    if opt == "reject":
        return "REJECT"
    return id_to_name.get(opt, opt)

def render(ir: Any) -> dict:
    """Return a dict ready to be dumped as Egern-style YAML."""
    id_to_name = {}
    for g in ir.proxy_base + ir.proxy_service:
        id_to_name[g["id"]] = _name(g)

    policy_groups = []

    for g in ir.proxy_base:
        entry = {
            "select": {
                "name": _name(g),
                "policies": [],
                "flatten": True,
            }
        }
        opts = g.get("options", [])
        policies = []
        for o in opts:
            if isinstance(o, dict):
                if "ref" in o:
                    policies.append(id_to_name.get(o["ref"], o["ref"]))
                elif "action" in o:
                    act = o["action"]
                    policies.append("DIRECT" if act == "direct" else "REJECT" if act == "reject" else act)
            else:
                policies.append(_resolve(str(o), id_to_name))
        if g.get("include-all-nodes"):
            # Nodes come from Sub-Store; leave empty for user to fill
            pass
        entry["select"]["policies"] = policies or ["DIRECT"]
        policy_groups.append(entry)

    for g in ir.proxy_service:
        proxy_cfg = g.get("proxy", {})
        options = proxy_cfg.get("options", [])
        policies = [_resolve(str(o), id_to_name) for o in options]
        entry = {
            "select": {
                "name": _name(g),
                "policies": policies or ["DIRECT"],
                "flatten": True,
            }
        }
        policy_groups.append(entry)
        id_to_name[g["id"]] = _name(g)

    rules = []
    for r in ir.rules:
        target = id_to_name.get(r.get("_group"), r.get("_group", "其它连接"))
        rtype = r.get("type", "")
        values = r.get("values", [])
        if rtype == "domain-suffix":
            for v in values:
                rules.append({"domain_suffix": {"match": v, "policy": target}})
        elif rtype == "domain-keyword":
            for v in values:
                rules.append({"domain_keyword": {"match": v, "policy": target}})
        elif rtype == "geosite":
            # Egern may use rule_set or geosite depending on version
            for v in values:
                rules.append({"domain_suffix": {"match": v, "policy": target}})  # simplified
        elif rtype == "geoip":
            for v in values:
                rules.append({"geoip": {"match": v, "policy": target, "no_resolve": r.get("no_resolve", False)}})
        elif rtype == "match":
            rules.append({"default": {"policy": target}})

    if not any("default" in x for x in rules):
        rules.append({"default": {"policy": id_to_name.get("final", "其它连接")}})

    config = {
        "ipv6": True,
        "policy_groups": policy_groups,
        "rules": rules,
    }
    return config
