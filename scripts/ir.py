#!/usr/bin/env python3
"""
Core → IR → Resolved IR (P1-6/7)
"""

from pathlib import Path
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

try:
    import yaml
except ImportError:
    raise SystemExit("PyYAML required: pip install pyyaml")

ROOT = Path(__file__).resolve().parent.parent
CORE = ROOT / "core"

def load_yaml(path: Path) -> Any:
    if not path.exists():
        return None
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)

@dataclass
class ResolvedService:
    id: str
    name_zh: str
    name_en: str
    type: str
    proxy_options: List[str]
    proxy_default: str
    dns_policy_id: str
    dns_default_resolver: str
    dns_options: List[str]
    icon: str

@dataclass
class ResolvedIR:
    """Fully resolved intermediate representation for renderers."""
    config_base: dict = field(default_factory=dict)
    config_runtime: dict = field(default_factory=dict)
    # DNS resolved
    resolvers: Dict[str, dict] = field(default_factory=dict)
    dns_groups: Dict[str, dict] = field(default_factory=dict)
    dns_policies: Dict[str, dict] = field(default_factory=dict)
    # Proxy
    base_groups: List[dict] = field(default_factory=list)
    services: List[ResolvedService] = field(default_factory=list)
    # Rules sorted by priority
    rules: List[dict] = field(default_factory=list)
    priority: List[dict] = field(default_factory=list)
    # Lookup maps
    id_to_display: Dict[str, str] = field(default_factory=dict)

def _display_name(g: dict) -> str:
    name = g.get("name", {})
    if isinstance(name, dict):
        return name.get("zh") or name.get("en") or g.get("id", "unknown")
    return str(name)

def build_ir() -> ResolvedIR:
    ir = ResolvedIR()

    ir.config_base = load_yaml(CORE / "config" / "base.yaml") or {}
    ir.config_runtime = load_yaml(CORE / "config" / "runtime.yaml") or {}

    # DNS layers
    resolvers_data = load_yaml(CORE / "dns" / "resolvers.yaml") or {}
    ir.resolvers = resolvers_data.get("resolvers") or {}

    groups_data = load_yaml(CORE / "dns" / "groups.yaml") or {}
    for g in groups_data.get("groups") or []:
        ir.dns_groups[g["id"]] = g

    policies_data = load_yaml(CORE / "dns" / "policies.yaml") or {}
    for p in policies_data.get("policies") or []:
        ir.dns_policies[p["id"]] = p

    # Base proxy groups
    base = load_yaml(CORE / "proxy-groups" / "base.yaml") or {}
    ir.base_groups = base.get("groups") or []
    for g in ir.base_groups:
        ir.id_to_display[g["id"]] = _display_name(g)

    # Special actions
    ir.id_to_display["direct"] = "DIRECT"
    ir.id_to_display["reject"] = "REJECT"

    # Priority
    prio = load_yaml(CORE / "rules" / "priority.yaml") or {}
    ir.priority = sorted(prio.get("priority") or [], key=lambda x: x.get("value", 999))
    priority_map = {p["id"]: p.get("value", 999) for p in ir.priority}

    # Services resolved
    service_data = load_yaml(CORE / "proxy-groups" / "service.yaml") or {}
    for g in service_data.get("groups") or []:
        sid = g["id"]
        name = g.get("name") or {}
        proxy_cfg = g.get("proxy") or {}
        options = list(proxy_cfg.get("options") or [])
        default = proxy_cfg.get("default") or (options[0] if options else "proxy-mode")
        if default not in options and options:
            default = options[0]

        dns_policy_id = g.get("dns") or "dns-foreign"
        policy = ir.dns_policies.get(dns_policy_id) or {}
        dns_options = list(policy.get("options") or ["cloudflare"])
        dns_default = policy.get("default") or (dns_options[0] if dns_options else "cloudflare")

        rs = ResolvedService(
            id=sid,
            name_zh=name.get("zh", sid) if isinstance(name, dict) else str(name),
            name_en=name.get("en", sid) if isinstance(name, dict) else str(name),
            type=g.get("type", "select"),
            proxy_options=options,
            proxy_default=default,
            dns_policy_id=dns_policy_id,
            dns_default_resolver=dns_default,
            dns_options=dns_options,
            icon=g.get("icon", ""),
        )
        ir.services.append(rs)
        ir.id_to_display[sid] = rs.name_zh

    # Rules
    rules_dir = CORE / "rules" / "services"
    all_rules = []
    if rules_dir.exists():
        for f in rules_dir.glob("*.yaml"):
            data = load_yaml(f) or {}
            gid = data.get("group") or data.get("id", "").replace("service-", "")
            order = priority_map.get(gid, 500)
            for r in data.get("rules") or []:
                r = dict(r)
                r["_group"] = data.get("group", gid)
                r["_priority"] = order
                all_rules.append(r)
    ir.rules = sorted(all_rules, key=lambda x: x.get("_priority", 999))
    return ir

# Backward compatible alias
def build_raw_ir():
    return build_ir()

if __name__ == "__main__":
    ir = build_ir()
    print(f"Resolved IR: {len(ir.base_groups)} base, {len(ir.services)} services, {len(ir.rules)} rules")
    print(f"DNS: {len(ir.resolvers)} resolvers, {len(ir.dns_policies)} policies")
    for s in ir.services[:3]:
        print(f"  {s.id}: proxy_default={s.proxy_default}, dns={s.dns_policy_id} -> {s.dns_default_resolver}")
