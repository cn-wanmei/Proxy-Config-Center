#!/usr/bin/env python3
"""Egern — no GEOSITE/GEOIP; domain_suffix from IR + BM note."""

import sys
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))

try:
    from engines.proxies import load_providers, enabled_subscriptions
except Exception:
    def load_providers():
        return {}
    def enabled_subscriptions(data=None):
        return []

def _resolve(opt: str, id_to_display: Dict[str, str]) -> str:
    if opt in ("direct", "DIRECT"):
        return "DIRECT"
    if opt in ("reject", "REJECT"):
        return "REJECT"
    return id_to_display.get(opt, opt)

def render(ir: Any) -> dict:
    id_to_display = dict(getattr(ir, "id_to_display", {}) or {})
    pdata = load_providers()

    for g in getattr(ir, "base_groups", []) or []:
        name = g.get("name", {})
        display = name.get("zh") if isinstance(name, dict) else str(name)
        id_to_display[g["id"]] = display or g["id"]

    policy_groups: List[dict] = []
    for g in getattr(ir, "base_groups", []) or []:
        policies = []
        for o in g.get("options") or []:
            if isinstance(o, dict):
                if "ref" in o:
                    policies.append(id_to_display.get(o["ref"], o["ref"]))
                elif "action" in o:
                    act = o["action"]
                    policies.append("DIRECT" if act == "direct" else "REJECT")
            else:
                policies.append(_resolve(str(o), id_to_display))
        if g.get("include-all-nodes") and not policies:
            policies = ["DIRECT"]
        policy_groups.append({
            "select": {
                "name": id_to_display.get(g["id"], g["id"]),
                "policies": policies or ["DIRECT"],
                "flatten": True,
            }
        })

    for s in getattr(ir, "services", []) or []:
        id_to_display[s.id] = s.name_zh
        policies = [_resolve(str(o), id_to_display) for o in s.proxy_options]
        dname = _resolve(s.proxy_default, id_to_display)
        if dname in policies:
            policies = [dname] + [p for p in policies if p != dname]
        policy_groups.append({
            "select": {"name": s.name_zh, "policies": policies or ["DIRECT"], "flatten": True}
        })

    # Egern: domain_suffix patches only (no geoip/geosite)
    # Full BM lists are for Clash rule-providers; Egern uses domain_suffix from source
    rules: List[dict] = []
    for rs in getattr(ir, "rule_sources", []) or []:
        if rs.is_match:
            continue
        target = id_to_display.get(rs.target_service, rs.target_service)
        for d in rs.domain_suffix:
            rules.append({"domain_suffix": {"match": d, "policy": target}})
        for d in rs.domain_keyword:
            rules.append({"domain_keyword": {"match": d, "policy": target}})

    rules.append({"default": {"policy": id_to_display.get("final", "其它连接")}})

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
        "dns": {"upstreams": dns_upstreams},
        "policy_groups": policy_groups,
        "rules": rules,
    }
    # 注释：Clash 系用 blackmatrix7 rule-providers；Egern 以策略组 + 域名补丁为主
    subs = []
    for s in enabled_subscriptions(pdata):
        name = s.get("name", {})
        n = name.get("zh") if isinstance(name, dict) else str(name)
        subs.append({"name": n or s.get("id"), "url": s.get("url"), "udp_relay": True})
    if subs:
        config["proxy_providers"] = subs
    return config
