#!/usr/bin/env python3
"""Egern — capabilities-aware rules, policy groups and external nodes."""

import sys
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))

from engines.capability import supports, supports_rule_set, platform_from_adapter_file
from engines.rules_emit import emit_egern_style

try:
    from engines.icons import icon_url
except Exception:
    def icon_url(name):
        return name if name and str(name).startswith("http") else None

try:
    from engines.proxies import EXTERNAL_RESOURCE_INTERVAL, load_providers, enabled_subscriptions
except Exception:
    EXTERNAL_RESOURCE_INTERVAL = 7 * 24 * 60 * 60
    def load_providers():
        return {}
    def enabled_subscriptions(data=None):
        return []

PLATFORM = platform_from_adapter_file(__file__)


def _resolve(opt: str, id_to_display: Dict[str, str]) -> str:
    if opt in ("direct", "DIRECT"):
        return "DIRECT"
    if opt in ("reject", "REJECT"):
        return "REJECT"
    return id_to_display.get(opt, opt)


def render(ir: Any) -> dict:
    id_to_display = dict(getattr(ir, "id_to_display", {}) or {})
    pdata = load_providers()
    subscriptions = enabled_subscriptions(pdata)

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

        entry = {
            "select": {
                "name": id_to_display.get(g["id"], g["id"]),
                "policies": policies or ["DIRECT"],
                "flatten": True,
            }
        }
        select = entry["select"]
        if g.get("include-all-nodes") and subscriptions:
            select["urls"] = [s["url"] for s in subscriptions]
            select["update_interval"] = EXTERNAL_RESOURCE_INTERVAL
        if g.get("filter"):
            select["filter"] = g["filter"]
        if supports(PLATFORM, "icons"):
            iu = icon_url(g.get("icon"))
            if iu:
                select["icon"] = iu
        policy_groups.append(entry)

    for s in getattr(ir, "services", []) or []:
        id_to_display[s.id] = s.name_zh
        policies = [_resolve(str(o), id_to_display) for o in s.proxy_options]
        dname = _resolve(s.proxy_default, id_to_display)
        if dname in policies:
            policies = [dname] + [p for p in policies if p != dname]
        entry = {"select": {"name": s.name_zh, "policies": policies or ["DIRECT"], "flatten": True}}
        if supports(PLATFORM, "icons"):
            iu = icon_url(s.icon)
            if iu:
                entry["select"]["icon"] = iu
        policy_groups.append(entry)

    use_rs = supports_rule_set(PLATFORM)
    rules = emit_egern_style(ir, id_to_display, use_rs)

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
    return config
