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

# The platform-independent base definition is the source of truth for these
# five user-facing proxy-mode entries. Egern must expose all five explicitly.
PROXY_MODE_NAMES = {
    "proxy-mode": "代理模式",
    "manual-select": "手动选择",
    "free-flow": "定向免流",
    "auto-select": "自动选择",
    "direct": "直连模式",
    "reject": "阻断连接",
}
PROXY_MODE_ORDER = [
    "proxy-mode",
    "manual-select",
    "free-flow",
    "auto-select",
    "direct",
    "reject",
]


def _resolve(opt: str, id_to_display: Dict[str, str]) -> str:
    if opt in ("direct", "DIRECT"):
        return "DIRECT"
    if opt in ("reject", "REJECT"):
        return "REJECT"
    return id_to_display.get(opt, opt)


def _add_policy_group(policy_groups: List[dict], declared: set[str], name: str, policies: List[str] | None = None) -> None:
    """Add one native Egern policy group exactly once."""
    if not name or name in declared:
        return
    policy_groups.append({
        "select": {
            "name": name,
            "policies": policies or ["DIRECT"],
            "flatten": True,
        }
    })
    declared.add(name)


def _normalize_proxy_mode_groups(policy_groups: List[dict], subscriptions: List[dict]) -> None:
    """Guarantee the complete five-entry proxy-mode UX in Egern.

    Egern does not infer nested groups from the platform-independent IR. The
    five proxy-mode groups therefore need an explicit, deterministic native
    representation. Existing generated entries are normalized in place so
    stale/missing options cannot silently change the user-facing menu.
    """
    by_name = {}
    for entry in policy_groups:
        select = entry.get("select") if isinstance(entry, dict) else None
        if isinstance(select, dict) and select.get("name"):
            by_name[select["name"]] = select

    def ensure(name: str) -> dict:
        select = by_name.get(name)
        if select is None:
            entry = {"select": {"name": name, "policies": [], "flatten": True}}
            policy_groups.append(entry)
            select = entry["select"]
            by_name[name] = select
        return select

    manual = ensure(PROXY_MODE_NAMES["manual-select"])
    manual["policies"] = []

    free_flow = ensure(PROXY_MODE_NAMES["free-flow"])
    free_flow["policies"] = []
    free_flow["filter"] = "(?i)免流"

    auto = ensure(PROXY_MODE_NAMES["auto-select"])
    auto["policies"] = []

    direct = ensure(PROXY_MODE_NAMES["direct"])
    direct["policies"] = ["DIRECT"]

    reject = ensure(PROXY_MODE_NAMES["reject"])
    reject["policies"] = ["REJECT"]

    mode = ensure(PROXY_MODE_NAMES["proxy-mode"])
    mode["policies"] = [
        PROXY_MODE_NAMES["manual-select"],
        PROXY_MODE_NAMES["free-flow"],
        PROXY_MODE_NAMES["auto-select"],
        PROXY_MODE_NAMES["direct"],
        PROXY_MODE_NAMES["reject"],
    ]

    if subscriptions:
        urls = [s["url"] for s in subscriptions if isinstance(s, dict) and s.get("url")]
        if urls:
            for select in (manual, free_flow, auto):
                select["urls"] = urls
                select["update_interval"] = EXTERNAL_RESOURCE_INTERVAL


def render(ir: Any) -> dict:
    id_to_display = dict(getattr(ir, "id_to_display", {}) or {})
    pdata = load_providers()
    subscriptions = enabled_subscriptions(pdata)

    for g in getattr(ir, "base_groups", []) or []:
        name = g.get("name", {})
        display = name.get("zh") if isinstance(name, dict) else str(name)
        id_to_display[g["id"]] = display or g["id"]

    # Build the native policy namespace before emitting rules. Egern rule_set.policy
    # is a reference to policy_groups[].select.name, so the namespace must be
    # complete before any rule is rendered.
    for s in getattr(ir, "services", []) or []:
        id_to_display[s.id] = s.name_zh

    policy_groups: List[dict] = []
    declared: set[str] = set()

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
        declared.add(select["name"])

    # Normalize the canonical five proxy-mode entries after loading the base
    # groups. This makes the Egern UX deterministic even when an older IR or a
    # partially populated base definition is encountered.
    _normalize_proxy_mode_groups(policy_groups, subscriptions)
    declared = {
        g["select"]["name"]
        for g in policy_groups
        if isinstance(g, dict) and isinstance(g.get("select"), dict) and g["select"].get("name")
    }

    for s in getattr(ir, "services", []) or []:
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
        declared.add(s.name_zh)

    use_rs = supports_rule_set(PLATFORM)
    rules = emit_egern_style(ir, id_to_display, use_rs)

    # Hard invariants: every Egern rule_set.policy must reference an existing
    # policy group, and the canonical proxy-mode menu must always be complete.
    required_names = [PROXY_MODE_NAMES[k] for k in PROXY_MODE_ORDER]
    missing = [name for name in required_names if name not in declared]
    if missing:
        raise ValueError(f"Egern proxy-mode groups missing: {', '.join(missing)}")

    mode_group = next(
        g["select"] for g in policy_groups
        if g.get("select", {}).get("name") == PROXY_MODE_NAMES["proxy-mode"]
    )
    expected_mode_policies = [PROXY_MODE_NAMES[k] for k in PROXY_MODE_ORDER[1:]]
    if mode_group.get("policies") != expected_mode_policies:
        raise ValueError("Egern 代理模式 policies are not canonical")

    for rule in rules:
        rule_set = rule.get("rule_set") if isinstance(rule, dict) else None
        if not isinstance(rule_set, dict):
            continue
        policy = rule_set.get("policy")
        if policy not in declared:
            raise ValueError(f"Egern rule_set policy has no policy group: {policy}")

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
